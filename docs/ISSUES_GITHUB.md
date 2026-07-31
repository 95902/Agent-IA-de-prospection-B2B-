# ISSUES_GITHUB.md — Issues GitHub rapatriées, regroupées par sprint

> Instantané des 41 issues telles qu'elles existent sur GitHub
> (repo `95902/Agent-IA-de-prospection-B2B-`), récupérées via `gh issue list`
> le **2026-07-31** et organisées par sprint via le label `sprint-N`.
>
> Cette vue reflète l'état **réel** sur GitHub (numéro, titre, état, labels).
> Le détail fonctionnel (objectifs, checklists, critères d'acceptance) reste
> dans `docs/ISSUES.md`, qui utilise une numérotation interne différente
> (`#S0-1`, `#1`…) — voir la table de correspondance en bas de ce fichier.
>
> Légende : ✅ fermée · 🟢 ouverte · 🟡 en attente de validation (`enattvalidation`)

---

## Synthèse

| Sprint | Période | Issues (numéros GitHub) | Total | Ouvertes | Fermées |
|---|---|---|---|---|---|
| Sprint 0 — Conception & Design | Sem. 0 | #1 → #5 | 5 | 1 | 4 |
| Sprint 1 — Fondations | Sem. 1-2 | #6 → #14 | 9 | 9 | 0 |
| Sprint 2 — Collecte & Enrichissement | Sem. 3-4 | #15 → #23 | 9 | 9 | 0 |
| Sprint 3 — Scoring & Pipeline | Sem. 5-6 | #24 → #32 | 9 | 9 | 0 |
| Sprint 4 — Production | Sem. 7-8 | #33 → #41 | 9 | 9 | 0 |
| **Total** | | | **41** | **37** | **4** |

> ⚠️ Note Sprint 0 : les issues #1, #2, #3 et #5 sont fermées mais portent le
> label `enattvalidation` — elles attendent une validation d'équipe avant
> démarrage du Sprint 1. Seule #4 reste ouverte.

---

## Sprint 0 — Conception & Design (Sem. 0)

| # | État | Titre | Labels |
|---|---|---|---|
| [1](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/1) | ✅ 🟡 | Maquettes Stitch — 5 écrans principaux (dashboard, prospects, fiche, file d'appel, création campagne) | design, maquettes, sprint-0, enattvalidation |
| [2](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/2) | ✅ 🟡 | Maquette fiche profil client B2B (wizard 4 étapes) | design, maquettes, sprint-0, enattvalidation |
| [3](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/3) | ✅ 🟡 | Modélisation BDD — schéma entité-relation (8 tables + relations + cardinalités) | sprint-0, database, conception, enattvalidation |
| [4](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/4) | 🟢 | Modéliser la configuration ICP générique (par client) | sprint-0, conception, ia, icp, enattvalidation |
| [5](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/5) | ✅ | Valider la stack technique avec l'équipe + ouvrir les comptes API (INSEE, Tavily, Bloctel, Dropcontact) | sprint-0, conception, setup |

---

## Sprint 1 — Fondations (Sem. 1-2)

| # | État | Titre | Labels |
|---|---|---|---|
| [6](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/6) | 🟢 | Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama) | infrastructure, docker, sprint-1 |
| [7](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/7) | 🟢 | Créer le schéma SQL PostgreSQL — 8 tables complètes | database, sprint-1, postgresql |
| [8](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/8) | 🟢 | Configurer Ollama + nomic-embed-text v2 (embeddings CPU) | ia, sprint-1, embeddings |
| [9](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/9) | 🟢 | Initialiser collections Qdrant + utils/db.py | database, sprint-1, qdrant |
| [10](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/10) | 🟢 | Créer modèles Pydantic v2 — Prospect, Score, EtatAgent | sprint-1, modèles, pydantic |
| [11](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/11) | 🟢 | Initialiser structure projet Python (arborescence complète) | setup, sprint-1 |
| [12](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/12) | 🟢 | Configurer profil ICP + script init_icp.py | ia, icp, sprint-1 |
| [13](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/13) | 🟢 | Tests unitaires modèles Pydantic (téléphone, email, SIRET) | sprint-1, tests |
| [14](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/14) | 🟢 | Script smoke_test.py — vérifier que la stack démarre | infrastructure, sprint-1, tests |

---

## Sprint 2 — Collecte & Enrichissement (Sem. 3-4)

| # | État | Titre | Labels |
|---|---|---|---|
| [15](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/15) | 🟢 | Implémenter sirene_agent.py — API INSEE + pagination | collecte, sirene, sprint-2 |
| [16](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/16) | 🟢 | Node init_campagne — charger critères depuis BDD | database, collecte, sprint-2 |
| [17](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/17) | 🟢 | Tests intégration Sirene (50 prospects réels) | tests, sprint-2, intégration |
| [18](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/18) | 🟢 | Implémenter enrichissement_agent.py (Tavily+Crawl4AI+DDG) | sprint-2, enrichissement |
| [19](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/19) | 🟢 | Implémenter nettoyage_agent.py (dédup + filtres groupes) | sprint-2, nettoyage |
| [20](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/20) | 🟢 | Implémenter utils/bloctel.py ⚠️ LÉGAL OBLIGATOIRE | sprint-2, légal, bloctel, compliance |
| [21](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/21) | 🟢 | Intégrer Dropcontact — enrichissement emails B2B | sprint-2, enrichissement, email |
| [22](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/22) | 🟢 | Test E2E pipeline collecte (100 prospects, ICP pilote) | tests, sprint-2, intégration |
| [23](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/23) | 🟢 | Métriques par source (taux succès + coûts) | sprint-2, monitoring |

---

## Sprint 3 — Scoring & Pipeline (Sem. 5-6)

| # | État | Titre | Labels |
|---|---|---|---|
| [24](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/24) | 🟢 | Scoring règles métier Python générique (35% du score) | scoring, sprint-3 |
| [25](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/25) | 🟢 | Prompts Claude scoring LLM générés dynamiquement depuis l'ICP (45%) | scoring, sprint-3, llm, prompt-engineering |
| [26](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/26) | 🟢 | Scoring similarité embeddings ICP Qdrant (20%) | scoring, sprint-3, embeddings |
| [27](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/27) | 🟢 | Agrégation score final + historique BDD | database, scoring, sprint-3 |
| [28](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/28) | 🟢 | Assembler graphe LangChain complet (6 nodes) | sprint-3, workflow, langchain |
| [29](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/29) | 🟢 | Créer main.py CLI argparse | sprint-3, cli |
| [30](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/30) | 🟢 | Configurer LangSmith (traces + coûts LLM) | monitoring, sprint-3 |
| [31](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/31) | 🟢 | Tests unitaires scoring — 20 cas (mock Claude) | tests, scoring, sprint-3 |
| [32](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/32) | 🟢 | Audit qualité scores — 100 prospects réels | sprint-3, qualité, validation |

---

## Sprint 4 — Production (Sem. 7-8)

| # | État | Titre | Labels |
|---|---|---|---|
| [33](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/33) | 🟢 | Déployer stack Docker sur VPS OVH (prod) | déploiement, vps, sprint-4 |
| [34](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/34) | 🟢 | Configurer cron campagnes automatiques (lundi 6h) | sprint-4, automatisation |
| [35](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/35) | 🟢 | 🚀 Première campagne réelle — 500 prospects (client pilote) | sprint-4, campagne, production |
| [36](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/36) | 🟢 | Synchroniser prospects qualifiés → Airtable | sprint-4, crm, airtable |
| [37](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/37) | 🟢 | Installer Metabase sur VPS (dashboard KPIs) | monitoring, sprint-4, metabase |
| [38](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/38) | 🟢 | Rapport hebdomadaire automatique par email (Brevo) | sprint-4, reporting |
| [39](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/39) | 🟢 | Rétrospective MVP + plan Phase 2 | sprint-4, planning |
| [40](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/40) | 🟢 | Job de re-vérification Bloctel (30 jours) ⚠️ LÉGAL OBLIGATOIRE | légal, bloctel, sprint-4, automatisation, compliance |
| [41](https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/41) | 🟢 | Job de purge RGPD automatique ⚠️ LÉGAL OBLIGATOIRE | légal, sprint-4, automatisation, compliance, rgpd |

---

## Correspondance numérotation GitHub ↔ `docs/ISSUES.md`

`docs/ISSUES.md` utilise une numérotation interne (`#S0-1`…`#S0-5` pour le
Sprint 0, puis `#1`…`#36` pour les Sprints 1-4) qui **ne correspond pas** aux
numéros GitHub ci-dessus. La table ci-dessous fait le mapping pour naviguer
entre les deux documents.

| Sprint | ISSUES.md (interne) | GitHub (réel) | Titre court |
|---|---|---|---|
| 0 | #S0-1 | #1 | Maquettes Stitch 5 écrans |
| 0 | #S0-2 | #2 | Maquette profil client B2B |
| 0 | #S0-3 | #3 | Modélisation BDD ERD |
| 0 | #S0-4 | #4 | Config ICP générique |
| 0 | #S0-5 | #5 | Valider stack + comptes API |
| 1 | #1 | #6 | docker-compose.yml |
| 1 | #2 | #7 | Schéma SQL PostgreSQL |
| 1 | #3 | #8 | Ollama + nomic-embed-text |
| 1 | #4 | #9 | Collections Qdrant + utils/db.py |
| 1 | #5 | #10 | Modèles Pydantic v2 |
| 1 | #6 | #11 | Structure projet Python |
| 1 | #7 | #12 | Script init_icp.py |
| 1 | #8 | #13 | Tests modèles Pydantic |
| 1 | #9 | #14 | smoke_test.py |
| 2 | #10 | #15 | sirene_agent.py |
| 2 | #11 | #16 | Node init_campagne |
| 2 | #12 | #17 | Tests intégration Sirene |
| 2 | #13 | #18 | enrichissement_agent.py |
| 2 | #14 | #19 | nettoyage_agent.py |
| 2 | #15 | #20 | utils/bloctel.py |
| 2 | #16 | #21 | Intégration Dropcontact |
| 2 | #17 | #22 | Test E2E collecte |
| 2 | #18 | #23 | Métriques par source |
| 3 | #19 | #24 | Scoring règles (35%) |
| 3 | #20 | #25 | Prompts Claude LLM (45%) |
| 3 | #21 | #26 | Scoring embeddings (20%) |
| 3 | #22 | #27 | Agrégation score final |
| 3 | #23 | #28 | Graphe LangChain 6 nodes |
| 3 | #24 | #29 | main.py CLI |
| 3 | #25 | #30 | LangSmith |
| 3 | #26 | #31 | Tests scoring 20 cas |
| 3 | #27 | #32 | Audit qualité scores |
| 4 | #28 | #33 | Déploiement VPS OVH |
| 4 | #29 | #34 | Cron campagnes |
| 4 | #30 | #35 | Première campagne réelle |
| 4 | #31 | #36 | Sync Airtable |
| 4 | #32 | #37 | Metabase |
| 4 | #33 | #38 | Rapport hebdo Brevo |
| 4 | #34 | #39 | Rétrospective MVP |
| 4 | #35 | #40 | Re-vérification Bloctel 30j |
| 4 | #36 | #41 | Purge RGPD |