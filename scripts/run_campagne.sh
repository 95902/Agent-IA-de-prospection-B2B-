#!/usr/bin/env bash
# Wrapper cron production — lance une campagne de prospection (issue #11 STUB).
# Implémentation détaillée portée par une issue dédiée (#29/#33).
#
# Usage : ./scripts/run_campagne.sh <client-id> [depts] [limit]
#
# IMPORTANT (CLAUDE.md) : .gitattributes force LF sur *.sh. Ne pas introduire de
# CRLF — ça casse les entrypoints Docker (crash en boucle du container Ollama).
set -euo pipefail

CLIENT_ID="${1:?Usage: $0 <client-id> [depts] [limit]}"
DEPTS="${2:-75,92}"
LIMIT="${3:-50}"

# TODO(issue dédiée) : python main.py run --client-id "$CLIENT_ID" --depts "$DEPTS" --limit "$LIMIT"
echo "[stub] run_campagne non implémenté — client=$CLIENT_ID depts=$DEPTS limit=$LIMIT" >&2
exit 2