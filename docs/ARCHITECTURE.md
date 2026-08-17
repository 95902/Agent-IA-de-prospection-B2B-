# ARCHITECTURE.md — Stack technique & Infrastructure (multi-secteurs)

> La BDD ci-dessous est déjà générique par construction : `criteres_ciblage`
> stocke l'ICP de chaque client (codes NAF, effectif, ancienneté, zone,
> mots-clés positifs/négatifs). Aucune table ni script ne doit coder en dur
> un secteur, un code NAF ou une liste de marques.

## Stack complète

```
┌─────────────────────────────────────────────┐
│  VPS CPU OVH — Docker self-hosted           │
│                                             │
│  ┌──────────┐  ┌────────┐  ┌────────────┐  │
│  │PostgreSQL│  │ Qdrant │  │   Ollama   │  │
│  │   16     │  │        │  │  (CPU)     │  │
│  │  :5432   │  │ :6333  │  │  :11434    │  │
│  └──────────┘  └────────┘  └────────────┘  │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  Pipeline Python (LangChain)           │ │
│  │  agents/ + graph/ + utils/             │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │ API calls
         ▼
┌─────────────────────────────────────────────┐
│  APIs Cloud                                 │
│  Claude API (scoring LLM — modèle configurable, config/settings.py) │
│  Sirene INSEE (collecte)                   │
│  Tavily (enrichissement)                   │
│  Dropcontact (emails B2B)                  │
└─────────────────────────────────────────────┘
```

## Arborescence projet

```
Agent-IA-de-prospection-B2B-/
├── CLAUDE.md
├── main.py                     # CLI argparse — point d'entrée
├── requirements.txt
├── .env.example
├── Makefile
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md         # Ce fichier
│   ├── SCORING.md
│   ├── ISSUES.md
│   └── LEGAL.md
├── config/
│   ├── settings.py             # Pydantic Settings depuis .env (modèle Claude, clés API — jamais l'ICP)
│   └── icp_seed_example.py     # Exemple illustratif pour bootstrap d'un nouveau client — pas une valeur par défaut utilisée en prod
├── agents/
│   ├── sirene_agent.py         # Node LangChain : collecte INSEE
│   ├── enrichissement_agent.py # Node : Tavily + Crawl4AI + DDG
│   ├── nettoyage_agent.py      # Node : dédup + filtres
│   └── scoring_agent.py        # Node : 3 couches scoring hybride
├── graph/
│   ├── workflow.py             # Graphe LangChain complet (6 nodes)
│   └── state.py                # EtatAgent TypedDict
├── models/
│   ├── prospect.py             # Pydantic v2 + validators E.164/SIRET
│   └── score.py                # ScoreResult BaseModel
├── utils/
│   ├── db.py                   # asyncpg pool + AsyncQdrantClient
│   ├── embeddings.py           # Ollama nomic-embed-text v2
│   ├── dropcontact.py          # Enrichissement emails
│   ├── airtable_sync.py        # Sync CRM
│   └── logger.py               # Loguru + LangSmith config
├── prompts/
│   ├── scorer_system.txt.j2    # Template Jinja — rendu depuis l'ICP du client (jamais figé)
│   └── scorer_user.txt.j2      # Template Jinja — données prospect
├── scripts/
│   ├── smoke_test.py           # Vérifie stack au démarrage
│   ├── init_icp.py             # Génère embedding ICP → Qdrant
│   ├── run_campagne.sh         # Wrapper cron production
│   └── rapport_hebdo.py        # Email hebdo métriques Brevo
├── tests/
│   ├── test_models.py          # Validators Pydantic
│   ├── test_sirene.py          # Intégration INSEE (marker: integration)
│   ├── test_scoring.py         # 20 cas + mock Claude
│   └── test_nettoyage.py       # Dédup + filtres
└── docker/
    ├── postgres/init/
    │   └── 01_schema.sql       # Auto-exécuté au 1er démarrage
    └── qdrant/
        └── config.yaml         # HNSW m=16, API key, log level
```

## Base de données PostgreSQL 16

### Tables

```sql
-- Entité racine
clients (
  id UUID PK, nom_entreprise, secteur, produit_vendu,
  zone_intervention, contact_nom, contact_email, contact_telephone,
  statut CHECK ('essai','actif','suspendu'), meta JSONB
)

-- Configuration ciblage par client
criteres_ciblage (
  id UUID PK, client_id FK, nom, description_icp,
  codes_naf TEXT[], departements TEXT[],
  effectif_min, effectif_max, anciennete_min_ans,
  exiger_site_web BOOL, exiger_email BOOL,
  mots_cles_positifs TEXT[], mots_cles_negatifs TEXT[]
)

-- Profils ICP vectorisés
icp_profiles (
  id UUID PK, client_id FK, critere_id FK,
  nom, description TEXT, qdrant_point_id UUID, actif BOOL
)

-- Sources de collecte
sources (
  id UUID PK, nom TEXT UNIQUE,
  type CHECK ('api_officielle','scraping','enrichissement','manuel'),
  url, derniere_collecte, nb_prospects
)
-- Données initiales : sirene_insee, tavily, pages_jaunes, dropcontact, manuel

-- Campagnes de prospection
campagnes (
  id UUID PK, client_id FK, critere_id FK, icp_profile_id FK,
  nom, statut CHECK ('brouillon','en_cours','terminee','annulee'),
  date_lancement, max_prospects,
  prospects_collectes, prospects_qualifies, appels_passes, rdv_obtenus,
  config_scoring JSONB  -- poids des 3 couches
)

-- Prospects collectés
prospects (
  id UUID PK, campagne_id FK, source_id FK,
  siret VARCHAR(14) UNIQUE, siren VARCHAR(9),
  nom_entreprise, nom_dirigeant, code_naf, libelle_naf,
  telephone, telephone_2, email, site_web,
  adresse, code_postal, ville, departement, latitude, longitude,
  effectif, date_creation, chiffre_affaire,
  score_final INT [0-100], score_regles INT, score_llm INT, score_embedding FLOAT,
  statut CHECK ('nouveau','qualifie','en_attente_appel','appele','rdv','refus','absent','invalide'),
  doublon BOOL, qdrant_point_id UUID,
  notes, raw_data JSONB
)

-- Historique des scorings
scores (
  id UUID PK, scored_at, prospect_id FK,
  score_regles, score_llm, score_embedding, score_final,
  justification_llm TEXT, prompt_version TEXT, details JSONB
)

-- Appels (Phase 2 vocal)
appels (
  id UUID PK, prospect_id FK, date_appel, duree_secondes,
  statut CHECK ('planifie','en_cours','termine','echec','absent','rappel'),
  transcript, resume_llm, rdv_pris BOOL, rdv_datetime,
  notes_commercial, metadata JSONB
)
```

### Vue clé — file d'appel

```sql
CREATE VIEW file_appel AS
SELECT p.id, p.nom_entreprise, p.nom_dirigeant,
       p.telephone, p.email, p.ville, p.departement,
       p.code_naf, p.effectif, p.score_final, p.statut,
       c.nom AS campagne_nom
FROM prospects p
JOIN campagnes c ON c.id = p.campagne_id
WHERE p.statut = 'qualifie'
  AND p.telephone IS NOT NULL
  AND p.doublon = FALSE
ORDER BY p.score_final DESC;
```

### Index critiques

```sql
CREATE INDEX idx_prospects_statut   ON prospects(statut);
CREATE INDEX idx_prospects_score    ON prospects(score_final DESC);
CREATE INDEX idx_prospects_dept     ON prospects(departement);
CREATE INDEX idx_prospects_naf      ON prospects(code_naf);
CREATE INDEX idx_prospects_nom_trgm ON prospects USING gin(nom_entreprise gin_trgm_ops);
```

## Qdrant — Collections vectorielles

```python
# Collection prospects
collection_name = "prospects_embeddings"
vectors_config = VectorParams(
    size=768,               # nomic-embed-text v2
    distance=Distance.COSINE
)
# HNSW m=16, ef_construct=100

# Collection ICP (référence)
collection_name = "icp_profiles"
# Même config — 1 seul vecteur par client

# Payload indexé (pour filtrage)
# departement, code_naf, score_final, campagne_id
```

## Ollama — Embeddings locaux CPU

```bash
# Modèles disponibles
nomic-embed-text   # 137MB, 768 dims, Apache 2.0 — RECOMMANDÉ MVP
qwen3-embedding    # 639MB, 1024 dims, #1 MTEB multilingue — alt.

# API
POST http://localhost:11434/api/embed
{"model": "nomic-embed-text", "input": "texte à vectoriser"}

# Temps de réponse : < 500ms sur CPU OVH
# Coût : 0€
```

## Variables d'environnement (.env)

```bash
# PostgreSQL
POSTGRES_DB=prospection_b2b
POSTGRES_USER=scraper
POSTGRES_PASSWORD=changeme_postgres
POSTGRES_HOST=localhost        # 'postgres' depuis un container Docker
POSTGRES_PORT=5432

# Qdrant
QDRANT_API_KEY=changeme_qdrant
QDRANT_HOST=localhost          # 'qdrant' depuis un container Docker
QDRANT_PORT=6333

# LLM & Observabilité
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=prospection-b2b

# APIs collecte
INSEE_API_KEY=...              # portail-api.insee.fr — header X-INSEE-Api-Key-Integration, base api-sirene/3.11, 30 req/min
TAVILY_API_KEY=tvly-...        # 1000 req/mois gratuit
DROPCONTACT_API_KEY=...        # 24€/mois

# Paramètres campagne — valeurs d'EXEMPLE uniquement.
# En production, ces critères viennent de la table criteres_ciblage du
# client/de la campagne (voir models/prospect.py + graph/state.py), pas
# de variables d'environnement globales. Ces defaults ne servent qu'aux
# runs --dry-run en local sans client configuré.
TARGET_DEPTS=75,92,93,94
TARGET_NAF=4520Z,4511Z,4531Z,4532Z
MAX_PROSPECTS=500
```

## Docker Compose — services

```yaml
services:
  postgres:   image: postgres:16-alpine, port: 5432
  qdrant:     image: qdrant/qdrant:latest, ports: 6333/6334
  ollama:     image: ollama/ollama:latest, port: 11434
  pgadmin:    image: dpage/pgadmin4, port: 5050, profile: dev
  metabase:   image: metabase/metabase, port: 3000, profile: monitoring

# Prod override (docker-compose.prod.yml)
# Ports liés à 127.0.0.1 uniquement (sécurité VPS)
```

## Makefile — commandes

```bash
make dev        # Lance stack dev (avec pgAdmin + Qdrant UI)
make prod       # Lance stack prod (ports fermés)
make stop       # Arrête tous les containers
make psql       # Shell PostgreSQL interactif
make logs       # Logs en temps réel
make backup     # Dump PostgreSQL → backups/
make reset-db   # ⚠️ Supprime toutes les données (confirmation requise)
```
