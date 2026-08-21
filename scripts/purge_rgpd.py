"""purge_rgpd — applique la politique de rétention RGPD (issue #41).

Job récurrent (cron quotidien, #34) — **jamais** de purge manuelle (CLAUDE.md règle #9).
Applique les 4 durées de conservation de `docs/LEGAL.md` (§ Durée de conservation) :

    - prospects **invalides**                 → supprimés après **6 mois**
    - prospects **qualifiés non convertis**    → supprimés après **3 ans**
    - historique **appels**                    → supprimé après **1 an**
    - **logs système** (`purge_rgpd_log`)      → supprimés après **3 mois**

Chaque suppression est journalisée dans `purge_rgpd_log` (`table_cible`, `nb_lignes`,
`motif`) pour l'audit (critère d'acceptance #41).

⚠️ **`oppositions_rgpd` n'est JAMAIS purgée.** Un SIRET opposé ne doit plus jamais être
recontacté, indépendamment de la purge (#41). La table est clé-primée sur `siret`, **sans
FK vers `prospects`** : supprimer un prospect opposé n'efface donc pas son opposition — la
liste de suppression survit à la purge et reste opposable aux campagnes futures.

Ancre temporelle :
    - prospects : `created_at` (date de collecte) — lecture *data-minimization* (on ne
      conserve pas une donnée collectée au-delà de la durée), cohérente avec le critère
      « prospect invalide de plus de 6 mois ». Supprimer un prospect cascade ses `scores`
      / `appels` / `bloctel_verifications` (FK `ON DELETE CASCADE`).
    - appels : `COALESCE(date_appel, created_at)` (l'événement, sinon la création).

« Non converti » = statut resté `qualifie` (un prospect converti passe à `rdv`, exclu).

Les durées viennent de LEGAL.md (constantes légales, pas des valeurs métier ICP de la
règle #3). Surchargeables par variable d'env **pour les tests uniquement**.

Usage :
    python scripts/purge_rgpd.py             # applique la purge + journalise
    python scripts/purge_rgpd.py --dry-run   # compte seulement, AUCUNE suppression
"""
from __future__ import annotations

import argparse
import asyncio
import codecs
import os
import sys
from pathlib import Path

# Permet `python scripts/purge_rgpd.py` depuis la racine du repo sans install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import db  # noqa: E402

# Table de suppression RGPD à NE JAMAIS purger (garde-fou explicite, cf. docstring).
_TABLE_INTOUCHABLE = "oppositions_rgpd"


def _intervalle(env: str, defaut: str) -> str:
    """Intervalle Postgres pour une règle. Défaut = LEGAL.md ; surcharge env pour tests."""
    return os.getenv(env, defaut)


def _regles() -> tuple[tuple[str, str, str], ...]:
    """(table_cible, motif, clause WHERE) — l'ordre est sans importance (règles disjointes).

    Les valeurs (table/WHERE) sont des constantes internes, jamais des entrées externes :
    pas de risque d'injection SQL."""
    return (
        (
            "prospects", "prospects invalides > 6 mois",
            f"statut = 'invalide' AND created_at < now() - INTERVAL '{_intervalle('RGPD_INVALIDES', '6 months')}'",
        ),
        (
            "prospects", "prospects qualifies non convertis > 3 ans",
            f"statut = 'qualifie' AND created_at < now() - INTERVAL '{_intervalle('RGPD_QUALIFIES', '3 years')}'",
        ),
        (
            "appels", "historique appels > 1 an",
            f"COALESCE(date_appel, created_at) < now() - INTERVAL '{_intervalle('RGPD_APPELS', '1 year')}'",
        ),
        (
            "purge_rgpd_log", "logs systeme > 3 mois",
            f"purge_le < now() - INTERVAL '{_intervalle('RGPD_LOGS', '3 months')}'",
        ),
    )


async def purger(dry_run: bool = False) -> list[tuple[str, str, int]]:
    """Applique (ou simule si `dry_run`) les règles de rétention. Retourne la liste
    `(table_cible, motif, nb_lignes)`. Chaque suppression réelle est journalisée dans
    `purge_rgpd_log` **dans la même transaction** que la suppression (atomicité)."""
    resultats: list[tuple[str, str, int]] = []
    pool = await db.get_pg_pool()
    for table, motif, where in _regles():
        assert table != _TABLE_INTOUCHABLE, f"garde-fou : {_TABLE_INTOUCHABLE} ne se purge jamais"
        async with pool.acquire() as conn:
            if dry_run:
                nb = await conn.fetchval(f"SELECT count(*) FROM {table} WHERE {where};")
            else:
                async with conn.transaction():
                    nb = await conn.fetchval(
                        f"WITH del AS (DELETE FROM {table} WHERE {where} RETURNING 1) "
                        f"SELECT count(*) FROM del;"
                    )
                    # Journal d'audit — sauf si rien supprimé (pas de bruit).
                    if nb:
                        await conn.execute(
                            "INSERT INTO purge_rgpd_log (table_cible, nb_lignes, motif) "
                            "VALUES ($1, $2, $3);",
                            table, nb, motif,
                        )
        resultats.append((table, motif, nb))
    return resultats


def _force_utf8_stdio() -> None:
    """stdout/stderr en UTF-8 (accents FR sur console Windows). Idempotent."""
    for stream in (sys.stdout, sys.stderr):
        enc = getattr(stream, "encoding", "") or ""
        try:
            if codecs.lookup(enc).name != "utf-8":
                stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (LookupError, AttributeError, ValueError, TypeError, OSError):
            pass


async def _run(dry_run: bool) -> int:
    try:
        resultats = await purger(dry_run=dry_run)
    finally:
        await db.close()
    tag = " [DRY-RUN]" if dry_run else ""
    total = sum(n for _, _, n in resultats)
    print(f"Purge RGPD{tag} — {total} ligne(s) {'à supprimer' if dry_run else 'supprimée(s)'} :")
    for table, motif, nb in resultats:
        print(f"  {nb:>6}  {table:16s} {motif}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="purge-rgpd",
        description="Applique la politique de rétention RGPD (docs/LEGAL.md). Job récurrent, "
                    "jamais manuel (CLAUDE.md règle #9).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compte seulement les lignes concernées, sans rien supprimer.",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
