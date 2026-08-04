"""Script de saisie d'une configuration ICP par client (issue #4).

Insère (ou met à jour) un client + ses `criteres_ciblage` + un `icp_profiles`
en base PostgreSQL, en réutilisant `utils/db.py` (pool asyncpg). Aucune
valeur métier n'est codée en dur ici : tout vient d'un fichier fourni par
l'appelant ou du seed exemplaire `config/icp_seed_example.py` (donnée de
test, pas défaut prod).

L'idempotence est gérée applicativement (le schéma actuel n'a pas de
contrainte UNIQUE sur `(client_id, nom)`) : on SELECT puis UPDATE ou INSERT.

Usage :
    # Dry-run (aucune écriture, valide juste le payload)
    python scripts/seed_icp.py --from-example garages --dry-run

    # Nouveau client depuis le seed garages
    python scripts/seed_icp.py --from-example garages

    # Nouveau client depuis un fichier JSON personnalisé
    python scripts/seed_icp.py --from-file mon-icp.json

    # Mise à jour d'un client existant
    python scripts/seed_icp.py --from-file mon-icp-v2.json --client-id <uuid>

Ne génère PAS l'embedding Qdrant (c'est l'issue #12).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

# Permet `python scripts/seed_icp.py` depuis la racine du repo sans install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.icp_seed_example import ICP_SEEDS  # noqa: E402
from utils.icp_payload import IcpPayload, normalize  # noqa: E402


def _load_payload(args: argparse.Namespace) -> dict[str, Any]:
    """Construit le dict brut du payload depuis `--from-example` ou `--from-file`."""
    if args.from_example:
        if args.from_example not in ICP_SEEDS:
            available = ", ".join(sorted(ICP_SEEDS))
            raise SystemExit(
                f"Seed exemple inconnu : '{args.from_example}'. "
                f"Disponibles : {available}"
            )
        return dict(ICP_SEEDS[args.from_example])

    if args.from_file:
        path = Path(args.from_file)
        if not path.exists():
            raise SystemExit(f"Fichier introuvable : {path}")
        if path.is_dir():
            raise SystemExit(f"Le chemin est un répertoire, pas un fichier : {path}")
        try:
            with path.open(encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"JSON invalide dans {path} : {exc}") from exc
        except UnicodeDecodeError as exc:
            raise SystemExit(
                f"Encodage non-UTF8 dans {path} : convertis le fichier en UTF-8. "
                f"({exc})"
            ) from exc

    raise SystemExit(
        "Il faut fournir --from-example <nom> ou --from-file <path.json>."
    )


async def _upsert_client(conn, p: IcpPayload, client_id: uuid.UUID | None) -> uuid.UUID:
    """Insère un nouveau client ou renvoie l'UUID existant (pas de doublon).

    Si `client_id` est fourni et existe, on ne touche pas à la fiche client
    (la mise à jour porte sur les critères, pas sur l'identité du client).
    """
    if client_id is not None:
        exists = await conn.fetchval(
            "SELECT 1 FROM clients WHERE id = $1", client_id
        )
        if not exists:
            # Ask First (spec) : FK violée — on HALT avant d'insérer.
            raise SystemExit(
                f"client-id {client_id} introuvable en base. Création d'un "
                f"nouveau client refusée sans confirmation (Ask First). "
                f"Re-exécutez sans --client-id pour créer un nouveau client."
            )
        return client_id

    row = await conn.fetchrow(
        """
        INSERT INTO clients (nom_entreprise, secteur, produit_vendu,
            zone_intervention, contact_nom, contact_email, contact_telephone)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id;
        """,
        p.nom_entreprise, p.secteur, p.produit_vendu, p.zone_intervention,
        p.contact_nom, p.contact_email, p.contact_telephone,
    )
    return row["id"]


async def _upsert_criteres(conn, client_id: uuid.UUID, p: IcpPayload) -> uuid.UUID:
    """Upsert applicatif sur `criteres_ciblage` (client_id, nom)."""
    existing = await conn.fetchval(
        "SELECT id FROM criteres_ciblage WHERE client_id = $1 AND nom = $2",
        client_id, p.nom,
    )
    fields = p.to_criteres_row()
    if existing is not None:
        await conn.execute(
            """
            UPDATE criteres_ciblage SET
                description_icp = $2, codes_naf = $3, departements = $4,
                effectif_min = $5, effectif_max = $6, anciennete_min_ans = $7,
                exiger_site_web = $8, exiger_email = $9,
                mots_cles_positifs = $10, mots_cles_negatifs = $11,
                updated_at = NOW()
            WHERE id = $1;
            """,
            existing, fields["description_icp"], fields["codes_naf"],
            fields["departements"], fields["effectif_min"], fields["effectif_max"],
            fields["anciennete_min_ans"], fields["exiger_site_web"],
            fields["exiger_email"], fields["mots_cles_positifs"],
            fields["mots_cles_negatifs"],
        )
        return existing

    row = await conn.fetchrow(
        """
        INSERT INTO criteres_ciblage (client_id, nom, description_icp,
            codes_naf, departements, effectif_min, effectif_max,
            anciennete_min_ans, exiger_site_web, exiger_email,
            mots_cles_positifs, mots_cles_negatifs)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id;
        """,
        client_id, fields["nom"], fields["description_icp"],
        fields["codes_naf"], fields["departements"], fields["effectif_min"],
        fields["effectif_max"], fields["anciennete_min_ans"],
        fields["exiger_site_web"], fields["exiger_email"],
        fields["mots_cles_positifs"], fields["mots_cles_negatifs"],
    )
    return row["id"]


async def _upsert_icp_profile(
    conn, client_id: uuid.UUID, critere_id: uuid.UUID, p: IcpPayload
) -> uuid.UUID:
    """Upsert applicatif sur `icp_profiles` (client_id, nom).

    `description` reprend `description_icp` du critère : c'est le texte qui
    sera embarqué plus tard par #12. `qdrant_point_id` reste NULL (embedding
    non généré ici).
    """
    description = p.description_icp or p.nom
    existing = await conn.fetchval(
        "SELECT id FROM icp_profiles WHERE client_id = $1 AND nom = $2",
        client_id, p.nom,
    )
    if existing is not None:
        await conn.execute(
            """
            UPDATE icp_profiles SET critere_id = $2, description = $3,
                -- La description ICP a changé → l'embedding Qdrant (généré par
                -- #12) est devenu stale. On reset le point_id pour forcer une
                -- re-génération lors du prochain init_icp.py.
                qdrant_point_id = NULL, embedding_version = NULL,
                updated_at = NOW()
            WHERE id = $1;
            """,
            existing, critere_id, description,
        )
        return existing

    row = await conn.fetchrow(
        """
        INSERT INTO icp_profiles (client_id, critere_id, nom, description)
        VALUES ($1, $2, $3, $4)
        RETURNING id;
        """,
        client_id, critere_id, p.nom, description,
    )
    return row["id"]


async def _run(args: argparse.Namespace) -> int:
    raw = _load_payload(args)
    try:
        payload = normalize(raw)
    except Exception as exc:  # pydantic.ValidationError + SystemExit remontés
        if isinstance(exc, SystemExit):
            raise
        print(f"❌ Payload invalide : {exc}", file=sys.stderr)
        return 2

    if args.client_id:
        try:
            client_id = uuid.UUID(args.client_id)
        except ValueError as exc:  # UUID mal formé
            raise SystemExit(
                f"--client-id invalide : '{args.client_id}' n'est pas un UUID "
                f"valide (ex. 550e8400-e29b-41d4-a716-446655440000)."
            ) from exc
    else:
        client_id = None

    if args.dry_run:
        print("[dry-run] Payload validé ✓")
        print(json.dumps(
            {"client": payload.to_client_row(),
             "criteres": payload.to_criteres_row(),
             "icp_description": payload.description_icp or payload.nom,
             "client_id": str(client_id) if client_id else "<nouveau>"},
            indent=2, ensure_ascii=False,
        ))
        print("[dry-run] Aucune écriture en base.")
        return 0

    from utils import db  # import différé : le dry-run n'a pas besoin de DB
    try:
        pool = await db.get_pg_pool()  # créé sur la loop courante
        async with pool.acquire() as conn, conn.transaction():
            cid = await _upsert_client(conn, payload, client_id)
            crit_id = await _upsert_criteres(conn, cid, payload)
            icp_id = await _upsert_icp_profile(conn, cid, crit_id, payload)
            print(f"✓ client_id      : {cid}")
            print(f"✓ critere_id     : {crit_id}")
            print(f"✓ icp_profile_id : {icp_id}")
    finally:
        # Ferme le pool sur la MÊME loop que sa création (un second
        # asyncio.run() laisserait les connexions orphelines).
        await db.close()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Saisie d'une configuration ICP par client (issue #4)."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-example", metavar="NOM",
                     help="Seed exemplaire (donnée de test), ex. 'garages'.")
    src.add_argument("--from-file", metavar="PATH",
                     help="Fichier JSON contenant le payload ICP.")
    parser.add_argument("--client-id", metavar="UUID", default=None,
                        help="UUID d'un client existant à mettre à jour.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Valide et affiche le payload sans écrire en base.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    # Un seul asyncio.run : le pool asyncpg y est créé ET fermé sur la même
    # loop (un second asyncio.run laisserait les connexions liées à une loop
    # fermée → RuntimeError "Event loop is closed").
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())