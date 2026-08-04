"""init_icp — génère l'embedding ICP d'un client → Qdrant (issue #12).

Issue #11 — STUB. Implémentation détaillée portée par #12.

Usage (CLAUDE.md) :
    python scripts/init_icp.py --client-id <uuid>

L'ICP est lu depuis `criteres_ciblage` / `icp_profiles` en base (règle #3,
aucune valeur codée en dur). L'embedding est produit par Ollama
nomic-embed-text (utils/embeddings.py, règle #5) puis stocké dans Qdrant
(collection `icp_profiles`, utils/db.py).
"""
from __future__ import annotations

import argparse


def main() -> int:
    """STUB — génère et stocke l'embedding ICP d'un client. À implémenter (#12)."""
    parser = argparse.ArgumentParser(description="Génère l'embedding ICP d'un client → Qdrant (issue #12).")
    parser.add_argument("--client-id", required=True, help="UUID du client.")
    parser.parse_args()
    raise NotImplementedError("scripts/init_icp non implémenté — voir #12.")


if __name__ == "__main__":
    raise SystemExit(main())