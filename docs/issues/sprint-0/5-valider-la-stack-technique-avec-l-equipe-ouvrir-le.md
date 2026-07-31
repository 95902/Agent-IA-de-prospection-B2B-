# #5 — Valider la stack technique avec l'équipe + ouvrir les comptes API (INSEE, Tavily, Bloctel, Dropcontact)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/5
> État : ✅ Fermée
> Sprint : Sprint 0 — Conception & Design
> Labels : `sprint-0`, `conception`, `setup`

---

**Sprint :** Sprint 0 — Conception & Design (Sem. 0)
**Points :** 1 pt
**Labels :** setup, conception, sprint-0

## Objectif
Valider les choix techniques avec l'équipe (3 personnes) et ouvrir tous les comptes API nécessaires au pipeline, avant le démarrage du Sprint 1. Certains délais d'obtention sont longs : à lancer en tout premier.

## Actions

- [ ] **Bloctel professionnel** — ouvrir un compte sur https://www.bloctel.gouv.fr (⚠️ délai d'obtention 3-5 jours ouvrés, à démarrer en priorité absolue — voir `docs/LEGAL.md`)
- [x] **Tavily** — ouvrir un compte (1000 requêtes/mois gratuites), récupérer la clé API
- [x] **API Sirene INSEE** — tester l'accès avec une clé gratuite sur https://api.insee.fr (endpoint `entreprises/sirene/V3.11/siret`)
- [ ] **Dropcontact** — ouvrir un compte (24€/mois), récupérer la clé API
- [x] **Repo GitHub** — créer/vérifier le repo `95902/Agent-IA-de-prospection-B2B-` et inviter les 3 collaborateurs de l'équipe
- [ ] **`.env.example`** — lister toutes les variables d'environnement nécessaires (clés API ci-dessus + connexions PostgreSQL/Qdrant/Ollama + `CLAUDE_API_KEY`)

## Contraintes
- Aucune clé API ou secret ne doit être commité en clair — seul `.env.example` (sans valeurs réelles) est versionné
- Le choix du modèle Claude pour le scoring doit rester configurable (`settings.CLAUDE_SCORING_MODEL`), jamais codé en dur dans les prompts (voir CLAUDE.md, règle #6)

## Critères d'acceptance
- [ ] Les 4 comptes API (Bloctel, Tavily, Sirene INSEE, Dropcontact) sont ouverts et une clé/accès valide est confirmé pour chacun
- [ ] Le repo GitHub contient les 3 collaborateurs avec les droits appropriés
- [ ] `.env.example` est présent à la racine et couvre toutes les variables utilisées dans `docs/ARCHITECTURE.md`


