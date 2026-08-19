"""Test d'intégration (#31) — garde SQL du compteur `prospects_qualifies`.

Vérifie, contre un **vrai PostgreSQL** (stack docker locale), l'invariant du
compteur de qualifiés posé par `utils.db.save_score` (#27) :

    `campagnes.prospects_qualifies` n'est incrémenté QUE sur une transition de
    statut vers `qualifie` (ancien statut ≠ `qualifie`).

L'historique `scores` autorisant plusieurs lignes par prospect, sans cette garde
un simple re-scoring double-compterait les qualifiés. Ce test exerce la vraie
requête `FOR UPDATE` + l'`UPDATE … + 1` conditionnel dans la transaction réelle —
ce qu'un test unitaire mocké ne peut pas garantir.

⚠️ `@integration` (exclu du run par défaut, voir conftest.py) : nécessite le
Postgres de la stack (`docker compose --profile dev up -d`). Lancer :

    pytest tests/test_persistance_counter.py -m integration -v

Données isolées : un client + critère + campagne jetables (UUID aléatoires),
supprimés en fin de test. Aucune valeur métier sectorielle codée en dur
(règle #3) — placeholders neutres.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from utils import db

pytestmark = pytest.mark.integration


async def _qualifies(campagne_id: uuid.UUID) -> int:
    """Lit le compteur courant `prospects_qualifies` de la campagne."""
    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT prospects_qualifies FROM campagnes WHERE id = $1;", campagne_id
        )


async def _nb_scores(prospect_id: str) -> int:
    """Compte les lignes d'historique `scores` d'un prospect."""
    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM scores WHERE prospect_id = $1;", uuid.UUID(prospect_id)
        )


async def _statut(prospect_id: str) -> str:
    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT statut FROM prospects WHERE id = $1;", uuid.UUID(prospect_id)
        )


@pytest_asyncio.fixture
async def campagne_jetable():
    """Crée client + critère + campagne isolés (UUID aléatoires) et les supprime
    en fin de test. Ferme ensuite le pool PG singleton (même raison que
    `_clean_db_pool` de test_init_campagne : éviter le partage d'une connexion en
    cours de reset entre tests d'intégration)."""
    client_id = uuid.uuid4()
    critere_id = uuid.uuid4()
    campagne_id = uuid.uuid4()

    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO clients (id, nom_entreprise, secteur, produit_vendu, "
            "zone_intervention, statut) "
            "VALUES ($1, $2, 'conseil', 'x', 'France', 'essai');",
            client_id, "Compteur SARL",
        )
        await conn.execute(
            "INSERT INTO criteres_ciblage (id, client_id, nom, codes_naf, departements) "
            "VALUES ($1, $2, 'crit test compteur', ARRAY['6201Z'], ARRAY['75']);",
            critere_id, client_id,
        )
        await conn.execute(
            "INSERT INTO campagnes (id, client_id, critere_id, nom, statut) "
            "VALUES ($1, $2, $3, 'camp test compteur', 'brouillon');",
            campagne_id, client_id, critere_id,
        )
    try:
        yield campagne_id
    finally:
        # Suppression explicite dans l'ordre inverse des dépendances (CASCADE gère
        # prospects + scores via campagnes ; on retire ensuite critère puis client).
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM campagnes WHERE id = $1;", campagne_id)
            await conn.execute("DELETE FROM criteres_ciblage WHERE id = $1;", critere_id)
            await conn.execute("DELETE FROM clients WHERE id = $1;", client_id)
        await db.close()


def _score_data(statut: str, score_final: int) -> dict:
    """Payload minimal pour `save_score` (les colonnes absentes gardent leur défaut)."""
    return {
        "score_regles": score_final,
        "score_llm": score_final,
        "score_embedding": 0.0,
        "score_final": score_final,
        "statut": statut,
        "modele_llm": "test-guard",
    }


@pytest.mark.asyncio
async def test_transition_vers_qualifie_incremente_une_fois(campagne_jetable) -> None:
    """AC #31 : une transition `nouveau` → `qualifie` incrémente le compteur de 1 ;
    un re-scoring qui reste `qualifie` ne le ré-incrémente PAS (garde de transition).
    L'historique `scores`, lui, accumule bien une ligne par scoring."""
    campagne_id = campagne_jetable
    assert await _qualifies(campagne_id) == 0

    prospect_id = await db.upsert_prospect({
        "campagne_id": campagne_id,
        "nom_entreprise": "Cible Alpha",
        "siret": "12345678901234",
    })
    # Statut initial par défaut du schéma.
    assert await _statut(prospect_id) == "nouveau"

    # 1er scoring : transition nouveau -> qualifie => compteur +1.
    await db.save_score(prospect_id, _score_data("qualifie", 82))
    assert await _statut(prospect_id) == "qualifie"
    assert await _qualifies(campagne_id) == 1
    assert await _nb_scores(prospect_id) == 1

    # 2e scoring : reste qualifie => compteur INCHANGÉ (pas de double-comptage),
    # mais l'historique gagne une 2e ligne.
    await db.save_score(prospect_id, _score_data("qualifie", 90))
    assert await _qualifies(campagne_id) == 1
    assert await _nb_scores(prospect_id) == 2


@pytest.mark.asyncio
async def test_statut_non_qualifie_n_incremente_pas(campagne_jetable) -> None:
    """Un prospect scoré `nouveau` puis `invalide` ne touche jamais le compteur."""
    campagne_id = campagne_jetable

    prospect_id = await db.upsert_prospect({
        "campagne_id": campagne_id,
        "nom_entreprise": "Cible Beta",
        "siret": "23456789012345",
    })
    await db.save_score(prospect_id, _score_data("nouveau", 45))
    assert await _qualifies(campagne_id) == 0
    await db.save_score(prospect_id, _score_data("invalide", 12))
    assert await _statut(prospect_id) == "invalide"
    assert await _qualifies(campagne_id) == 0


@pytest.mark.asyncio
async def test_deux_prospects_qualifies_comptent_deux(campagne_jetable) -> None:
    """Deux prospects distincts qui deviennent qualifiés comptent 2 (le compteur est
    par campagne, pas par prospect)."""
    campagne_id = campagne_jetable

    p1 = await db.upsert_prospect({
        "campagne_id": campagne_id, "nom_entreprise": "Cible Un", "siret": "34567890123456",
    })
    p2 = await db.upsert_prospect({
        "campagne_id": campagne_id, "nom_entreprise": "Cible Deux", "siret": "45678901234567",
    })
    await db.save_score(p1, _score_data("qualifie", 70))
    await db.save_score(p2, _score_data("qualifie", 65))
    assert await _qualifies(campagne_id) == 2
