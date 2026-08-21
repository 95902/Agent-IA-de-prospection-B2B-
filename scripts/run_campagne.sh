#!/usr/bin/env bash
# Wrapper cron production — lance une campagne de prospection (#34).
#
# Pilote la vraie CLI (#29) : `main.py --campagne-id <uuid>`. La campagne doit
# exister en base (client + criteres_ciblage + icp_profiles + campagnes) et son
# ICP être embarqué dans Qdrant (scripts/init_icp.py) — voir docs/DEPLOY.md.
#
# Usage : ./scripts/run_campagne.sh <campagne-id> [limit]
#   <campagne-id>  UUID d'une campagne existante (pas un client-id).
#   [limit]        plafond de prospects collectés (défaut : 500, cf. #35).
#
# IMPORTANT (CLAUDE.md) : .gitattributes force LF sur *.sh. Ne pas introduire de
# CRLF — ça casse /bin/sh dans les containers Linux (boucle de redémarrage Ollama).
set -euo pipefail

CAMPAGNE_ID="${1:?Usage: $0 <campagne-id> [limit]}"
LIMIT="${2:-500}"

# Racine du repo (le script peut être appelé depuis n'importe quel cwd, ex. cron).
cd "$(dirname "$0")/.."

# Python : venv si présent (VPS : `python3 -m venv .venv && .venv/bin/pip install -r
# requirements.txt`), sinon le python système (doit avoir les deps). Surchargeable
# via $PYTHON.
PY="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PY=.venv/bin/python

exec env PYTHONPATH=. PYTHONIOENCODING=utf-8 \
  "$PY" main.py --campagne-id "$CAMPAGNE_ID" --limit "$LIMIT"
