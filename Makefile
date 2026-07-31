# =============================================================================
# Makefile — Commandes du quotidien (issue #6)
# Agent IA de Prospection B2B (multi-secteurs)
# =============================================================================
# Voir docs/ARCHITECTURE.md (section « Makefile — commandes »).
# Cible : Linux VPS OVH + Git Bash en local. Requiert Docker + Compose v2.20+
# et un fichier .env à la racine (cp .env.example .env puis renseigner clés).
# =============================================================================

# Shell explicite : recipes utilisent des builtins bash (read -p, pipefail)
SHELL := /bin/bash

# Charger .env s'il existe (Make lit KEY=value comme variables make).
# Ignore-missing si .env absent (fresh checkout -> defaults ci-dessous).
-include .env

# Compose de base + override prod
COMPOSE      = docker compose
COMPOSE_DEV  = $(COMPOSE) --profile dev
COMPOSE_PROD = $(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml

# PG_USER / PG_DB lus depuis .env (POSTGRES_USER / POSTGRES_DB) avec fallback.
PG_USER      = $(or $(POSTGRES_USER),scraper)
PG_DB        = $(or $(POSTGRES_DB),prospection_b2b)
BACKUP_DIR   := backups

# Volume Postgres nommé explicitement (cible précise pour reset-db).
PG_VOLUME    = prospection_b2b_postgres_data

.DEFAULT_GOAL := help

.PHONY: help dev prod stop psql logs backup reset-db pull-ollama smoke status

## help — Afficher cette aide
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //' | column -t -s '—'

## dev — Démarrer la stack dev (postgres + qdrant + ollama + pgAdmin)
dev:
	$(COMPOSE_DEV) up -d
	@echo "\n✅ Stack dev démarrée. pgAdmin → http://localhost:$${PGADMIN_PORT:-5050}"

## prod — Démarrer la stack prod (ports liés à 127.0.0.1, override sécurité)
prod:
	@test -f .env || { echo "❌ .env manquant — lancer: cp .env.example .env"; exit 1; }
	@if grep -qE '^POSTGRES_PASSWORD=changeme_postgres$$' .env; then \
		echo "❌ POSTGRES_PASSWORD est encore la valeur par défaut 'changeme' — interdit en prod"; exit 1; \
	fi
	@if grep -qE '^QDRANT_API_KEY=changeme_qdrant$$' .env; then \
		echo "❌ QDRANT_API_KEY est encore la valeur par défaut 'changeme' — interdit en prod"; exit 1; \
	fi
	$(COMPOSE_PROD) up -d
	@echo "\n✅ Stack prod démarrée (ports 5432/6333/11434 liés à 127.0.0.1)"

## stop — Arrêter tous les containers (données conservées dans les volumes)
stop:
	$(COMPOSE) down

## psql — Shell PostgreSQL interactif
psql:
	@$(COMPOSE) exec postgres psql -U $(PG_USER) $(PG_DB)

## logs — Logs en temps réel de tous les services
logs:
	$(COMPOSE) logs -f --tail=100

## pull-ollama — Télécharger le modèle d'embedding configuré (OLLAMA_EMBED_MODEL)
pull-ollama:
	@$(COMPOSE) exec ollama sh -c 'ollama pull "$${OLLAMA_EMBED_MODEL:-nomic-embed-text}"'

## smoke — Vérifier que la stack répond (scripts/smoke_test.py, issue #14)
smoke:
	python scripts/smoke_test.py

## status — État des containers
status:
	$(COMPOSE) ps

## backup — Dump PostgreSQL compressé → backups/YYYYMMDD-HHMM.sql.gz
backup:
	@mkdir -p $(BACKUP_DIR); \
	set -o pipefail; \
	F=$(BACKUP_DIR)/$$(date +%Y%m%d-%H%M).sql.gz; \
	$(COMPOSE) exec -T postgres pg_dump -U $(PG_USER) $(PG_DB) | gzip > $$F \
		&& echo "✅ Backup → $$F" \
		|| { echo "❌ Backup échoué (pg_dump)"; rm -f $$F; exit 1; }

## reset-db — ⚠️ Supprime UNIQUEMENT le volume Postgres (demande confirmation)
reset-db:
	@read -r -p "⚠️ Cela supprimera les données Postgres (uniquement). Taper 'OUI' pour confirmer : " confirm; \
	if [ "$$confirm" = "OUI" ]; then \
		$(COMPOSE) stop postgres; \
		docker volume rm $(PG_VOLUME) || { echo "❌ Volume $(PG_VOLUME) introuvable"; exit 1; }; \
		echo "✅ Volume Postgres supprimé. Relancer 'make dev' pour réinitialiser le schéma."; \
	else \
		echo "Abandon."; \
	fi