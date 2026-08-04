#!/usr/bin/env python3
"""Smoke test de la stack (#14) — PostgreSQL + Qdrant + Ollama.

Un point d'entrée unique qui vérifie en une commande que toute la stack (locale
`make dev` ou VPS prod, #33) est opérationnelle. Toute la config vient de `.env`
via `config/settings.py`, donc le même script tourne en local et sur le VPS.

Sortie : une ligne `[OK]`/`[FAIL]` par check + un message explicite en cas
d'échec. Code de sortie 0 si tout passe, 1 sinon. Pensé pour tourner en < 30 s.

Usage : python scripts/smoke_test.py
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

# Lançable directement (`python scripts/smoke_test.py`) : on ajoute la racine
# du repo au path pour résoudre les imports config/ et utils/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# stdout en UTF-8 (évite un UnicodeEncodeError sous console Windows cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import httpx  # noqa: E402

from config.settings import get_settings  # noqa: E402
from utils import db  # noqa: E402
from utils.embeddings import EMBEDDING_DIM, get_embedding  # noqa: E402

# 11 tables réellement créées par docker/postgres/init/01_schema.sql. L'issue #14
# dit « 8 » mais le schéma (#7) en a 11 (ajoute bloctel_verifications,
# oppositions_rgpd, purge_rgpd_log) — cf. gotchas CLAUDE.md.
EXPECTED_TABLES = {
    "clients", "criteres_ciblage", "icp_profiles", "sources", "campagnes",
    "prospects", "scores", "bloctel_verifications", "oppositions_rgpd",
    "purge_rgpd_log", "appels",
}


async def check_postgres() -> str:
    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        )
    missing = EXPECTED_TABLES - {r["tablename"] for r in rows}
    if missing:
        raise RuntimeError(f"tables manquantes : {sorted(missing)}")
    return f"{len(EXPECTED_TABLES)} tables présentes"


async def check_qdrant() -> str:
    client = db.get_qdrant()
    for coll in (db.COLLECTION_PROSPECTS, db.COLLECTION_ICP):
        if not await client.collection_exists(coll):
            raise RuntimeError(f"collection absente : {coll} (lancer ensure_collections)")
    return "2 collections présentes"


async def check_ollama_model() -> str:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.ollama_url}/api/tags")
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
    want = settings.ollama_embed_model
    if not any(m == want or m.startswith(want + ":") for m in models):
        raise RuntimeError(f"modèle '{want}' absent (dispos : {models})")
    return f"modèle '{want}' chargé"


async def check_embedding() -> str:
    vec = await get_embedding("smoke test prospection b2b")
    if len(vec) != EMBEDDING_DIM:
        raise RuntimeError(f"dimension {len(vec)} (attendu {EMBEDDING_DIM})")
    return f"embedding {EMBEDDING_DIM} dims"


async def check_db_roundtrip() -> str:
    """Insertion d'un prospect de test (via upsert_prospect) + relecture +
    suppression. Crée des FK minimales (client/critère/campagne), nettoyées en
    fin de test par CASCADE — même en cas d'échec (try/finally)."""
    pool = await db.get_pg_pool()
    client_id = None
    try:
        async with pool.acquire() as conn, conn.transaction():
            client_id = await conn.fetchval(
                "INSERT INTO clients (nom_entreprise, secteur, produit_vendu, "
                "zone_intervention) VALUES ('SMOKE_TEST', 'test', 'test', 'test') "
                "RETURNING id;"
            )
            critere_id = await conn.fetchval(
                "INSERT INTO criteres_ciblage (client_id, nom) VALUES ($1, 'smoke') "
                "RETURNING id;",
                client_id,
            )
            campagne_id = await conn.fetchval(
                "INSERT INTO campagnes (client_id, critere_id, nom) VALUES "
                "($1, $2, 'smoke') RETURNING id;",
                client_id, critere_id,
            )
        prospect_id = await db.upsert_prospect({
            "campagne_id": campagne_id,
            "siret": "73282932000074",
            "nom_entreprise": "SMOKE_TEST prospect",
        })
        async with pool.acquire() as conn:
            nom = await conn.fetchval(
                "SELECT nom_entreprise FROM prospects WHERE id = $1;",
                uuid.UUID(prospect_id),
            )
        if nom != "SMOKE_TEST prospect":
            raise RuntimeError("relecture du prospect incohérente")
        return f"round-trip OK (prospect {prospect_id[:8]}…)"
    finally:
        if client_id is not None:
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM clients WHERE id = $1;", client_id)


CHECKS = [
    ("PostgreSQL", check_postgres),
    ("Qdrant", check_qdrant),
    ("Ollama (modèle)", check_ollama_model),
    ("Embedding 768", check_embedding),
    ("Round-trip BDD", check_db_roundtrip),
]


async def main() -> int:
    print("== Smoke test stack ==")
    failures = 0
    for name, check in CHECKS:
        try:
            detail = await check()
            print(f"  [OK]   {name} — {detail}")
        except Exception as exc:  # on rapporte chaque échec, sans s'arrêter
            failures += 1
            print(f"  [FAIL] {name} — {type(exc).__name__}: {exc}")
    await db.close()
    print()
    if failures:
        print(f"ÉCHEC — {failures} check(s) en erreur. Stack non opérationnelle.")
        return 1
    print("OK — stack opérationnelle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
