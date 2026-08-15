# CLAUDE.md — Agent IA de Prospection B2B (multi-secteurs)

> Fichier maître lu automatiquement par Claude Code au démarrage.
> Pour les détails, charge le fichier spécialisé correspondant à ta tâche.

## Projet en une phrase

Agent IA générique qui scrape des entreprises (Sirene INSEE) selon le profil client idéal (ICP) défini par chaque client — quel que soit son secteur cible —, les enrichit (Tavily + Crawl4AI), les score via un système hybride (règles + Claude + embeddings Qdrant), et génère une file d'appel triée pour n'importe quel client B2B (courtier, éditeur SaaS, agence, cabinet de recrutement, etc.).

**Le produit n'est spécifique à aucun secteur.** Chaque client configure son propre ICP (codes NAF, effectif, ancienneté, zone géographique, mots-clés positifs/négatifs) via `criteres_ciblage` en base — aucune valeur métier ne doit être codée en dur dans l'agent.

## État réel du repo & pièges (MAJ 2026-08-02)

Sprint 1 en cours. Sur `main` : docker-compose (#6), schéma SQL (#7), front
React/Vite. Le back Python arrive (embeddings #8 + `utils/db.py` #9 en revue).
L'arborescence Python complète (#11) et le pipeline (`main.py`) n'existent pas
encore. Les « Commandes du quotidien » plus bas sont la **cible**, pas l'état actuel.

**Monorepo** : le front (React/Vite/shadcn) ET le back Python vivent à la
**racine** — `config/`, `utils/`, `docker/` cohabitent avec `src/`, `package.json`.

Pièges connus (drift docs ↔ réalité — vérifier avant de coder) :
- **Numérotation des issues** : `docs/ISSUES.md` numérote le Sprint 0 en `#S0-x` ;
  sur GitHub ce sont les issues #1–5, donc **tout est décalé de +5**. Ex. : « #5
  Pydantic » dans la doc = issue GitHub **#10**. Toujours mapper avant de citer.
- **11 tables, pas 8** : le schéma ajoute `bloctel_verifications`,
  `oppositions_rgpd`, `purge_rgpd_log` aux 8 documentées.
- **INSEE** : nouveau portail `api-sirene/3.11` + header
  `X-INSEE-Api-Key-Integration` (et non l'ancien `entreprises/sirene/V3.11` + OAuth2).
- **Fins de ligne** : `.gitattributes` force LF sur `*.sh`. Ne pas réintroduire de
  CRLF — ça casse les entrypoints Docker (crash en boucle du container Ollama).
- **Qdrant** : `qdrant-client` doit suivre la version du serveur du docker
  (~1.15.x). Créer les **index payload** à la création des collections, sinon le
  filtrage (`departement`, `code_naf`) fait un scan séquentiel lent.

**Lancer la stack en local** : `docker compose --profile dev up -d` (pas de `make`
garanti sous Windows). Tests d'intégration marqués `@pytest.mark.integration`
(tapent de vraies APIs) — exclus des runs par défaut.

## Repo & équipe

```
Repo    : 95902/Agent-IA-de-prospection-B2B-
Équipe  : 3 personnes
Sprints : 2 semaines × 5 sprints (Sprint 0 à Sprint 4)
Durée   : 9 semaines MVP
```

## Navigation dans les docs

| Tu veux coder... | Lis ce fichier |
|---|---|
| L'architecture globale, la BDD, Docker, les APIs | `docs/ARCHITECTURE.md` |
| Le scoring hybride, les prompts Claude (générés dynamiquement depuis l'ICP client), les embeddings | `docs/SCORING.md` |
| Une issue spécifique (Sprint 0 à Sprint 4, 41 issues au total sur GitHub) | `docs/ISSUES.md` |
| Les règles légales (opposition commerciale R123-232, RGPD, loi 2025-594) | `docs/LEGAL.md` |
| Le produit, les user stories, les KPIs | `docs/PRD.md` |

## Règles absolues — ne jamais ignorer

1. **Opposition commerciale OBLIGATOIRE** (art. R123-232 c. com.) avant tout enrichissement tiers ou file de contact — `utils/opposition_commerciale.py::peut_etre_contacte()`, **fermé par défaut**. ⚠️ **Bloctel a été supprimé** par la loi n° 2025-594 au **11 août 2026** (opt-in B2C, intérêt légitime B2B inchangé) : ne plus fonder aucune logique d'appel dessus. L'appel = Phase 2 (V1 email-first). Lire `docs/LEGAL.md`.
2. **Sources légales uniquement** : Sirene INSEE, Tavily, Pappers. Zéro scraping illégal.
3. **Aucun ICP codé en dur** : codes NAF, tranche d'effectif, ancienneté, zone géographique, mots-clés positifs/négatifs viennent tous de `criteres_ciblage` / `icp_profiles` en base, jamais de constantes Python. Un client = un ICP = une configuration.
4. **Exclusions configurables par client** (`criteres_ciblage.mots_cles_negatifs`) — jamais de liste de marques/groupes codée en dur. Un prospect qui matche une exclusion → score = 0 automatiquement.
5. **Embeddings locaux sur CPU** : Ollama + `nomic-embed-text` (tag Ollama = v1.5, ~274 MB au téléchargement / 137M paramètres, 768 dims). Pas d'API OpenAI pour ça. Modèle configurable via `OLLAMA_EMBED_MODEL`.
6. **LLM scorer en cloud** : Claude API uniquement (CPU OVH trop lent pour inférence locale). Voir `docs/SCORING.md` pour le choix de modèle et le prompt caching.
7. **Pydantic v2 partout** : tous les modèles de données passent par Pydantic avec validators.
8. **Async partout** : asyncpg pour Postgres, AsyncQdrantClient pour Qdrant, httpx pour HTTP.
9. **RGPD** : purge automatique des données selon la politique de rétention (voir `docs/LEGAL.md`) — job récurrent, pas une tâche manuelle.

## Stack en 30 secondes

```
Python 3.12 + LangChain + Pydantic v2
PostgreSQL 16 (Docker) + Qdrant (Docker) + Ollama CPU (Docker)
Claude API (scoring LLM — modèle configuré dans config/settings.py, jamais codé en dur dans les prompts)
Sirene INSEE + Tavily + Crawl4AI + Bloctel + Dropcontact
VPS CPU OVH — tout self-hosted
```

## Commandes du quotidien

```bash
make dev                    # Démarre Postgres + Qdrant + Ollama + pgAdmin
python scripts/smoke_test.py  # Vérifie que tout répond
python scripts/init_icp.py --client-id <uuid>  # Génère l'embedding ICP d'un client → Qdrant
python main.py --client-id <uuid> --depts 75,92 --limit 50 --dry-run
pytest tests/ -v
```

## Coût mensuel MVP (par client actif) : ~125-140€

Dropcontact ~79€ + Tavily 20€ + Claude API ~10€ + VPS OVH ~15-30€
(Bloctel supprimé — loi 2025-594. La chaîne A OSM/Pappers est **gratuite** et
réduit ce coût quand elle suffit : viser Dropcontact en dernier recours.)

@agents.md
