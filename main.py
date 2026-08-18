"""Point d'entrée CLI — Agent IA de Prospection B2B (multi-secteurs).

Issue #29 — pilote le pipeline (`graph.workflow.run`, #28) via `argparse`.
Trois modes :
- `--campagne-id <uuid>` : charge une campagne en base et lance le pipeline complet
  (écrit prospects + scores, sauf `--dry-run`).
- `--depts/--naf [--limit]` : mode **ad hoc** (tests locaux) — ICP synthétisé depuis
  les flags, pipeline en mémoire, **dry-run forcé** (aucune écriture ; `upsert_prospect`
  exige un `campagne_id` en base, absent ici).
- `--list-campagnes` : liste les campagnes existantes et leur statut (lecture seule).

Aucune valeur métier (ICP) codée en dur : en mode campagne l'ICP vient de la base
(`criteres_ciblage`) ; en ad hoc, les codes NAF / départements sont des **paramètres
CLI** explicites, pas des defaults globaux (CLAUDE.md règle #3).
"""
from __future__ import annotations

import argparse
import asyncio
import codecs
import io
import sys


def _is_utf8(encoding: str) -> bool:
    """True si l'encodage est sémantiquement UTF-8 (utf-8, utf_8, utf-8-sig, cp65001…)."""
    try:
        return codecs.lookup(encoding).name == "utf-8"
    except (LookupError, TypeError):
        return False


def _force_utf8_stdio() -> None:
    """Force stdout/stderr en UTF-8 — sinon `--help`/résumés crashent sur console
    cp1252 Windows (accents français). Idempotent, jamais bloquant au démarrage."""
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", "") or ""
        if not _is_utf8(encoding):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                try:
                    reconfigure(encoding="utf-8", errors="replace")
                except (AttributeError, ValueError, OSError, io.UnsupportedOperation):
                    pass


def _split_csv(valeur: str | None) -> list[str]:
    """'75, 92' -> ['75', '92'] ; None/'' -> []."""
    return [x.strip() for x in valeur.split(",") if x.strip()] if valeur else []


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prospection-b2b",
        description=(
            "Agent IA de prospection B2B générique — collecte (Sirene), enrichit, "
            "score (règles + Claude + embeddings Qdrant) et persiste la file d'appel, "
            "selon l'ICP du client (configuré en base)."
        ),
    )
    parser.add_argument(
        "--campagne-id", metavar="UUID",
        help="UUID d'une campagne existante — lance le pipeline complet.",
    )
    parser.add_argument(
        "--depts", metavar="75,92",
        help="Départements (mode ad hoc, dry-run forcé).",
    )
    parser.add_argument(
        "--naf", metavar="45.20A,45.20B",
        help="Codes NAF (mode ad hoc). Sirene itère départements × NAF.",
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="Plafond de prospects collectés (défaut pipeline : 500).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Exécute le pipeline sans AUCUNE écriture en base / Qdrant.",
    )
    parser.add_argument(
        "--list-campagnes", action="store_true",
        help="Liste les campagnes existantes et leur statut (lecture seule).",
    )
    return parser


def _print_resume(titre: str, etat: dict, dry_run: bool) -> None:
    tag = " [DRY-RUN]" if dry_run else ""
    print(
        f"{titre}{tag} — collectés: {etat.get('collectes', 0)}, "
        f"qualifiés: {etat.get('qualifies', 0)}, "
        f"erreurs: {len(etat.get('erreurs', []))}"
    )
    for err in etat.get("erreurs", [])[:5]:
        print(f"  ! {err}", file=sys.stderr)


async def _lister_campagnes() -> int:
    from utils import db
    try:
        pool = await db.get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, nom, statut, prospects_collectes, prospects_qualifies "
                "FROM campagnes ORDER BY nom;"
            )
        if not rows:
            print("Aucune campagne en base.")
        for r in rows:
            print(
                f"{r['id']}  [{r['statut']}]  {r['nom']}  — "
                f"collectés: {r['prospects_collectes']}, qualifiés: {r['prospects_qualifies']}"
            )
        return 0
    finally:
        await db.close()


async def _run_campagne(campagne_id: str, limit: int | None, dry_run: bool) -> int:
    import uuid
    from graph.workflow import run
    from utils import db

    try:
        uuid.UUID(campagne_id)
    except (ValueError, TypeError):
        print(f"[erreur] --campagne-id invalide : '{campagne_id}' (UUID attendu).", file=sys.stderr)
        return 2

    state: dict = {"campagne_id": campagne_id, "dry_run": dry_run}
    if limit is not None:
        state["limit"] = limit
    try:
        etat = await run(state)
    finally:
        await db.close()

    _print_resume(f"Campagne {campagne_id}", etat, dry_run)
    # Un échec de node prérequis (campagne/ICP introuvable, Sirene KO) est capté par
    # `run` dans `state["erreurs"]` → code de sortie non nul + message déjà affiché.
    erreurs = etat.get("erreurs", [])
    prereq_ko = any(e.startswith(("init_campagne:", "fetch_sirene:")) for e in erreurs)
    return 1 if prereq_ko else 0


async def _run_adhoc(depts: str | None, naf: str | None, limit: int | None) -> int:
    import uuid
    from graph.workflow import run
    from models.criteres import CriteresCiblage
    from utils import db

    criteres = CriteresCiblage(
        nom=f"ad-hoc {depts or ''} {naf or ''}".strip(),
        codes_naf=_split_csv(naf),
        departements=_split_csv(depts),
    )
    state: dict = {
        "campagne_id": str(uuid.uuid4()),  # jetable — ad hoc = dry-run, jamais persisté
        "criteres": criteres,              # → init_campagne no-op (état pré-peuplé)
        "config_scoring": {},              # poids par défaut à l'agrégation
        "icp_embedding": None,             # pas d'ICP embarqué en ad hoc → couche neutre
        "dry_run": True,                   # forcé : pas de campagne en base pour persister
    }
    if limit is not None:
        state["limit"] = limit
    try:
        etat = await run(state)
    finally:
        await db.close()

    _print_resume("Ad hoc", etat, dry_run=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_campagnes:
        return asyncio.run(_lister_campagnes())

    mode_adhoc = bool(args.depts or args.naf)
    if args.campagne_id and mode_adhoc:
        parser.error("--depts/--naf (mode ad hoc) sont exclusifs de --campagne-id.")
    if not args.campagne_id and not mode_adhoc:
        parser.error(
            "Rien à faire : fournir --campagne-id, ou --depts/--naf (ad hoc), "
            "ou --list-campagnes."
        )

    if args.campagne_id:
        return asyncio.run(_run_campagne(args.campagne_id, args.limit, args.dry_run))
    return asyncio.run(_run_adhoc(args.depts, args.naf, args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
