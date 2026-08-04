"""Point d'entrée CLI — Agent IA de Prospection B2B (multi-secteurs).

Issue #11 (Sprint 1) — STUB. L'implémentation complète du CLI argparse et de
l'orchestration du pipeline est portée par l'issue #29. Ici on ne pose que la
structure : `python main.py --help` doit fonctionner même sans pipeline.

Aucune valeur métier (ICP) codée en dur — l'ICP vient de la base
(`criteres_ciblage`), voir `docs/ARCHITECTURE.md` et CLAUDE.md règle #3.
"""
from __future__ import annotations

import argparse
import codecs
import io
import sys


def _is_utf8(encoding: str) -> bool:
    """True si l'encodage est sémantiquement UTF-8 (gère utf-8, utf_8, utf-8-sig,
    cp65001… via `codecs.lookup` plutôt qu'une comparaison de chaîne fragile)."""
    try:
        return codecs.lookup(encoding).name == "utf-8"
    except (LookupError, TypeError):
        return False


def _force_utf8_stdio() -> None:
    """Force stdout/stderr en UTF-8 — sinon `--help` crash sur console cp1252
    Windows (UnicodeEncodeError sur les accents français / flèches). Idempotent.

    On reconfigure stdout/stderr (pas stdin : pas d'input interactif au stub).
    `except` large : `reconfigure` peut lever `OSError`/`io.UnsupportedOperation`
    si le flux sous-jacent est fermé ou non reconfigurable (redirection vers un
    fd fermé, wrapper personnalisé) — on préfère ne jamais crasher au démarrage.
    """
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", "") or ""
        if not _is_utf8(encoding):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                try:
                    reconfigure(encoding="utf-8", errors="replace")
                except (AttributeError, ValueError, OSError, io.UnsupportedOperation):
                    pass


def _build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI. STUB — les sous-commandes sont des placeholders."""
    parser = argparse.ArgumentParser(
        prog="prospection-b2b",
        description=(
            "Agent IA de prospection B2B générique — scrape, enrichit, score "
            "(règles + Claude + embeddings Qdrant) et génère une file d'appel "
            "triée selon l'ICP du client (configuré en base)."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    # --- run : lancement d'une campagne (détail dans #29) ---
    p_run = sub.add_parser("run", help="Lance une campagne de prospection pour un client.")
    p_run.add_argument("--client-id", required=False, help="UUID du client (icp_profiles).")
    p_run.add_argument("--depts", help="Départements cibles, ex. 75,92 (ex. --dry-run).")
    p_run.add_argument("--limit", type=int, default=50, help="Nombre max de prospects.")
    p_run.add_argument("--dry-run", action="store_true", help="Sans écriture en base ni appel.")

    # --- init-icp : bootstrap ICP d'un client (#12) — --client-id obligatoire ---
    p_icp = sub.add_parser("init-icp", help="Génère l'embedding ICP d'un client → Qdrant (#12).")
    p_icp.add_argument("--client-id", required=True, help="UUID du client (icp_profiles).")

    # --- smoke : vérifie que la stack répond ---
    sub.add_parser("smoke", help="Vérifie que la stack (PG, Qdrant, Ollama) répond.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point CLI. STUB — orchestration réelle dans #29."""
    _force_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)

    # `sub.required=True` → argparse impose une sous-commande. Si `argv` est vide
    # (ex. `python main.py` sans argument), `parse_args` imprime l'usage et sort
    # avec code 2 lui-même ; on n'arrive donc jamais ici sans `args.command`.

    # TODO(#29): dispatcher vers graph/workflow.run() (issue #28).
    # Les imports des modules métier sont faits en lazy ici pour garder
    # `main.py --help` fonctionnel tant que les stubs ne sont pas implémentés.
    print(
        f"[stub] Commande '{args.command}' non implémentée (voir issue #29).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())