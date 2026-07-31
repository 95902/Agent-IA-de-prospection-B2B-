# #6 — Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/6
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `infrastructure`, `docker`, `sprint-1`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 3 pts
**Labels :** infrastructure, docker, sprint-1

## Objectif
Fournir la stack Docker complète (PostgreSQL + Qdrant + Ollama) qui sert de socle à tout le reste du projet, en dev comme en prod.

## Fichiers à créer
- [ ] `docker-compose.yml` — services `postgres` (postgres:16-alpine, :5432), `qdrant` (qdrant/qdrant:latest, :6333/:6334), `ollama` (ollama/ollama:latest, :11434), `pgadmin` (profil `dev`), `metabase` (profil `monitoring`, voir #37)
- [ ] `docker-compose.prod.yml` — override qui lie les ports Postgres/Qdrant à `127.0.0.1` uniquement (sécurité VPS, voir #33)
- [ ] `docker/qdrant/config.yaml` — HNSW `m=16`, `ef_construct=100`, API key, niveau de log
- [ ] `.env.example` — toutes les variables listées dans `docs/ARCHITECTURE.md` (Postgres, Qdrant, Claude, LangSmith, INSEE, Tavily, Bloctel, Dropcontact)
- [ ] `Makefile` — cibles `dev`, `prod`, `stop`, `psql`, `logs`, `backup`, `reset-db`

## Contraintes
- Volumes persistants pour Postgres, Qdrant et les modèles Ollama (ne pas perdre les données entre `docker compose down`/`up`)
- Aucun secret réel dans `docker-compose.yml` — tout passe par `.env` (non versionné) et `.env.example` (versionné, sans valeurs)

## Critères d'acceptance
- [ ] `make dev` démarre tous les services sans erreur
- [ ] `curl localhost:6333/healthz` → OK
- [ ] `curl localhost:11434` → « Ollama is running »
- [ ] `make prod` (avec l'override) n'expose pas les ports 5432/6333 en dehors de `127.0.0.1`


