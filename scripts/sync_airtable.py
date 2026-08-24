"""Synchronise les prospects qualifiés vers Airtable (livraison, #36).

Lit les prospects (statut 'qualifie' par défaut) depuis Postgres et les UPSERT dans
une table Airtable — clé de fusion = SIRET, donc idempotent (re-run = mise à jour,
jamais de doublon). Async (httpx), batché à 10 records/requête (limite Airtable).

Config (settings / .env) : AIRTABLE_PAT, AIRTABLE_BASE_ID, AIRTABLE_TABLE.

    python scripts/sync_airtable.py [--statut qualifie] [--campagne-id UUID] [--dry-run]

RGPD : pousse de la PII (dirigeant, email, tél) vers Airtable (SaaS US) — OK pour le
MVP, à durcir avant tout usage commercial (DPA / EU / purge, cf. #36).
"""
from __future__ import annotations

import argparse
import asyncio

import httpx

from config.settings import get_settings
from utils import db

_AIRTABLE_API = "https://api.airtable.com/v0"
_BATCH = 10  # limite Airtable : 10 records / requête upsert

# Colonne SQL (prospects) -> nom du champ Airtable.
_FIELD_MAP = {
    "nom_entreprise": "Entreprise",
    "siret": "SIRET",
    "ville": "Ville",
    "departement": "Département",
    "code_naf": "Code NAF",
    "score_final": "Score",
    "statut": "Statut",
    "telephone": "Téléphone",
    "email": "Email",
    "site_web": "Site web",
    "nom_dirigeant": "Dirigeant",
    # "Campagne" est ajouté séparément (jointure campagnes.nom).
}


def _to_airtable_fields(row: dict) -> dict:
    """Mappe une ligne prospect -> champs Airtable (ignore None et chaînes vides)."""
    fields: dict[str, object] = {}
    for col, name in _FIELD_MAP.items():
        val = row.get(col)
        if val not in (None, ""):
            fields[name] = val
    if row.get("campagne"):
        fields["Campagne"] = row["campagne"]
    return fields


def _build_records(rows: list[dict]) -> tuple[list[dict], int, int]:
    """Dédup par SIRET (clé d'upsert Airtable). Les lignes arrivent triées par score
    décroissant → on garde la MEILLEURE occurrence de chaque entreprise. Un même SIRET
    peut apparaître dans plusieurs campagnes (unicité BDD = (campagne_id, siret)), mais
    Airtable = un enregistrement par entreprise, et l'upsert refuse deux fois la même
    clé dans une requête. Retourne (records, nb doublons SIRET, nb sans SIRET)."""
    records: list[dict] = []
    seen: set[str] = set()
    sans_siret = doublons = 0
    for r in rows:
        siret = r.get("siret")
        if not siret:
            sans_siret += 1
            continue
        if siret in seen:
            doublons += 1
            continue
        seen.add(siret)
        records.append({"fields": _to_airtable_fields(r)})
    return records, doublons, sans_siret


async def _fetch_prospects(statut: str, campagne_id: str | None) -> list[dict]:
    pool = await db.get_pg_pool()
    conds: list[str] = []
    params: list[object] = []
    if statut:
        params.append(statut)
        conds.append(f"p.statut = ${len(params)}")
    if campagne_id:
        params.append(campagne_id)
        conds.append(f"p.campagne_id = ${len(params)}")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    rows = await pool.fetch(
        f"""
        SELECT p.nom_entreprise, p.siret, p.ville, p.departement, p.code_naf,
               p.score_final, p.statut, p.telephone, p.email, p.site_web,
               p.nom_dirigeant, c.nom AS campagne
        FROM prospects p
        LEFT JOIN campagnes c ON c.id = p.campagne_id
        {where}
        ORDER BY p.score_final DESC
        """,
        *params,
    )
    return [dict(r) for r in rows]


async def _upsert_batch(client: httpx.AsyncClient, url: str, records: list[dict]) -> tuple[int, int]:
    resp = await client.patch(url, json={
        "performUpsert": {"fieldsToMergeOn": ["SIRET"]},
        "typecast": True,
        "records": records,
    })
    resp.raise_for_status()
    data = resp.json()
    return len(data.get("createdRecords", [])), len(data.get("updatedRecords", []))


async def _run(args: argparse.Namespace) -> int:
    s = get_settings()
    if not (s.airtable_pat and s.airtable_base_id and s.airtable_table):
        print("ERREUR : AIRTABLE_PAT / AIRTABLE_BASE_ID / AIRTABLE_TABLE absents du .env")
        return 1

    rows = await _fetch_prospects(args.statut, args.campagne_id)
    records, doublons, sans_siret = _build_records(rows)
    print(f"{len(rows)} prospect(s) lus · {len(records)} SIRET uniques (upsert) · "
          f"{doublons} doublon(s) SIRET · {sans_siret} sans SIRET")

    if args.dry_run:
        print("[dry-run] rien écrit dans Airtable.")
        return 0
    if not records:
        print("Rien à synchroniser.")
        return 0

    url = f"{_AIRTABLE_API}/{s.airtable_base_id}/{s.airtable_table}"
    created = updated = 0
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {s.airtable_pat}"}, timeout=30.0
    ) as client:
        for i in range(0, len(records), _BATCH):
            try:
                c, u = await _upsert_batch(client, url, records[i:i + _BATCH])
            except httpx.HTTPStatusError as exc:
                print(f"ERREUR Airtable (HTTP {exc.response.status_code}) : {exc.response.text[:400]}")
                return 1
            created += c
            updated += u
    print(f"OK Airtable : {created} créé(s), {updated} mis à jour.")
    return 0


async def main() -> int:
    ap = argparse.ArgumentParser(description="Sync prospects -> Airtable (#36)")
    ap.add_argument("--statut", default="qualifie",
                    help="statut à synchroniser (défaut: qualifie ; chaîne vide = tous)")
    ap.add_argument("--campagne-id", default=None, help="limiter à une campagne (UUID)")
    ap.add_argument("--dry-run", action="store_true", help="n'écrit rien, compte seulement")
    args = ap.parse_args()
    try:
        return await _run(args)
    finally:
        await db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
