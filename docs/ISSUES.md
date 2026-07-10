# ISSUES.md — 41 issues GitHub · 5 sprints (générique, multi-secteurs)

> Pour créer toutes les issues dans GitHub via Claude Code :
> `gh issue create --title "..." --body "..." --label "..." --repo 95902/Agent-IA-de-prospection-B2B-`
>
> Le produit n'est pas verrouillé sur un secteur : l'ICP (codes NAF, effectif,
> ancienneté, exclusions) est une configuration par client, pas du code. Les
> exemples "garages" ci-dessous sont illustratifs pour Sprint 0-2 (premier
> client pilote) — aucune valeur ne doit finir codée en dur dans le code.

---

## Sprint 0 — Conception & Design (Sem. 0) · 5 issues · 8 pts

### #S0-1 · Maquettes Stitch — 5 écrans principaux
**Labels :** `design` `maquettes` `sprint-0`  
**Estimation :** 2 pts  
**Écrans à concevoir :**
- Dashboard principal (KPIs + chart + table derniers prospects)
- Liste prospects (table dense + filtres département/NAF/score)
- Fiche prospect détaillée (score breakdown + justification LLM)
- File d'appel (vue commerciale, boutons RDV/Refus/Absent)
- Création de campagne (formulaire critères + zone + NAF)

**Outil :** Google Stitch (stitch.withgoogle.com) — Experimental Mode Gemini 2.5 Pro  
**Critères d'acceptance :**
- [ ] 5 écrans exportés en PNG/Figma
- [ ] Design system cohérent (couleurs, typo, composants)
- [ ] Validé par l'équipe avant Sprint 1

---

### #S0-2 · Maquette fiche profil client B2B (wizard 4 étapes)
**Labels :** `design` `maquettes` `sprint-0`  
**Estimation :** 2 pts  
**Écrans à concevoir :**
- Étape 1 : Informations client (nom, secteur, contact)
- Étape 2 : Zone & ciblage (départements, codes NAF, effectif)
- Étape 3 : Profil ICP (texte description + mots-clés +/-)
- Étape 4 : Confirmation (résumé + bouton créer)
- Fiche profil complète (KPIs + historique campagnes + coûts)

**Critères d'acceptance :**
- [ ] Wizard 4 étapes maquetté
- [ ] Fiche profil complète avec toutes les sections

---

### #S0-3 · Modélisation BDD — schéma entité-relation
**Labels :** `database` `conception` `sprint-0`  
**Estimation :** 2 pts  
**Livrables :**
- Diagramme ERD (8 tables + relations + cardinalités)
- Liste des index critiques justifiés
- Validation des types de données (UUID, JSONB, arrays)
- Schéma Qdrant (2 collections + dimensions + distance)

**Critères d'acceptance :**
- [ ] ERD exporté en PNG ou Mermaid
- [ ] Toutes les FK documentées
- [ ] Validé par l'équipe avant écriture du SQL

---

### #S0-4 · Modéliser la configuration ICP générique (par client)
**Labels :** `ia` `icp` `conception` `sprint-0`  
**Estimation :** 1 pt  
**Livrables :**
- Formulaire/script de saisie ICP par client : `description_icp`, `codes_naf`, `effectif_min/max`, `anciennete_min_ans`, `departements`, `mots_cles_positifs/negatifs`
- Validation qu'**aucune** de ces valeurs n'est codée en dur ailleurs dans le code (agents, prompts, scripts)
- Pour le client pilote : renseigner un premier ICP concret (ex. garages indépendants — codes NAF 4520Z/4511Z/4531Z/4532Z, effectif 2-15, ancienneté 3 ans) comme donnée de test, pas comme valeur par défaut du produit

---

### #S0-5 · Valider stack + ouvrir tous les comptes API
**Labels :** `setup` `conception` `sprint-0`  
**Estimation :** 1 pt  
**Actions :**
- [ ] Ouvrir compte Bloctel professionnel (délai 3-5 jours ⚠️)
- [ ] Ouvrir compte Tavily (1000 req/mois gratuit)
- [ ] Tester API Sirene INSEE (clé gratuite api.insee.fr)
- [ ] Ouvrir compte Dropcontact (24€/mois)
- [ ] Créer repo GitHub + inviter les 3 collaborateurs
- [ ] Configurer .env.example avec toutes les variables

---

## Sprint 1 — Fondations (Sem. 1-2) · 9 issues · 17 pts

### #1 · Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama)
**Labels :** `infrastructure` `docker` `sprint-1` `priorité-haute`  
**Estimation :** 3 pts  
**Fichiers à créer :**
- [ ] `docker-compose.yml` (postgres + qdrant + ollama + pgadmin profil dev)
- [ ] `docker-compose.prod.yml` (ports liés à 127.0.0.1)
- [ ] `docker/qdrant/config.yaml` (HNSW m=16, API key)
- [ ] `.env.example` (toutes les variables)
- [ ] `Makefile` (make dev/prod/stop/psql/logs/backup)

**Critères d'acceptance :**
- [ ] `make dev` démarre tous les services sans erreur
- [ ] `curl localhost:6333/healthz` → OK
- [ ] `curl localhost:11434` → Ollama running

---

### #2 · Créer le schéma SQL PostgreSQL (8 tables + triggers + vue)
**Labels :** `database` `postgresql` `sprint-1` `priorité-haute`  
**Estimation :** 3 pts  
**Fichier :** `docker/postgres/init/01_schema.sql`  
**Contenu :**
- [ ] 8 tables (voir ARCHITECTURE.md)
- [ ] Extensions : `uuid-ossp`, `pg_trgm`
- [ ] Triggers `set_updated_at()` sur clients, campagnes, prospects
- [ ] Index critiques (statut, score, département, naf, trgm)
- [ ] Vue `file_appel` avec filtre bloctel_ok = TRUE
- [ ] Données initiales table `sources` (5 entrées)

**Critères d'acceptance :**
- [ ] `make psql` + `\dt` → 8 tables présentes
- [ ] Vue `file_appel` requêtable sans erreur

---

### #3 · Configurer Ollama + nomic-embed-text v2 (embeddings CPU)
**Labels :** `ia` `embeddings` `sprint-1` `priorité-haute`  
**Estimation :** 2 pts  
**Fichiers :**
- [ ] Ollama dans docker-compose.yml avec volume modèles
- [ ] Script entrypoint qui pull `nomic-embed-text` au démarrage
- [ ] `utils/embeddings.py` avec `async get_embedding(text: str) -> list[float]`

**Critères d'acceptance :**
- [ ] `curl -X POST localhost:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'` → vecteur 768 dims
- [ ] `utils/embeddings.py` retourne une liste de 768 floats
- [ ] Temps de réponse < 500ms sur CPU OVH

---

### #4 · Initialiser collections Qdrant + utils/db.py
**Labels :** `database` `qdrant` `sprint-1` `priorité-haute`  
**Estimation :** 3 pts  
**Fichier :** `utils/db.py`  
**Fonctions à implémenter :**
- [ ] `get_pg_pool()` — pool asyncpg singleton
- [ ] `get_qdrant()` — AsyncQdrantClient singleton
- [ ] `_ensure_collections()` — crée si absent, idempotent
- [ ] `upsert_prospect(data: dict) -> str` — ON CONFLICT siret
- [ ] `get_file_appel(limit: int) -> list[dict]`
- [ ] `save_score(prospect_id, score_data)`
- [ ] `upsert_prospect_embedding(prospect_id, embedding, payload)`
- [ ] `search_similar_prospects(query_embedding, top_k, departement?)`
- [ ] `get_icp_embedding(icp_id) -> list[float]`

**Critères d'acceptance :**
- [ ] Premier lancement → 2 collections créées dans Qdrant
- [ ] Deuxième lancement → pas d'erreur (idempotent)
- [ ] `upsert_prospect` fonctionne (test round-trip)

---

### #5 · Créer modèles Pydantic v2 (Prospect, Score, EtatAgent)
**Labels :** `modèles` `pydantic` `sprint-1` `priorité-haute`  
**Estimation :** 2 pts  
**Fichiers :** `models/prospect.py`, `models/score.py`, `graph/state.py`  
**Validators obligatoires :**
- [ ] `telephone` → normalisation E.164 via `phonenumbers`
- [ ] `email` → regex + blacklist domaines (pagesjaunes.fr, noreply., etc.)
- [ ] `siret` → exactement 14 chiffres
- [ ] `to_db_dict()` → dict asyncpg-compatible

**Critères d'acceptance :**
- [ ] `0612345678` → `+33612345678`
- [ ] SIRET invalide → `ValidationError`
- [ ] Email blacklisté → `None`

---

### #6 · Initialiser structure projet Python
**Labels :** `setup` `sprint-1` `priorité-haute`  
**Estimation :** 1 pt  
**Créer l'arborescence complète** (voir ARCHITECTURE.md)  
**Critères d'acceptance :**
- [ ] `python main.py --help` fonctionne
- [ ] `pip install -r requirements.txt` sans erreur
- [ ] Tous les imports résolus

---

### #7 · Configurer profil ICP + script init_icp.py
**Labels :** `ia` `icp` `sprint-1` `priorité-haute`  
**Estimation :** 1 pt  
**Fichiers :** `config/icp_seed_example.py` (exemple illustratif, pas un défaut produit), `scripts/init_icp.py --client-id <uuid>`  
**Critères d'acceptance :**
- [ ] `python scripts/init_icp.py` → embedding inséré dans Qdrant
- [ ] Collection `icp_profiles` contient 1 vecteur

---

### #8 · Tests unitaires modèles Pydantic
**Labels :** `tests` `sprint-1` `priorité-moyenne`  
**Estimation :** 1 pt  
**Fichier :** `tests/test_models.py`  
**20 cas à tester** (tel, email, SIRET, to_db_dict)  
**Critères d'acceptance :**
- [ ] `pytest tests/test_models.py` → 100% pass

---

### #9 · Script smoke_test.py
**Labels :** `tests` `infrastructure` `sprint-1` `priorité-moyenne`  
**Estimation :** 1 pt  
**Fichier :** `scripts/smoke_test.py`  
**Checks :** PostgreSQL (8 tables) + Qdrant (2 collections) + Ollama (modèle) + embedding test + round-trip BDD  
**Critères d'acceptance :**
- [ ] Passe en vert en local ET sur VPS OVH

---

## Sprint 2 — Collecte & Enrichissement (Sem. 3-4) · 9 issues · 17 pts

### #10 · Implémenter sirene_agent.py
**Labels :** `collecte` `sirene` `sprint-2` `priorité-haute`  
**Estimation :** 3 pts  
**Endpoint INSEE (NAF et DEPT viennent de `criteres_ciblage`, jamais codés en dur) :**
```
GET https://api.insee.fr/entreprises/sirene/V3.11/siret
?q=activitePrincipaleEtablissement:{NAF}
  AND codePostalEtablissement:{DEPT}*
  AND etatAdministratifEtablissement:A
&nombre=100&debut=0
```
**Fonctions :**
- [ ] `fetch_sirene(etat, api_key)` — node LangChain
- [ ] `_fetch_etablissements(client, headers, dept, naf, limit)` — pagination
- [ ] `_parser_etablissement(etab)` — parse → Prospect

**Gestion :** Rate limit 429 → sleep 2s + retry (max 3) · Pagination auto  
**Critères :** 50 prospects (ICP pilote, dept. 75 en exemple) en < 30s · 100% SIRET valides

---

### #11 · Node init_campagne — charger critères depuis BDD
**Labels :** `collecte` `database` `sprint-2` `priorité-haute`  
**Estimation :** 2 pts  
**Fichier :** `graph/workflow.py` (premiers nodes)  
**Fixtures SQL de test incluses** (client pilote générique + critères + campagne — nom de test neutre, pas lié à un secteur)

---

### #12 · Tests intégration Sirene (50 prospects réels)
**Labels :** `tests` `intégration` `sprint-2` `priorité-moyenne`  
**Estimation :** 1 pt  
**Marker pytest :** `@pytest.mark.integration` (exclu du CI auto)

---

### #13 · Implémenter enrichissement_agent.py
**Labels :** `enrichissement` `sprint-2` `priorité-haute`  
**Estimation :** 3 pts  
**Cascade :** Tavily → Crawl4AI + Playwright → DuckDuckGo fallback  
**Batch :** 5 prospects en parallèle (asyncio.gather)  
**Regex :**
```python
RE_PHONE = r'(?:(?:\+33|0033|0)[1-9])(?:[\s.\-]?\d{2}){4}'
RE_EMAIL = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
```
**Critères :** > 40% taux enrichissement téléphone

---

### #14 · Implémenter nettoyage_agent.py
**Labels :** `nettoyage` `sprint-2` `priorité-haute`  
**Estimation :** 2 pts  
**Actions :** Dédup SIRET · Normalisation E.164 · Bloctel (#15) · Exclusions client (`mots_cles_negatifs`, voir #19) · Filtre effectif hors cible ICP

---

### #15 · Implémenter utils/bloctel.py ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `bloctel` `compliance` `sprint-2` `priorité-haute`  
**Estimation :** 2 pts  
**⚠️ Lire LEGAL.md avant de commencer.**  
**Fonction :** `verifier_batch(numeros: list[str]) -> dict[str, bool]`  
**Critères :** 100 numéros en < 5s · bloctel_ok=False exclu de file_appel · colonne `bloctel_verifie_le` posée pour permettre la re-vérification à 30 jours (voir #35)

---

### #16 · Intégrer Dropcontact (emails B2B)
**Labels :** `enrichissement` `email` `sprint-2` `priorité-moyenne`  
**Estimation :** 2 pts  
**Flow :** POST /batch → request_id → polling 5s → upsert email  
**Condition :** email=None ET nom_dirigeant≠None ET site_web≠None

---

### #17 · Test E2E pipeline collecte (100 prospects, ICP pilote)
**Labels :** `tests` `intégration` `sprint-2` `priorité-haute`  
**Estimation :** 1 pt  
**Cibles :** ≥40% tél · ≥20% email · 0 doublon · 0 prospect matchant une exclusion ICP · Bloctel 100% · < 10 min

---

### #18 · Métriques par source
**Labels :** `monitoring` `sprint-2` `priorité-basse`  
**Estimation :** 1 pt  
**Fichier :** `utils/metrics.py` · Mise à jour table `sources`

---

## Sprint 3 — Scoring & Pipeline (Sem. 5-6) · 9 issues · 17 pts

### #19 · Scoring règles métier Python générique (35%)
**Labels :** `scoring` `sprint-3` `priorité-haute`  
**Estimation :** 2 pts  
**Voir SCORING.md** pour le barème complet — toutes les valeurs (effectif, ancienneté, exclusions) viennent de `criteres_ciblage`, aucune constante métier codée en dur  
**Critères :** `_score_effectif` et `_score_anciennete` sont des fonctions pures testées indépendamment (pas de dict jamais lu comme dans une version antérieure du barème) · `_matche_exclusion` teste par mot entier, pas par sous-chaîne

---

### #20 · Prompts Claude scoring LLM générés dynamiquement depuis l'ICP (45%)
**Labels :** `scoring` `llm` `prompt-engineering` `sprint-3` `priorité-haute`  
**Estimation :** 3 pts  
**Fichiers :** `prompts/scorer_system.txt.j2` + `prompts/scorer_user.txt.j2` (templates Jinja, rendus depuis `clients` + `criteres_ciblage`, pas de texte figé)  
**Voir SCORING.md** pour les templates complets  
**Critères :** JSON valide 100% · < 0.003€/prospect · justification > 20 mots · prompt caching activé sur le system prompt rendu (économie ~90% après le 1er appel de la campagne) · modèle Claude configurable via `settings.CLAUDE_SCORING_MODEL`, jamais codé en dur

---

### #21 · Scoring embeddings ICP Qdrant (20%)
**Labels :** `scoring` `embeddings` `sprint-3` `priorité-haute`  
**Estimation :** 2 pts  
**Voir SCORING.md** pour l'algorithme complet  
**Critères :** < 200ms/prospect sur CPU OVH

---

### #22 · Agrégation score final + historique BDD
**Labels :** `scoring` `database` `sprint-3` `priorité-haute`  
**Estimation :** 1 pt  
**Formule :** `round(0.35×règles + 0.45×llm + 0.20×embedding)`  
**Voir SCORING.md** pour l'implémentation complète

---

### #23 · Assembler graphe LangChain complet (6 nodes)
**Labels :** `workflow` `langchain` `sprint-3` `priorité-haute`  
**Estimation :** 3 pts  
**Fichier :** `graph/workflow.py`  
**Nodes :** init_campagne → fetch_sirene → enrichir → nettoyer → scorer → sauvegarder  
**Fallback :** Claude down → scoring règles uniquement  
**Critères :** < 15 min pour 100 prospects bout-en-bout

---

### #24 · Créer main.py CLI argparse
**Labels :** `cli` `sprint-3` `priorité-moyenne`  
**Estimation :** 1 pt  
**Usage :**
```bash
python main.py --campagne-id {uuid}
python main.py --depts 75,92 --naf 4520Z --limit 200
python main.py --depts 75 --limit 10 --dry-run
python main.py --list-campagnes
```

---

### #25 · Configurer LangSmith
**Labels :** `monitoring` `sprint-3` `priorité-basse`  
**Estimation :** 1 pt  
**Critères :** Traces visibles sur smith.langchain.com · Coût par run visible

---

### #26 · Tests unitaires scoring (20 cas + mock Claude)
**Labels :** `tests` `scoring` `sprint-3` `priorité-haute`  
**Estimation :** 2 pts  
**Cas (avec un ICP de test générique, pas garage-spécifique) :**
- Prospect qui matche parfaitement l'ICP de test → score > 75
- Prospect en périphérie de l'ICP (effectif/ancienneté limites) → score < 30
- Prospect matchant un `mots_cles_negatifs` de test → score = 0
- Prospect qualifié sans email (téléphone seul) → score 55-70
- Mock Claude indisponible → fallback règles
- Deux ICP de test différents (secteurs distincts) sur les mêmes prospects → scores cohérents avec chaque ICP respectif

---

### #27 · Audit qualité scores (100 prospects réels)
**Labels :** `qualité` `validation` `sprint-3` `priorité-haute`  
**Estimation :** 2 pts  
**Critères :** Export CSV · 20 revus manuellement · accord humain > 75%

---

## Sprint 4 — Production (Sem. 7-8) · 9 issues · 14 pts

### #28 · Déployer stack Docker sur VPS OVH (prod)
**Labels :** `déploiement` `vps` `production` `sprint-4` `priorité-haute`  
**Estimation :** 3 pts  
**Checklist :**
- [ ] Ubuntu 22.04 + Docker CE + Docker Compose
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- [ ] Hardening : fail2ban + ufw + clé SSH uniquement
- [ ] Ports 5432 et 6333 liés à 127.0.0.1 UNIQUEMENT
- [ ] Backup PostgreSQL cron quotidien à 2h
- [ ] smoke_test.py passe en vert sur VPS

---

### #29 · Configurer cron campagnes automatiques
**Labels :** `automatisation` `sprint-4` `priorité-moyenne`  
**Estimation :** 1 pt  
**Crontab :**
```bash
0 6 * * 1 cd /opt/prospection_b2b && python main.py --campagne-id {uuid} >> /var/log/prospection_b2b.log 2>&1
0 2 * * * docker exec prospection_b2b_postgres pg_dump -U scraper prospection_b2b | gzip > /opt/backups/$(date +%Y%m%d).sql.gz
```

---

### #30 · 🚀 Première campagne réelle — 500 prospects (client pilote)
**Labels :** `campagne` `production` `sprint-4` `priorité-haute`  
**Estimation :** 2 pts  
**Config :** ICP du client pilote (ex. garages IDF : depts 75,92,93,94, NAF 4520Z,4511Z,4531Z,4532Z) · limit 500 — config lue depuis `criteres_ciblage`, pas en dur dans le script  
**Objectifs :** 200+ tél (40%) · 100+ emails (20%) · 150+ qualifiés · export CSV

---

### #31 · Synchroniser prospects qualifiés → Airtable
**Labels :** `crm` `airtable` `sprint-4` `priorité-haute`  
**Estimation :** 2 pts  
**Fichier :** `utils/airtable_sync.py`  
**Upsert sur SIRET · Sync bidirectionnelle statut · Nouveaux qualifiés seulement**

---

### #32 · Installer Metabase sur VPS (dashboard KPIs)
**Labels :** `monitoring` `metabase` `sprint-4` `priorité-moyenne`  
**Estimation :** 2 pts  
**6 questions :** statuts · score/département · enrichissement · évolution · top 10 · KPIs campagne

---

### #33 · Rapport hebdomadaire automatique (Brevo)
**Labels :** `reporting` `sprint-4` `priorité-basse`  
**Estimation :** 1 pt  
**Fichier :** `scripts/rapport_hebdo.py` · Cron lundi 8h

---

### #34 · Rétrospective MVP + plan Phase 2
**Labels :** `planning` `sprint-4` `priorité-haute`  
**Estimation :** 1 pt  
**Métriques à comparer vs cibles** (voir PRD.md) · Décisions Phase 2 (vocal, mailing, DeepSeek)

---

### #35 · Job de re-vérification Bloctel (30 jours) ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `bloctel` `compliance` `automatisation` `sprint-4` `priorité-haute`  
**Estimation :** 1 pt  
**⚠️ Lire LEGAL.md → Règle 5.**  
**Contexte :** un numéro vérifié il y a plus de 30 jours ne doit plus être appelable sans re-vérification (obligation légale, amende jusqu'à 75 000€). Ce point n'était couvert par aucune tâche dans le plan initial — corrigé ici.  
**Actions :**
- [ ] Script `scripts/reverifier_bloctel.py` : sélectionne les prospects avec `bloctel_verifie_le` absent ou > 30 jours et appelables (statut qualifié/nouveau)
- [ ] Repasse `bloctel_ok = NULL` tant que non re-vérifié (donc exclu de `file_appel`)
- [ ] Cron quotidien (`crontab` ou `make cron-bloctel`)
- [ ] Log du nombre de prospects re-vérifiés / repassés en attente

**Critères d'acceptance :**
- [ ] Un prospect avec `bloctel_verifie_le` > 30 jours disparaît de `file_appel` tant qu'il n'est pas re-vérifié
- [ ] Le job tourne sans intervention manuelle

---

### #36 · Job de purge RGPD automatique ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `rgpd` `compliance` `automatisation` `sprint-4` `priorité-haute`  
**Estimation :** 1 pt  
**⚠️ Lire LEGAL.md → Durée de conservation.**  
**Contexte :** la politique de rétention (invalides 6 mois, qualifiés non convertis 3 ans, appels 1 an, logs 3 mois) était documentée dans LEGAL.md mais sans job pour l'appliquer — corrigé ici.  
**Actions :**
- [ ] Script `scripts/purge_rgpd.py` appliquant les 4 règles de rétention
- [ ] Anonymisation ou suppression selon le type de donnée (voir LEGAL.md)
- [ ] Journal d'audit des suppressions (nombre de lignes, motif, date)
- [ ] Cron quotidien

**Critères d'acceptance :**
- [ ] Aucun prospect invalide de plus de 6 mois en base après un run
- [ ] Journal d'audit consultable

---

## Commande Claude Code pour créer toutes les issues

> ⚠️ Historique : les 41 issues et tous les labels ci-dessous existent déjà
> sur GitHub (créés via `gh`). Cette liste ne reflète que l'état initial —
> elle omet `compliance`, `rgpd` et `embeddings`, ajoutés depuis. Ne pas
> relancer ce bloc tel quel sur un repo déjà initialisé.

```bash
# Depuis le terminal, avec gh CLI authentifié :

# Créer les labels d'abord
gh label create "design" --color "c5def5" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "maquettes" --color "bfd4f2" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "infrastructure" --color "0075ca" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "database" --color "1d76db" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "ia" --color "5319e7" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "collecte" --color "f9d0c4" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "enrichissement" --color "fef2c0" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "scoring" --color "c2e0c6" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "workflow" --color "bfd4f2" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "tests" --color "e4e669" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "légal" --color "d73a4a" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "bloctel" --color "d73a4a" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "déploiement" --color "d4c5f9" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "monitoring" --color "e4e669" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "sprint-0" --color "0052cc" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "sprint-1" --color "0052cc" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "sprint-2" --color "0052cc" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "sprint-3" --color "0052cc" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "sprint-4" --color "0052cc" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "priorité-haute" --color "d73a4a" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "priorité-moyenne" --color "fbca04" --repo 95902/Agent-IA-de-prospection-B2B-
gh label create "priorité-basse" --color "0e8a16" --repo 95902/Agent-IA-de-prospection-B2B-
```
