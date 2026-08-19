"""init_icp — génère l'embedding ICP d'un client → Qdrant (issue #12).

Lit la description ICP du client en base — `icp_profiles.description` avec
fallback sur `criteres_ciblage.description_icp` (spec #12) — la enrichit des
critères structurés (NAF, effectif, mots-clés), génère l'embedding via
`utils/embeddings.py` (Ollama nomic-embed-text, règle #5), l'upsert dans la
collection Qdrant `icp_profiles` (utils/db.py), puis enregistre le
`qdrant_point_id` + `embedding_version` sur la ligne `icp_profiles`.

Règle #3 (CLAUDE.md) : aucune valeur ICP codée en dur ici — tout vient de la
base. Le script ne fait que lire, embarquer et stocker.

Idempotence (AC #3) : le point Qdrant utilise l'UUID de `icp_profiles.id` comme
id de point. Une ré-exécution met à jour le MÊME point (upsert Qdrant), pas de
doublon. Si `seed_icp.py` (#4) a reset `qdrant_point_id = NULL` suite à un
changement de description, ce script le régénère.

Usage (CLAUDE.md) :
    python scripts/init_icp.py --client-id <uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

# Permet `python scripts/init_icp.py` depuis la racine du repo sans install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import db, embeddings  # noqa: E402


# Version d'embedding tracée en base (permet la ré-indexation si le modèle
# change — cf. colonne `icp_profiles.embedding_version`). Alignée sur le modèle
# configuré dans `config/settings.py` (OLLAMA_EMBED_MODEL), pas codée en dur
# métier — c'est un tag technique d'infrastructure.
def _embedding_version() -> str:
    from config.settings import get_settings
    return get_settings().ollama_embed_model


def _build_icp_text(row: dict[str, Any]) -> str:
    """Construit le texte libre à embarmer : description ICP enrichie des
    critères structurés (NAF, effectif, mots-clés) pour un embedding plus
    expressif que la seule description.

    Args:
        row: dict renvoyé par `_load_icp` (description + champs de ciblage).

    Raises:
        ValueError: si la description ET les critères sont vides (rien à
            embarmer).
    """
    parts: list[str] = []

    desc = (row.get("description") or "").strip()
    if desc:
        parts.append(desc)

    # `_as_list` protège contre un JSONB scalaire (ex. "4520Z" au lieu de
    # ["4520Z"]) : sans ça, ", ".join("4520Z") itère les caractères →
    # "4, 5, 2, 0, Z" — embedding silencieusement corrompu.
    def _as_list(val: Any) -> list[str]:
        if val is None:
            return []
        if isinstance(val, str):
            return [val]
        if isinstance(val, (list, tuple)):
            return [str(x) for x in val]
        return [str(val)]

    codes_naf = _as_list(row.get("codes_naf"))
    if codes_naf:
        parts.append("Codes NAF ciblés : " + ", ".join(codes_naf))

    departements = _as_list(row.get("departements"))
    if departements:
        parts.append("Zones géographiques : " + ", ".join(departements))

    eff_min = row.get("effectif_min")
    eff_max = row.get("effectif_max")
    if eff_min is not None or eff_max is not None:
        borne_basse = eff_min if eff_min is not None else ""
        borne_haute = eff_max if eff_max is not None else ""
        parts.append(f"Effectif : {borne_basse}–{borne_haute} salariés")

    anc = row.get("anciennete_min_ans")
    if anc is not None:
        parts.append(f"Ancienneté minimale : {anc} ans")

    pos = _as_list(row.get("mots_cles_positifs"))
    if pos:
        parts.append("Mots-clés positifs : " + ", ".join(pos))

    neg = _as_list(row.get("mots_cles_negatifs"))
    if neg:
        parts.append("Mots-clés négatifs (exclusions) : " + ", ".join(neg))

    text = "\n".join(parts).strip()
    if not text:
        raise ValueError(
            "Aucun texte ICP à embarmer : description et critères vides pour "
            "ce client. Renseignez `description_icp` ou des critères de "
            "ciblage dans `criteres_ciblage` avant de générer l'embedding."
        )
    return text


async def _load_icp(conn, client_id: uuid.UUID) -> dict[str, Any] | None:
    """Charge l'ICP d'un client depuis PG : description + critères structurés.

    Joint `icp_profiles` (description de référence pour l'embedding) et
    `criteres_ciblage` (critères structurés) en LEFT JOIN — un client avec un
    `icp_profiles` actif mais sans `criteres_ciblage` reste embarquable (la
    description seule suffit). Retourne None si le client n'existe pas.

    Description : `icp_profiles.description` avec fallback sur
    `criteres_ciblage.description_icp` (spec #12 : « lit
    `criteres_ciblage.description_icp` »). Le `critere_id` retourné est le
    critère *résolu* (COALESCE de `icp.critere_id` et du fallback), pas le
    `icp.critere_id` nullable — pour que le payload Qdrant porte le vrai
    critère utilisé.
    """
    row = await conn.fetchrow(
        """
        SELECT
            icp.id                        AS icp_profile_id,
            COALESCE(icp.description, cc.description_icp) AS description,
            cc.id                         AS critere_id,
            cc.codes_naf,
            cc.departements,
            cc.effectif_min,
            cc.effectif_max,
            cc.anciennete_min_ans,
            cc.mots_cles_positifs,
            cc.mots_cles_negatifs
        FROM icp_profiles icp
        LEFT JOIN criteres_ciblage cc ON cc.id = COALESCE(
            icp.critere_id,
            (SELECT id FROM criteres_ciblage
             WHERE client_id = icp.client_id AND actif = TRUE
             ORDER BY created_at DESC LIMIT 1)
        )
        WHERE icp.client_id = $1 AND icp.actif = TRUE
        ORDER BY icp.created_at DESC
        LIMIT 1;
        """,
        client_id,
    )
    return dict(row) if row else None


async def _run(client_id_str: str) -> int:
    """Orchestration : load → embed → ensure_collections → upsert Qdrant
    → update PG. Retourne un exit code."""
    try:
        client_id = uuid.UUID(client_id_str)
    except ValueError:
        print(
            f"--client-id invalide : '{client_id_str}' n'est pas un UUID "
            f"valide (ex. 550e8400-e29b-41d4-a716-446655440000).",
            file=sys.stderr,
        )
        return 2

    try:
        pool = await db.get_pg_pool()
        async with pool.acquire() as conn:
            row = await _load_icp(conn, client_id)
            if row is None:
                print(
                    f"Aucun profil ICP actif trouvé pour le client {client_id}. "
                    f"Créez d'abord le client et ses critères avec "
                    f"`scripts/seed_icp.py` (#4).",
                    file=sys.stderr,
                )
                return 2

            try:
                text = _build_icp_text(row)
            except ValueError as exc:
                print(f"❌ {exc}", file=sys.stderr)
                return 2

            # Embedding (Ollama CPU, règle #5). Erreur Ollama (service down,
            # timeout, dimension inattendue) → exit 2 propre avec message,
            # cohérent avec les autres paths d'erreur.
            try:
                embedding = await embeddings.get_embedding(text)
            except Exception as exc:
                print(
                    f"❌ Génération d'embedding échouée (Ollama) : {exc}. "
                    f"Vérifiez que le service tourne (docker compose --profile "
                    f"dev up -d ollama) et que OLLAMA_EMBED_MODEL est correct.",
                    file=sys.stderr,
                )
                return 2

            # Collection Qdrant + index payload (idempotent).
            await db.ensure_collections()

            # Upsert Qdrant : id du point = icp_profile_id (UUID PG, coeré en
            # str pour cohérence avec db.py::upsert_prospect_embedding). AC #3 :
            # une ré-exécution met à jour le même point, pas de doublon.
            icp_profile_id = str(row["icp_profile_id"])
            embedding_version = _embedding_version()
            qdrant = db.get_qdrant()
            from qdrant_client import models
            await qdrant.upsert(
                collection_name=db.COLLECTION_ICP,
                points=[
                    models.PointStruct(
                        id=icp_profile_id,
                        vector=embedding,
                        payload={
                            "client_id": str(client_id),
                            "critere_id": str(row["critere_id"])
                            if row.get("critere_id") else None,
                            "description": row.get("description"),
                        },
                    )
                ],
            )

            # Enregistre qdrant_point_id + embedding_version en PG. Si l'UPDATE
            # échoue ici (conn perdue, timeout), le vecteur est déjà dans Qdrant
            # mais PG reste à NULL → drift. On logge explicitement l'erreur
            # (Qdrant n'est pas transactionnable, pas de rollback possible).
            try:
                await conn.execute(
                    """
                    UPDATE icp_profiles
                    SET qdrant_point_id = $2,
                        embedding_version = $3
                    WHERE id = $1;
                    -- NB : `icp_profiles` n'a PAS de colonne `updated_at` (seul
                    -- `created_at` existe, cf. 01_schema.sql) — ne pas la SET,
                    -- sinon l'UPDATE échoue et `qdrant_point_id` n'est jamais
                    -- persisté → couche embedding (#26) muette en mode campagne.
                    """,
                    icp_profile_id,
                    icp_profile_id,
                    embedding_version,
                )
            except Exception as exc:
                print(
                    f"⚠ Drift Qdrant/PG : le vecteur a été upserté dans Qdrant "
                    f"(point {icp_profile_id}) mais l'UPDATE PG a échoué : {exc}. "
                    f"Relancez le script pour resynchroniser.",
                    file=sys.stderr,
                )
                return 2

        print(f"✓ ICP embedding généré pour le client {client_id}")
        print(f"  icp_profile_id   : {icp_profile_id}")
        print(f"  qdrant_point_id  : {icp_profile_id}")
        print(f"  embedding_version: {embedding_version}")
        print(f"  vecteurs         : {len(embedding)} dims")
        return 0
    finally:
        # Ferme le pool sur la MÊME loop que sa création (cf. seed_icp.py).
        await db.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Génère l'embedding ICP d'un client depuis sa description en base "
            "→ Qdrant (issue #12)."
        ),
    )
    parser.add_argument(
        "--client-id", required=True, metavar="UUID",
        help="UUID du client dont on veut générer l'embedding ICP.",
    )
    return parser


def _force_utf8_stdio() -> None:
    """Force stdout/stderr en UTF-8 — sinon `--help` crash sur console cp1252
    Windows (UnicodeEncodeError sur les accents). Idempotent. Cf. main.py (#11).
    """
    import codecs
    import io

    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", "") or ""
        try:
            is_utf8 = codecs.lookup(encoding).name == "utf-8"
        except (LookupError, TypeError):
            is_utf8 = False
        if not is_utf8:
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                try:
                    reconfigure(encoding="utf-8", errors="replace")
                except (AttributeError, ValueError, OSError, io.UnsupportedOperation):
                    pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    args = _build_parser().parse_args(argv)
    # Un seul asyncio.run : le pool asyncpg y est créé ET fermé sur la même
    # loop (un second asyncio.run laisserait les connexions liées à une loop
    # fermée → RuntimeError "Event loop is closed").
    return asyncio.run(_run(args.client_id))


if __name__ == "__main__":
    raise SystemExit(main())