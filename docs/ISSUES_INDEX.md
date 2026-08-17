# Index des issues GitHub rapatriées

Les 41 issues du repo `95902/Agent-IA-de-prospection-B2B-` rapatriées 
depuis GitHub, organisées par sprint dans `docs/issues/<sprint>/`.

Total : **39 issues** (récupérées le 2026-07-31 ; #20 et #40, dédiées à Bloctel, ont été supprimées suite au retrait de cette contrainte du produit).

## Sprint 0 — Conception & Design (5)

- ✅ [#1](./issues/sprint-0/1-maquettes-stitch-5-ecrans-principaux-dashboard-pro.md) — Maquettes Stitch — 5 écrans principaux (dashboard, prospects, fiche, file d'appel, création campagne)
- ✅ [#2](./issues/sprint-0/2-maquette-fiche-profil-client-b2b-wizard-4-etapes.md) — Maquette fiche profil client B2B (wizard 4 étapes)
- ✅ [#3](./issues/sprint-0/3-modelisation-bdd-schema-entite-relation-8-tables-r.md) — Modélisation BDD — schéma entité-relation (8 tables + relations + cardinalités)
- 🟢 [#4](./issues/sprint-0/4-modeliser-la-configuration-icp-generique-par-clien.md) — Modéliser la configuration ICP générique (par client)
- ✅ [#5](./issues/sprint-0/5-valider-la-stack-technique-avec-l-equipe-ouvrir-le.md) — Valider la stack technique avec l'équipe + ouvrir les comptes API (INSEE, Tavily, Bloctel, Dropcontact)

## Sprint 1 — Fondations (9)

- 🟢 [#6](./issues/sprint-1/6-creer-docker-compose-yml-postgresql-16-qdrant-olla.md) — Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama)
- 🟢 [#7](./issues/sprint-1/7-creer-le-schema-sql-postgresql-8-tables-completes.md) — Créer le schéma SQL PostgreSQL — 8 tables complètes
- 🟢 [#8](./issues/sprint-1/8-configurer-ollama-nomic-embed-text-v2-embeddings-c.md) — Configurer Ollama + nomic-embed-text v2 (embeddings CPU)
- 🟢 [#9](./issues/sprint-1/9-initialiser-collections-qdrant-utils-db-py.md) — Initialiser collections Qdrant + utils/db.py
- 🟢 [#10](./issues/sprint-1/10-creer-modeles-pydantic-v2-prospect-score-etatagent.md) — Créer modèles Pydantic v2 — Prospect, Score, EtatAgent
- 🟢 [#11](./issues/sprint-1/11-initialiser-structure-projet-python-arborescence-c.md) — Initialiser structure projet Python (arborescence complète)
- 🟢 [#12](./issues/sprint-1/12-configurer-profil-icp-script-init-icp-py.md) — Configurer profil ICP + script init_icp.py
- 🟢 [#13](./issues/sprint-1/13-tests-unitaires-modeles-pydantic-telephone-email-s.md) — Tests unitaires modèles Pydantic (téléphone, email, SIRET)
- 🟢 [#14](./issues/sprint-1/14-script-smoke-test-py-verifier-que-la-stack-demarre.md) — Script smoke_test.py — vérifier que la stack démarre

## Sprint 2 — Collecte & Enrichissement (8)

- 🟢 [#15](./issues/sprint-2/15-implementer-sirene-agent-py-api-insee-pagination.md) — Implémenter sirene_agent.py — API INSEE + pagination
- 🟢 [#16](./issues/sprint-2/16-node-init-campagne-charger-criteres-depuis-bdd.md) — Node init_campagne — charger critères depuis BDD
- 🟢 [#17](./issues/sprint-2/17-tests-integration-sirene-50-prospects-reels.md) — Tests intégration Sirene (50 prospects réels)
- 🟢 [#18](./issues/sprint-2/18-implementer-enrichissement-agent-py-tavily-crawl4a.md) — Implémenter enrichissement_agent.py (Tavily+Crawl4AI+DDG)
- 🟢 [#19](./issues/sprint-2/19-implementer-nettoyage-agent-py-dedup-filtres-group.md) — Implémenter nettoyage_agent.py (dédup + filtres groupes)
- 🟢 [#21](./issues/sprint-2/21-integrer-dropcontact-enrichissement-emails-b2b.md) — Intégrer Dropcontact — enrichissement emails B2B
- 🟢 [#22](./issues/sprint-2/22-test-e2e-pipeline-collecte-100-prospects-icp-pilot.md) — Test E2E pipeline collecte (100 prospects, ICP pilote)
- 🟢 [#23](./issues/sprint-2/23-metriques-par-source-taux-succes-couts.md) — Métriques par source (taux succès + coûts)

## Sprint 3 — Scoring & Pipeline (9)

- 🟢 [#24](./issues/sprint-3/24-scoring-regles-metier-python-generique-35-du-score.md) — Scoring règles métier Python générique (35% du score)
- 🟢 [#25](./issues/sprint-3/25-prompts-claude-scoring-llm-generes-dynamiquement-d.md) — Prompts Claude scoring LLM générés dynamiquement depuis l'ICP (45%)
- 🟢 [#26](./issues/sprint-3/26-scoring-similarite-embeddings-icp-qdrant-20.md) — Scoring similarité embeddings ICP Qdrant (20%)
- 🟢 [#27](./issues/sprint-3/27-agregation-score-final-historique-bdd.md) — Agrégation score final + historique BDD
- 🟢 [#28](./issues/sprint-3/28-assembler-graphe-langchain-complet-6-nodes.md) — Assembler graphe LangChain complet (6 nodes)
- 🟢 [#29](./issues/sprint-3/29-creer-main-py-cli-argparse.md) — Créer main.py CLI argparse
- 🟢 [#30](./issues/sprint-3/30-configurer-langsmith-traces-couts-llm.md) — Configurer LangSmith (traces + coûts LLM)
- 🟢 [#31](./issues/sprint-3/31-tests-unitaires-scoring-20-cas-mock-claude.md) — Tests unitaires scoring — 20 cas (mock Claude)
- 🟢 [#32](./issues/sprint-3/32-audit-qualite-scores-100-prospects-reels.md) — Audit qualité scores — 100 prospects réels

## Sprint 4 — Production (8)

- 🟢 [#33](./issues/sprint-4/33-deployer-stack-docker-sur-vps-ovh-prod.md) — Déployer stack Docker sur VPS OVH (prod)
- 🟢 [#34](./issues/sprint-4/34-configurer-cron-campagnes-automatiques-lundi-6h.md) — Configurer cron campagnes automatiques (lundi 6h)
- 🟢 [#35](./issues/sprint-4/35-premiere-campagne-reelle-500-prospects-client-pilo.md) — 🚀 Première campagne réelle — 500 prospects (client pilote)
- 🟢 [#36](./issues/sprint-4/36-synchroniser-prospects-qualifies-airtable.md) — Synchroniser prospects qualifiés → Airtable
- 🟢 [#37](./issues/sprint-4/37-installer-metabase-sur-vps-dashboard-kpis.md) — Installer Metabase sur VPS (dashboard KPIs)
- 🟢 [#38](./issues/sprint-4/38-rapport-hebdomadaire-automatique-par-email-brevo.md) — Rapport hebdomadaire automatique par email (Brevo)
- 🟢 [#39](./issues/sprint-4/39-retrospective-mvp-plan-phase-2.md) — Rétrospective MVP + plan Phase 2
- 🟢 [#41](./issues/sprint-4/41-job-de-purge-rgpd-automatique-legal-obligatoire.md) — Job de purge RGPD automatique ⚠️ LÉGAL OBLIGATOIRE
