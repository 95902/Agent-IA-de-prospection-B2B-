# Agent IA de Prospection B2B (multi-secteurs)

Agent IA générique qui scrape des entreprises (Sirene INSEE) selon le profil
client idéal (ICP) défini par chaque client — quel que soit son secteur
cible —, les enrichit (Tavily + Crawl4AI), les score via un système hybride
(règles + Claude + embeddings Qdrant), et génère une file d'appel triée pour
n'importe quel client B2B (courtier, éditeur SaaS, agence, cabinet de
recrutement, etc.).

**Le produit n'est spécifique à aucun secteur.** Chaque client configure son
propre ICP (codes NAF, effectif, ancienneté, zone géographique, mots-clés
positifs/négatifs) via `criteres_ciblage` en base — aucune valeur métier
n'est codée en dur dans l'agent.

> 🚧 **Statut : Sprint 0 (conception).** Le code du pipeline n'existe pas
> encore — voir [`docs/ISSUES.md`](docs/ISSUES.md) pour l'avancement détaillé
> des 41 issues réparties sur 5 sprints. Ce README décrit la cible du MVP.

## Comment ça marche

```
Sirene INSEE (collecte, filtrée par l'ICP du client)
        │
        ▼
Enrichissement (Tavily → Crawl4AI/Playwright → DuckDuckGo)
        │
        ▼
Nettoyage (dédup SIRET, Bloctel, exclusions client, filtre ICP)
        │
        ▼
Scoring hybride : 35% règles + 45% Claude (LLM) + 20% embeddings Qdrant
        │
        ▼
File d'appel triée par score (vue PostgreSQL `file_appel`)
```

Le commercial n'a plus qu'à appeler dans l'ordre de la file. Voir
[`docs/PRD.md`](docs/PRD.md) pour la vision produit complète et
[`docs/SCORING.md`](docs/SCORING.md) pour le détail du scoring.

## Stack technique

```
Python 3.12 + LangChain + Pydantic v2
PostgreSQL 16 (Docker) + Qdrant (Docker) + Ollama CPU (Docker)
Claude API (scoring LLM — modèle configuré dans config/settings.py)
Sirene INSEE + Tavily + Crawl4AI + Bloctel + Dropcontact
VPS CPU OVH — tout self-hosted
```

Détail complet (schéma BDD, arborescence, variables d'environnement) dans
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Règles absolues du projet

1. **Bloctel obligatoire** avant tout appel prospect, avec re-vérification
   tous les 30 jours max.
2. **Sources légales uniquement** : Sirene INSEE, Tavily, Pappers. Zéro
   scraping illégal.
3. **Aucun ICP codé en dur** : codes NAF, effectif, ancienneté, zone,
   mots-clés viennent tous de `criteres_ciblage` / `icp_profiles` en base.
   Un client = un ICP = une configuration.
4. **Exclusions configurables par client** — jamais de liste de
   marques/groupes codée en dur.
5. **Embeddings locaux sur CPU** : Ollama + nomic-embed-text v2.
6. **LLM scorer en cloud** : Claude API uniquement.
7. **Pydantic v2 partout**, **async partout** (asyncpg, AsyncQdrantClient,
   httpx).
8. **RGPD** : purge automatique selon la politique de rétention (job
   récurrent, pas une tâche manuelle).

Détail complet dans [`docs/LEGAL.md`](docs/LEGAL.md) et `CLAUDE.md`.

## Documentation

| Sujet | Fichier |
|---|---|
| Architecture, BDD, Docker, APIs | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Scoring hybride, prompts Claude, embeddings | [`docs/SCORING.md`](docs/SCORING.md) |
| Issues détaillées (Sprint 0 à Sprint 4) | [`docs/ISSUES.md`](docs/ISSUES.md) |
| Règles légales (Bloctel, RGPD) | [`docs/LEGAL.md`](docs/LEGAL.md) |
| Produit, user stories, KPIs | [`docs/PRD.md`](docs/PRD.md) |

## Commandes du quotidien (cible Sprint 1+)

```bash
make dev                                        # Démarre Postgres + Qdrant + Ollama + pgAdmin
python scripts/smoke_test.py                    # Vérifie que tout répond
python scripts/init_icp.py --client-id <uuid>   # Génère l'embedding ICP d'un client → Qdrant
python main.py --client-id <uuid> --depts 75,92 --limit 50 --dry-run
pytest tests/ -v
```

## Roadmap

```
Sprint 0 (Sem. 0)   : Conception & design — maquettes, ERD, ICP, comptes API
Sprint 1 (Sem. 1-2) : Fondations — Docker, schéma SQL, Qdrant, modèles Pydantic
Sprint 2 (Sem. 3-4) : Collecte & enrichissement — Sirene, Tavily, Bloctel, Dropcontact
Sprint 3 (Sem. 5-6) : Scoring & pipeline — règles + LLM + embeddings, graphe LangChain
Sprint 4 (Sem. 7-8) : Production — déploiement VPS, Airtable, Metabase, jobs légaux
```

MVP : 9 semaines. Détail des 41 issues dans [`docs/ISSUES.md`](docs/ISSUES.md).

## Coût mensuel MVP (par client actif)

~70-90€ : Dropcontact 24€ + Tavily 20€ + Claude API ~10€ + VPS OVH ~15-30€ + Bloctel ~5€

## Équipe

Repo `95902/Agent-IA-de-prospection-B2B-` · 3 personnes · 5 sprints de 2 semaines
