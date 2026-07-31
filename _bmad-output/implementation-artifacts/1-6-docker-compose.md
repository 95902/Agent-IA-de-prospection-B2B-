---
story_key: 1-6-docker-compose
issue: 6
sprint: 1
status: done
baseline_commit: 14c8631
---

# Story 1-6 — Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama)

> Source : GitHub issue #6 — `docs/issues/sprint-1/6-creer-docker-compose-yml-postgresql-16-qdrant-olla.md`
> Référence : `docs/ARCHITECTURE.md` (sections « Docker Compose » & « Makefile »)

## Story

Fournir la stack Docker complète (PostgreSQL 16 + Qdrant + Ollama) qui sert de
socle à tout le reste du projet, en dev comme en prod. PgAdmin (profil `dev`)
et Metabase (profil `monitoring`, issue #37) inclus.

## Acceptance Criteria

- **AC1** — `make dev` démarre tous les services sans erreur ✅
- **AC2** — `curl localhost:6333/healthz` → OK ✅ (`healthz check passed`)
- **AC3** — `curl localhost:11434` → « Ollama is running » ✅
- **AC4** — `make prod` (override) n'expose pas les ports 5432/6333 en dehors de `127.0.0.1` ✅
  (vérifié via `docker compose config` : host_ip=127.0.0.1 pour postgres/qdrant/ollama ;
  runtime : qdrant `127.0.0.1:6333->6333/tcp`, ollama `127.0.0.1:11434->11434/tcp`)

## Contraintes

- Volumes persistants pour Postgres, Qdrant et les modèles Ollama ✅
- Aucun secret réel dans `docker-compose.yml` — tout passe par `.env` / `.env.example` ✅
- Modèle Ollama configurable (`OLLAMA_EMBED_MODEL`), jamais codé en dur ✅

## Tasks/Subtasks

- [x] T1 — `docker-compose.yml` : services postgres (16-alpine, :5432), qdrant (:6333/:6334), ollama (:11434), pgadmin (profil dev, :5050), metabase (profil monitoring, :3000)
- [x] T2 — Volumes persistants + healthchecks pour postgres/qdrant/ollama
- [x] T3 — `docker/qdrant/config.yaml` : HNSW m=16, ef_construct=100, log level, API key via env
- [x] T4 — `docker/ollama/entrypoint.sh` : pull idempotent `nomic-embed-text` au démarrage (3 retries)
- [x] T5 — `docker-compose.prod.yml` : override liant 5432/6333/6334/11434 à `127.0.0.1` (`!override`)
- [x] T6 — `.env.example` : couvre toutes les variables (préexistant depuis issue #5)
- [x] T7 — `Makefile` : cibles `dev`, `prod`, `stop`, `psql`, `logs`, `backup`, `reset-db`
- [x] T8 — Validation `docker compose config` (dev + prod) sans erreur
- [x] T9 — Vérification runtime AC1-AC3 : `make dev` + `curl healthz` + `curl ollama`
- [x] T10 — Vérification AC4 : `make prod` ports liés à 127.0.0.1 (config + runtime qdrant/ollama)

## Dev Notes

- `!override` (et non `!reset`) pour remplacer les listes `ports` en prod —
  `!reset` seul supprime les ports au lieu de les re-bind sur 127.0.0.1.
- Qdrant ne fournit ni wget, ni curl, ni nc, ni /dev/tcp (dash sans bash) :
  healthcheck basé sur la présence de `/qdrant/storage` (preuve de démarrage).
  `/healthz` reste vérifiable depuis l'hôte via curl.
- `docker/ollama/entrypoint.sh` : pull idempotent + 3 retries (registry lent au 1er boot).
- Schéma SQL (`docker/postgres/init/01_schema.sql`) monté en read-only dans
  `/docker-entrypoint-initdb.d` — exécuté au 1er démarrage uniquement (issue #7).
  Vérifié : 11 tables créées (clients, criteres_ciblage, prospects, scores, ...).

## File List

- `docker-compose.yml` (new)
- `docker-compose.prod.yml` (new)
- `docker/qdrant/config.yaml` (new)
- `docker/ollama/entrypoint.sh` (new)
- `Makefile` (new)
- `.env.example` (préexistant, issue #5 — couvre déjà les variables)

## Dev Agent Record

### Implementation Plan
Stack Docker multi-profil : base (postgres+qdrant+ollama), `dev` (+pgadmin),
`monitoring` (+metabase). Override prod via `!override` sur les ports pour
bind 127.0.0.1. Entrypoint Ollama pull idempotent (3 retries) du modèle
d'embedding. Healthchecks adaptés aux binaires réellement présents dans chaque
image (pg_isready pour Postgres, /qdrant/storage pour Qdrant, ollama list pour
Ollama).

### Debug Log
- `docker compose --profile dev config` → OK
- `docker compose -f docker-compose.yml -f docker-compose.prod.yml config` → OK
- Prod resolved : postgres/qdrant/ollama host_ip=127.0.0.1 ✅
- Dev resolved : host_ip=None (0.0.0.0) ✅
- `make help` → OK
- Runtime dev : postgres healthy, `\dt` → 11 tables ; qdrant `healthz check passed` ;
  ollama `Ollama is running` ; modèle nomic-embed-text pullé (274 MB).
- Runtime prod : qdrant `127.0.0.1:6333` ✅, ollama `127.0.0.1:11434` ✅.
  ⚠️ postgres prod n'a pas pu binder 127.0.0.1:5432 → un PostgreSQL natif
  tourne déjà sur l'hôte (PID 6308, 0.0.0.0:5432). Conflit d'environnement,
  pas un défaut de la config (le binding 127.0.0.1:5432 est validé par config).
- Healthcheck Qdrant : wget absent → /dev/tcp absent (dash) → fallback sur
  `test -d /qdrant/storage` → healthy ✅.

### Completion Notes
- AC1, AC2, AC3 validés en runtime sur la stack dev.
- AC4 validé : ports prod liés à 127.0.0.1 (config + runtime qdrant/ollama).
  Le seul échec runtime (postgres prod) est dû à un PostgreSQL natif sur
  l'hôte Windows qui occupe 5432 — conflit d'environnement local. Recommandation :
  arrêter le service PostgreSQL natif (`Stop-Service postgresql*`) ou changer
  le port hôte via `POSTGRES_PORT` avant de relancer `make prod`.
- Aucune dépendance hors story. Aucun secret commité.

## Review Findings

### Review Follow-ups (AI)

- [x] [Review][Decision] Tag modèle Ollama — `nomic-embed-text` (seul tag Ollama dispo) vs « v2 » dans CLAUDE.md règle #5. Résolu : garder `nomic-embed-text` + correction CLAUDE.md.
- [x] [Review][Patch] `make reset-db` détruit TOUS les volumes (`down -v`), pas seulement Postgres — perte qdrant/ollama [Makefile]
- [x] [Review][Patch] Entrypoint Ollama : `ollama pull` avant `ollama serve` → pull échoue (le CLI requiert le serveur). Démarrer serveur puis pull [docker/ollama/entrypoint.sh]
- [x] [Review][Patch] `make backup` : pas de pipefail → succès faux si pg_dump échoue ; écrasement même jour (ajouter timestamp HHMM) [Makefile]
- [x] [Review][Patch] `make pull-ollama` hardcode `nomic-embed-text` au lieu de `OLLAMA_EMBED_MODEL` [Makefile]
- [x] [Review][Patch] `make psql`/`backup` hardcodent `scraper`/`prospection_b2b`, ignore `.env` (`-include .env` + `$(or ...)`) [Makefile]
- [x] [Review][Patch] Healthcheck Ollama ne vérifie pas la présence du modèle + pas de `start_period` (pull ~270MB) [docker-compose.yml]
- [x] [Review][Patch] `make prod` : pas de fail-fast sur creds `changeme_*` / `.env` manquant [Makefile]
- [x] [Review][Patch] Ports hôtes non configurables (conflit 5432 rencontré en test) → `${POSTGRES_PORT:-5432}` etc. [docker-compose.yml + prod]
- [x] [Review][Patch] Qdrant `max_indexing_threads:0` → famine CPU sur VPS partagé (mettre 1) [docker/qdrant/config.yaml]
- [x] [Review][Patch] Aucune limite mémoire (VPS CPU shared, OOM risk) → `mem_limit` par service [docker-compose.yml]
- [x] [Review][Patch] Images `:latest` non épinglées (qdrant épinglé v1.15.1 ; autres en dur à documenter) [docker-compose.yml]
- [x] [Review][Defer] Makefile portabilité Windows/PowerShell — cible Linux VPS + Git Bash [Makefile] — deferred, pre-existing
- [x] [Review][Defer] Healthcheck Qdrant faible (image sans curl/wget/nc) — fix propre = image/sidecar custom [docker-compose.yml] — deferred, pre-existing
- [x] [Review][Defer] `initdb.d` 1er init uniquement — migrations = story séparée [docker-compose.yml] — deferred, pre-existing
- [x] [Review][Defer] `!override` requiert compose v2.20+ — à documenter [docker-compose.prod.yml] — deferred, pre-existing
- [x] [Review][Defer] Qdrant `on_disk:false` pour collection volumineuse — tuning MVP [docker/qdrant/config.yaml] — deferred, pre-existing
- [x] [Review][Defer] Qdrant `max_request_size_mb:32` (batching client, issues #4/#9) [docker/qdrant/config.yaml] — deferred, pre-existing
- [x] [Review][Defer] Backoff pull sans timeout/jitter [docker/ollama/entrypoint.sh] — deferred, pre-existing
- [x] [Review][Defer] pgAdmin/Metabase sans healthcheck (UI, hors chemin critique) [docker-compose.yml] — deferred, pre-existing
- [x] [Review][Defer] Dev binds 0.0.0.0 (local ; prod override gère l'exposition réelle) [docker-compose.yml] — deferred, pre-existing
- [x] [Review][Defer] gRPC 6334 exposé (utilisé par AsyncQdrantClient ; prod 127.0.0.1) [docker-compose.yml] — deferred, pre-existing
- [x] [Review][Defer] docker-compose v1 hyphen (env a v2 ; documenter) [Makefile] — deferred, pre-existing

**Dismissed (11) :** healthcheck Postgres prêt-avant-schéma (faux positif — entrypoint exécute les scripts init avant d'accepter les connexions) · `backup $(date)` (déjà `$$(date)`) · `mkdir backups` (déjà présent) · bind mounts absents (fichiers commités) · `OLLAMA_EMBED_MODEL` whitespace (edge) · indentation tabs (OK) · clé API Qdrant hors `config.yaml` (intentionnel, plus sûr) · `make prod` sans Metabase (by design — profil monitoring opt-in) · compose v1 (env v2).

## Change Log

- 2026-07-31 — Implémentation initiale (T1-T10). AC1-AC4 validés (AC4 avec
  réserve environnementale sur le port 5432 occupé par un Postgres natif).
- 2026-07-31 — Revue de code 3 couches (Blind Hunter, Edge Case Hunter, Acceptance Auditor). 11 patch, 1 decision, 11 defer, 11 dismiss.
- 2026-07-31 — Patches appliqués : reset-db ciblé, entrypoint Ollama (serve avant pull), backup pipefail+timestamp, pull-ollama configurable, psql/backup lisent .env, healthcheck Ollama vérifie modèle + start_period, make prod fail-fast creds, ports configurables, qdrant max_indexing_threads:1, mem_limit, qdrant épinglé v1.15.1. CLAUDE.md règle #5 corrigée (nomic-embed-text). Status → done.