#!/bin/sh
# =============================================================================
# docker/ollama/entrypoint.sh — Pull idempotent du modèle d'embedding (issue #8)
# =============================================================================
# Démarre d'abord le serveur Ollama (le CLI `ollama pull` requiert que le
# serveur tourne), attend qu'il soit prêt, puis télécharge le modèle de façon
# idempotente (ollama pull ne retélécharge pas un modèle déjà présent).
#
# Le nom du modèle est configurable via OLLAMA_EMBED_MODEL (défaut .env).
# =============================================================================

set -e

MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

# 1) Démarrer le serveur en arrière-plan
echo "[ollama-entrypoint] Démarrage du serveur Ollama..."
ollama serve &
SERVER_PID=$!

# 2) Attendre que le serveur réponde (max ~60s)
echo "[ollama-entrypoint] Attente de la disponibilité du serveur..."
READY=0
for i in $(seq 1 60); do
  if ollama list >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" -ne 1 ]; then
  echo "[ollama-entrypoint] ⚠️ Serveur Ollama non répondant après 60s."
fi

# 3) Pull idempotent du modèle (3 tentatives, backoff 5s)
attempt=1
MAX_ATTEMPTS=3
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  echo "[ollama-entrypoint] Pull du modèle ${MODEL} (tentative ${attempt}/${MAX_ATTEMPTS})..."
  if ollama pull "${MODEL}"; then
    echo "[ollama-entrypoint] ✅ Modèle ${MODEL} disponible."
    break
  fi
  echo "[ollama-entrypoint] ⚠️ Pull échoué (tentative ${attempt})."
  attempt=$((attempt + 1))
  sleep 5
done

if ! ollama list 2>/dev/null | grep -q "${MODEL}"; then
  echo "[ollama-entrypoint] ⚠️ Modèle ${MODEL} absent — le serveur reste actif."
  echo "[ollama-entrypoint]    Relancer plus tard : docker compose exec ollama ollama pull ${MODEL}"
fi

echo "[ollama-entrypoint] Serveur Ollama prêt (PID ${SERVER_PID})."
# Garder le conteneur vivant tant que le serveur tourne
wait "${SERVER_PID}"