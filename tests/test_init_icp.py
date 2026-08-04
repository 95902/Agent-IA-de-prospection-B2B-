"""Tests unitaires de `scripts/init_icp.py` (issue #12).

Couvre la logique métier sans dépendances live (PG/Qdrant/Ollama mockés) :
- construction du texte ICP à embarquer (description + champs structurés) ;
- orchestration end-to-end (load → embed → upsert Qdrant → update PG) ;
- idempotence : une 2e exécution met à jour le même point Qdrant (AC #3) ;
- erreur si client introuvable ;
- erreur si description ICP vide (embedding impossible).

Les tests d'intégration (vraie base + Ollama) sont marqués `integration`.
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Permet l'import du script depuis la racine du repo.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import init_icp  # noqa: E402


# --- Construction du texte ICP à embarmer -----------------------------------

def test_build_icp_text_uses_description_plus_criteres():
    """Le texte embarqué enrichit la description libre avec les critères
    structurés (NAF, effectif, mots-clés) pour un embedding plus riche."""
    row = {
        "description": "Garages automobiles indépendants",
        "codes_naf": ["4520Z", "4511Z"],
        "departements": ["75", "92"],
        "effectif_min": 2,
        "effectif_max": 15,
        "anciennete_min_ans": 3,
        "mots_cles_positifs": ["réparation", "multi-marques"],
        "mots_cles_negatifs": ["concession"],
    }
    text = init_icp._build_icp_text(row)
    assert "Garages automobiles indépendants" in text
    assert "4520Z" in text
    assert "4511Z" in text
    assert "75" in text
    assert "réparation" in text
    assert "multi-marques" in text
    assert "concession" in text  # les négatifs orientent aussi l'embedding
    assert "2" in text and "15" in text  # bornes effectif


def test_build_icp_text_handles_missing_optional_fields():
    """Champs structurés absents (NULL en base) → texte dégradé propre."""
    row = {
        "description": "Cible vague",
        "codes_naf": None,
        "departements": None,
        "effectif_min": None,
        "effectif_max": None,
        "anciennete_min_ans": None,
        "mots_cles_positifs": None,
        "mots_cles_negatifs": None,
    }
    text = init_icp._build_icp_text(row)
    assert "Cible vague" in text
    # Ne crash pas, ne lève pas de TypeError sur None.


def test_build_icp_text_empty_description_raises():
    """Une description vide + aucun critère → ValueError (embedding impossible)."""
    row = {
        "description": "",
        "codes_naf": [],
        "departements": [],
        "effectif_min": None,
        "effectif_max": None,
        "anciennete_min_ans": None,
        "mots_cles_positifs": [],
        "mots_cles_negatifs": [],
    }
    with pytest.raises(ValueError):
        init_icp._build_icp_text(row)


# --- Orchestration end-to-end (mockée) ---------------------------------------

def _fake_icp_row(*, description="Garages indépendants", icp_profile_id=None):
    """Row simulée renvoyée par la lecture PG de l'ICP."""
    return {
        "icp_profile_id": icp_profile_id or str(uuid.uuid4()),
        "description": description,
        "critere_id": str(uuid.uuid4()),
        "codes_naf": ["4520Z"],
        "departements": ["75"],
        "effectif_min": 2,
        "effectif_max": 15,
        "anciennete_min_ans": 3,
        "mots_cles_positifs": ["réparation"],
        "mots_cles_negatifs": ["concession"],
    }


@pytest.mark.asyncio
async def test_run_end_to_end_embeds_and_upserts_and_updates_pg():
    """Parcours nominal : load → embed → ensure_collections → upsert Qdrant
    → update PG (qdrant_point_id + embedding_version)."""
    cid = str(uuid.uuid4())
    row = _fake_icp_row()

    with (
        patch("scripts.init_icp.db.get_pg_pool", new_callable=AsyncMock) as mock_pool,
        patch("scripts.init_icp.db.ensure_collections", new_callable=AsyncMock) as f_collect,
        patch("scripts.init_icp.db.get_qdrant") as mock_get_q,
        patch("scripts.init_icp.embeddings.get_embedding", new_callable=AsyncMock) as f_embed,
        patch("scripts.init_icp.db.close", new_callable=AsyncMock) as f_close,
    ):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        mock_pool.return_value.acquire = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        f_embed.return_value = [0.1] * 768
        qdrant = AsyncMock()
        mock_get_q.return_value = qdrant

        rc = await init_icp._run(cid)

    assert rc == 0
    f_collect.assert_awaited_once()
    f_embed.assert_awaited_once()  # embedding généré
    # Upsert Qdrant : 1 point, id = icp_profile_id (AC #3 idempotence).
    qdrant.upsert.assert_awaited_once()
    call = qdrant.upsert.call_args
    assert call.kwargs["collection_name"] == "icp_profiles"
    points = call.kwargs["points"]
    assert len(points) == 1
    assert points[0].id == row["icp_profile_id"]
    # Update PG : qdrant_point_id + embedding_version posés.
    update_query = conn.execute.call_args.args[0]
    assert "qdrant_point_id" in update_query
    assert "embedding_version" in update_query
    f_close.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_idempotent_reuses_same_qdrant_point_id():
    """AC #3 : une 2e exécution met à jour le MÊME point Qdrant (id fixe =
    icp_profile_id), pas un nouveau point → pas de doublon."""
    cid = str(uuid.uuid4())
    icp_id = str(uuid.uuid4())
    row = _fake_icp_row(icp_profile_id=icp_id)

    async def _run_once():
        with (
            patch("scripts.init_icp.db.get_pg_pool", new_callable=AsyncMock) as mock_pool,
            patch("scripts.init_icp.db.ensure_collections", new_callable=AsyncMock),
            patch("scripts.init_icp.db.get_qdrant") as mock_get_q,
            patch("scripts.init_icp.embeddings.get_embedding", new_callable=AsyncMock) as f_embed,
            patch("scripts.init_icp.db.close", new_callable=AsyncMock),
        ):
            conn = AsyncMock()
            conn.fetchrow = AsyncMock(return_value=row)
            mock_pool.return_value.acquire = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=conn),
                __aexit__=AsyncMock(return_value=None),
            ))
            f_embed.return_value = [0.2] * 768
            qdrant = AsyncMock()
            mock_get_q.return_value = qdrant
            await init_icp._run(cid)
            return qdrant.upsert.call_args.kwargs["points"][0].id

    point_id_1 = await _run_once()
    point_id_2 = await _run_once()
    assert point_id_1 == icp_id
    assert point_id_2 == icp_id  # même point, pas de doublon


@pytest.mark.asyncio
async def test_run_client_not_found_exits_nonzero():
    """Client UUID introuvable en base → exit 2 (pas d'embedding)."""
    cid = str(uuid.uuid4())
    with (
        patch("scripts.init_icp.db.get_pg_pool", new_callable=AsyncMock) as mock_pool,
        patch("scripts.init_icp.embeddings.get_embedding", new_callable=AsyncMock) as f_embed,
        patch("scripts.init_icp.db.close", new_callable=AsyncMock),
    ):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)  # client introuvable
        mock_pool.return_value.acquire = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        rc = await init_icp._run(cid)

    assert rc != 0
    f_embed.assert_not_awaited()  # pas d'appel embedding


def test_main_invalid_uuid_returns_nonzero(capsys):
    """--client-id mal formé → exit code 2 (pas de SystemExit : _run gère
    l'erreur et retourne 2, main() propage le code)."""
    rc = init_icp.main(["--client-id", "pas-un-uuid"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "pas un UUID" in err or "invalide" in err


# --- Patches revue de code (protection des fixes) ----------------------------

@pytest.mark.asyncio
async def test_run_ollama_down_returns_2_with_message():
    """Patch #6 : Ollama down/timeout → exit 2 propre avec message, pas de
    traceback brut. Cohérent avec les autres paths d'erreur."""
    cid = str(uuid.uuid4())
    row = _fake_icp_row()
    with (
        patch("scripts.init_icp.db.get_pg_pool", new_callable=AsyncMock) as mock_pool,
        patch("scripts.init_icp.embeddings.get_embedding", new_callable=AsyncMock) as f_embed,
        patch("scripts.init_icp.db.close", new_callable=AsyncMock),
    ):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        mock_pool.return_value.acquire = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        f_embed.side_effect = RuntimeError("Ollama timeout")  # Ollama down
        rc = await init_icp._run(cid)

    assert rc == 2  # exit propre, pas de traceback propagé


@pytest.mark.asyncio
async def test_run_pg_update_failure_after_qdrant_logs_drift():
    """Patch #5 : si l'UPDATE PG échoue après l'upsert Qdrant, on logge le
    drift (vecteur orphelin) et on retourne 2 — pas de rollback silencieux."""
    cid = str(uuid.uuid4())
    row = _fake_icp_row()
    with (
        patch("scripts.init_icp.db.get_pg_pool", new_callable=AsyncMock) as mock_pool,
        patch("scripts.init_icp.db.ensure_collections", new_callable=AsyncMock),
        patch("scripts.init_icp.db.get_qdrant") as mock_get_q,
        patch("scripts.init_icp.embeddings.get_embedding", new_callable=AsyncMock) as f_embed,
        patch("scripts.init_icp.db.close", new_callable=AsyncMock),
    ):
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=row)
        # L'UPDATE PG échoue (conn perdue).
        conn.execute = AsyncMock(side_effect=RuntimeError("PG connection lost"))
        mock_pool.return_value.acquire = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=conn),
            __aexit__=AsyncMock(return_value=None),
        ))
        f_embed.return_value = [0.1] * 768
        mock_get_q.return_value = AsyncMock()
        rc = await init_icp._run(cid)

    assert rc == 2  # drift signalé, pas de silent success


def test_build_icp_text_scalar_string_does_not_iterate_characters():
    """Patch #8 : si codes_naf arrive comme string scalaire (JSONB mal formé),
    on ne itère pas les caractères — on traite comme un seul élément."""
    row = {
        "description": "Cible",
        "codes_naf": "4520Z",  # string scalaire, pas une list
        "departements": "75",
        "effectif_min": None, "effectif_max": None, "anciennete_min_ans": None,
        "mots_cles_positifs": "réparation",
        "mots_cles_negatifs": None,
    }
    text = init_icp._build_icp_text(row)
    assert "4520Z" in text  # le code complet, pas "4, 5, 2, 0, Z"
    assert "4, 5, 2, 0, Z" not in text
    assert "75" in text
    assert "réparation" in text