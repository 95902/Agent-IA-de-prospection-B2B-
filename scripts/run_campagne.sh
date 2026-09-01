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

# Garde-fou préflight : refuse de démarrer si une API payante est cassée — p.ex. une
# clé Anthropic expirée fait basculer TOUT le scoring en repli règles-only *sans erreur
# pipeline* (« 0 erreur » ≠ « a marché »). Sonde Anthropic + Tavily + INSEE.
# Court-circuit exceptionnel : PREFLIGHT_SKIP=1 ./scripts/run_campagne.sh ...
if [ "${PREFLIGHT_SKIP:-0}" != "1" ]; then
  if ! env PYTHONPATH=. "$PY" scripts/preflight.py; then
    echo "[run_campagne] PRÉFLIGHT ÉCHOUÉ — run annulé. Corrige la/les clé(s) .env, ou PREFLIGHT_SKIP=1 pour forcer." >&2
    exit 1
  fi
fi

exec env PYTHONPATH=. PYTHONIOENCODING=utf-8 \
  "$PY" main.py --campagne-id "$CAMPAGNE_ID" --limit "$LIMIT"
