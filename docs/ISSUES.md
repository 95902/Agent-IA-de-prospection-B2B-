# ISSUES.md — 41 issues GitHub · 5 sprints (générique, multi-secteurs)

> Pour créer toutes les issues dans GitHub via Claude Code :
> `gh issue create --title "..." --body "..." --label "..." --repo 95902/Agent-IA-de-prospection-B2B-`
>
> Le produit n'est pas verrouillé sur un secteur : l'ICP (codes NAF, effectif,
> ancienneté, exclusions) est une configuration par client, pas du code. Les
> exemples "garages" ci-dessous sont illustratifs pour Sprint 0-2 (premier
> client pilote) — aucune valeur ne doit finir codée en dur dans le code.
>
> Le détail ci-dessous (objectifs, checklists, contraintes, critères
> d'acceptance) est synchronisé avec le contenu réellement publié sur les
> issues GitHub correspondantes (`gh issue view <n>`).

---

## Sprint 0 — Conception & Design (Sem. 0) · 5 issues · 8 pts

### #S0-1 · Maquettes Stitch — 5 écrans principaux
**Labels :** `design` `maquettes` `sprint-0`
**Estimation :** 2 pts

**Objectif**
Concevoir les 5 écrans principaux du produit sous forme de maquettes haute-fidélité, avant toute écriture de code Sprint 1+.

**Écrans à concevoir :**
- [ ] Dashboard principal — KPIs (prospects collectés, qualifiés, taux d'enrichissement, coût campagne), chart d'évolution, table des derniers prospects
- [ ] Liste prospects — table dense avec filtres département / code NAF / score, tri par colonne
- [ ] Fiche prospect détaillée — breakdown du score (règles / LLM / embedding), justification texte du LLM, coordonnées, historique
- [ ] File d'appel — vue commerciale, boutons d'action rapide (RDV / Refus / Absent), infos essentielles visibles sans scroll
- [ ] Création de campagne — formulaire critères de ciblage (départements, codes NAF, effectif, mots-clés +/-)

**Outil :** Google Stitch (stitch.withgoogle.com) — Experimental Mode Gemini 2.5 Pro

**Contraintes**
- Le produit n'est pas verrouillé sur un secteur : ne pas coder en dur de valeurs métier (NAF, secteur) dans les maquettes — utiliser des exemples génériques ou le client pilote comme illustration uniquement
- Cohérence avec la maquette du profil client B2B (#S0-2)

**Critères d'acceptance :**
- [ ] 5 écrans exportés en PNG et/ou lien Figma
- [ ] Design system cohérent (couleurs, typographie, composants réutilisables)
- [ ] Validé par l'équipe (3 personnes) avant le démarrage du Sprint 1

---

### #S0-2 · Maquette fiche profil client B2B (wizard 4 étapes)
**Labels :** `design` `maquettes` `sprint-0`
**Estimation :** 2 pts

**Objectif**
Maquetter le parcours de création d'un profil client B2B (wizard) ainsi que la fiche de suivi de ce client, puisque **un client = un ICP = une configuration** (voir CLAUDE.md, règle absolue #3).

**Écrans à concevoir :**

*Wizard de création (4 étapes)*
- [ ] Étape 1 — Informations client : nom, secteur, contact
- [ ] Étape 2 — Zone & ciblage : départements, codes NAF, tranche d'effectif
- [ ] Étape 3 — Profil ICP : description texte libre (utilisée pour l'embedding), mots-clés positifs / négatifs
- [ ] Étape 4 — Confirmation : résumé des critères saisis + bouton « Créer le client »

*Fiche profil complète*
- [ ] KPIs du client (prospects collectés, qualifiés, taux de conversion)
- [ ] Historique des campagnes lancées
- [ ] Coûts associés (API, enrichissement, etc.)

**Contraintes**
- Le formulaire doit permettre de saisir **tous** les champs de `criteres_ciblage` (voir #S0-4 et ARCHITECTURE.md) sans qu'aucun ne soit pré-rempli en dur pour un secteur donné
- Cohérence visuelle avec les maquettes de #S0-1

**Critères d'acceptance :**
- [ ] Wizard 4 étapes maquetté et navigable (au moins en export statique)
- [ ] Fiche profil complète avec toutes les sections listées ci-dessus
- [ ] Validé par l'équipe avant le démarrage du Sprint 1

---

### #S0-3 · Modélisation BDD — schéma entité-relation
**Labels :** `database` `conception` `sprint-0`
**Estimation :** 2 pts

**Objectif**
Concevoir le schéma de données complet (PostgreSQL + Qdrant) avant l'écriture du SQL en Sprint 1 (#1).

**Livrables :**
- [ ] Diagramme ERD — 8 tables (`clients`, `criteres_ciblage`, `icp_profiles`, `sources`, `campagnes`, `prospects`, `scores`, `appels`) avec relations et cardinalités. Voir `docs/ARCHITECTURE.md` pour la base de départ
- [ ] Liste des index critiques, justifiés un par un (ex. index sur `statut`, `score`, `departement`, `code_naf`, index trigram sur les champs texte recherchés)
- [ ] Validation des types de données : UUID pour les clés primaires, JSONB pour les champs flexibles, arrays PostgreSQL le cas échéant
- [ ] Schéma Qdrant — 2 collections (`icp_profiles`, `prospects_embeddings`), dimensions des vecteurs (768 pour nomic-embed-text v2), métrique de distance (cosine)

**Contraintes**
- Aucune valeur métier (codes NAF, secteur) ne doit apparaître dans le schéma lui-même — les critères de ciblage sont des données, stockées dans `criteres_ciblage` / `icp_profiles`, pas des colonnes fixes par secteur
- Le schéma doit prévoir les colonnes nécessaires à la conformité légale : `bloctel_ok`, `bloctel_verifie_le` (re-vérification 30 jours, voir `docs/LEGAL.md` et #35), champs de rétention RGPD (#36)

**Critères d'acceptance :**
- [ ] ERD exporté en PNG ou Mermaid, versionné dans le repo
- [ ] Toutes les FK documentées (table source, table cible, cardinalité)
- [ ] Validé par l'équipe avant écriture du SQL

---

### #S0-4 · Modéliser la configuration ICP générique (par client)
**Labels :** `ia` `icp` `conception` `sprint-0`
**Estimation :** 1 pt

**Livrables :**
- Formulaire/script de saisie ICP par client : `description_icp`, `codes_naf`, `effectif_min/max`, `anciennete_min_ans`, `departements`, `mots_cles_positifs/negatifs`
- Validation qu'**aucune** de ces valeurs n'est codée en dur ailleurs dans le code (agents, prompts, scripts)
- Pour le client pilote : renseigner un premier ICP concret (ex. garages indépendants — codes NAF 4520Z/4511Z/4531Z/4532Z, effectif 2-15, ancienneté 3 ans) comme donnée de test, pas comme valeur par défaut du produit

Le produit n'est pas verrouillé sur un secteur : l'ICP est une configuration par client, pas du code.

---

### #S0-5 · Valider stack + ouvrir tous les comptes API
**Labels :** `setup` `conception` `sprint-0`
**Estimation :** 1 pt

**Objectif**
Valider les choix techniques avec l'équipe (3 personnes) et ouvrir tous les comptes API nécessaires au pipeline, avant le démarrage du Sprint 1. Certains délais d'obtention sont longs : à lancer en tout premier.

**Actions :**
- [ ] Bloctel professionnel — ouvrir un compte sur bloctel.gouv.fr (⚠️ délai d'obtention 3-5 jours ouvrés, à démarrer en priorité absolue — voir `docs/LEGAL.md`)
- [ ] Tavily — ouvrir un compte (1000 requêtes/mois gratuites), récupérer la clé API
- [ ] API Sirene INSEE — créer une application sur `portail-api.insee.fr`, s'abonner à l'API Sirene 3.11 (plan « Accès public »), puis tester l'accès (endpoint `api-sirene/3.11/siret`, auth par header `X-INSEE-Api-Key-Integration`)
- [ ] Dropcontact — ouvrir un compte (24€/mois), récupérer la clé API
- [ ] Repo GitHub — créer/vérifier le repo et inviter les 3 collaborateurs de l'équipe
- [ ] `.env.example` — lister toutes les variables d'environnement nécessaires (clés API ci-dessus + connexions PostgreSQL/Qdrant/Ollama + `CLAUDE_API_KEY`)

**Contraintes**
- Aucune clé API ou secret ne doit être commité en clair — seul `.env.example` (sans valeurs réelles) est versionné
- Le choix du modèle Claude pour le scoring doit rester configurable (`settings.CLAUDE_SCORING_MODEL`), jamais codé en dur dans les prompts (voir CLAUDE.md, règle #6)

**Critères d'acceptance :**
- [ ] Les 4 comptes API (Bloctel, Tavily, Sirene INSEE, Dropcontact) sont ouverts et une clé/accès valide est confirmé pour chacun
- [ ] Le repo GitHub contient les 3 collaborateurs avec les droits appropriés
- [ ] `.env.example` est présent à la racine et couvre toutes les variables utilisées dans `docs/ARCHITECTURE.md`

---

## Sprint 1 — Fondations (Sem. 1-2) · 9 issues · 17 pts

### #1 · Créer docker-compose.yml (PostgreSQL 16 + Qdrant + Ollama)
**Labels :** `infrastructure` `docker` `sprint-1` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Fournir la stack Docker complète (PostgreSQL + Qdrant + Ollama) qui sert de socle à tout le reste du projet, en dev comme en prod.

**Fichiers à créer :**
- [ ] `docker-compose.yml` — services `postgres` (postgres:16-alpine, :5432), `qdrant` (qdrant/qdrant:latest, :6333/:6334), `ollama` (ollama/ollama:latest, :11434), `pgadmin` (profil `dev`), `metabase` (profil `monitoring`, voir #32)
- [ ] `docker-compose.prod.yml` — override qui lie les ports Postgres/Qdrant à `127.0.0.1` uniquement (sécurité VPS, voir #28)
- [ ] `docker/qdrant/config.yaml` — HNSW `m=16`, `ef_construct=100`, API key, niveau de log
- [ ] `.env.example` — toutes les variables listées dans `docs/ARCHITECTURE.md`
- [ ] `Makefile` — cibles `dev`, `prod`, `stop`, `psql`, `logs`, `backup`, `reset-db`

**Contraintes**
- Volumes persistants pour Postgres, Qdrant et les modèles Ollama (ne pas perdre les données entre `docker compose down`/`up`)
- Aucun secret réel dans `docker-compose.yml` — tout passe par `.env` (non versionné) et `.env.example` (versionné, sans valeurs)

**Critères d'acceptance :**
- [ ] `make dev` démarre tous les services sans erreur
- [ ] `curl localhost:6333/healthz` → OK
- [ ] `curl localhost:11434` → Ollama running
- [ ] `make prod` (avec l'override) n'expose pas les ports 5432/6333 en dehors de `127.0.0.1`

---

### #2 · Créer le schéma SQL PostgreSQL (8 tables + triggers + vue)
**Labels :** `database` `postgresql` `sprint-1` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Écrire le script SQL d'initialisation exécuté automatiquement au premier démarrage de PostgreSQL, à partir de l'ERD validé en Sprint 0 (#S0-3).

**Fichier :** `docker/postgres/init/01_schema.sql`
**Contenu :**
- [ ] Extensions : `uuid-ossp`, `pg_trgm`
- [ ] 8 tables : `clients`, `criteres_ciblage`, `icp_profiles`, `sources`, `campagnes`, `prospects`, `scores`, `appels` (voir ARCHITECTURE.md)
- [ ] Triggers `set_updated_at()` sur `clients`, `campagnes`, `prospects`
- [ ] Index critiques : statut, score, département, naf, bloctel, bloctel_verifie_le (utilisé par #35), trgm
- [ ] Vue `file_appel` avec filtre `bloctel_ok = TRUE`
- [ ] Données initiales table `sources` (5 entrées : `sirene_insee`, `tavily`, `pages_jaunes`, `dropcontact`, `manuel`)

**Contraintes**
- Aucune valeur métier (code NAF, secteur) codée en dur dans le schéma — `criteres_ciblage` reste la seule source de vérité pour l'ICP
- Les colonnes `bloctel_ok` (BOOL, nullable → 3 états) et `bloctel_verifie_le` (TIMESTAMPTZ) doivent respecter la sémantique légale de `docs/LEGAL.md` (Règle 5 : `NULL` = non vérifié = pas d'appel)

**Critères d'acceptance :**
- [ ] `make psql` + `\dt` → 8 tables présentes
- [ ] Vue `file_appel` requêtable sans erreur
- [ ] Ré-exécuter le script sur une base déjà initialisée ne casse rien (ou est explicitement non supporté et documenté)

---

### #3 · Configurer Ollama + nomic-embed-text v2 (embeddings CPU)
**Labels :** `ia` `embeddings` `sprint-1` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Mettre en place la génération d'embeddings 100% locale sur CPU (aucune API OpenAI, voir CLAUDE.md règle #5), utilisée par la couche 3 du scoring (#21) et par `scripts/init_icp.py` (#7).

**Fichiers :**
- [ ] Ollama dans docker-compose.yml avec volume modèles
- [ ] Script entrypoint qui `ollama pull nomic-embed-text` au démarrage (idempotent)
- [ ] `utils/embeddings.py` avec `async def get_embedding(text: str) -> list[float]`

**Contraintes**
- Modèle recommandé MVP : `nomic-embed-text` (137MB, 768 dims, Apache 2.0). `qwen3-embedding` (1024 dims) reste une alternative si besoin de meilleure précision multilingue
- Le nom du modèle doit être configurable, pas codé en dur partout où il est utilisé

**Critères d'acceptance :**
- [ ] `curl -X POST localhost:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'` → vecteur 768 dims
- [ ] `utils/embeddings.py` retourne une liste de 768 floats
- [ ] Temps de réponse < 500ms sur CPU OVH

---

### #4 · Initialiser collections Qdrant + utils/db.py
**Labels :** `database` `qdrant` `sprint-1` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Fournir la couche d'accès aux données (PostgreSQL + Qdrant) utilisée par tous les nodes du graphe LangChain (#23) et les scripts.

**Fichier :** `utils/db.py`
**Fonctions à implémenter :**
- [ ] `get_pg_pool()` — pool asyncpg singleton
- [ ] `get_qdrant()` — AsyncQdrantClient singleton
- [ ] `_ensure_collections()` — crée si absent, idempotent (`prospects_embeddings` et `icp_profiles`, 768 dims, cosine, HNSW m=16)
- [ ] `upsert_prospect(data: dict) -> str` — ON CONFLICT siret
- [ ] `get_file_appel(limit: int) -> list[dict]`
- [ ] `save_score(prospect_id, score_data)`
- [ ] `upsert_prospect_embedding(prospect_id, embedding, payload)`
- [ ] `search_similar_prospects(query_embedding, top_k, departement?)`
- [ ] `get_icp_embedding(icp_id) -> list[float]`

**Contraintes**
- Tout est async (`asyncpg`, `AsyncQdrantClient`) — voir CLAUDE.md règle #8

**Critères d'acceptance :**
- [ ] Premier lancement → 2 collections créées dans Qdrant
- [ ] Deuxième lancement → pas d'erreur (idempotent)
- [ ] `upsert_prospect` fonctionne (test round-trip)

---

### #5 · Créer modèles Pydantic v2 (Prospect, Score, EtatAgent)
**Labels :** `modèles` `pydantic` `sprint-1` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Modéliser en Pydantic v2 (CLAUDE.md règle #7) les structures de données centrales du pipeline : le prospect, son score, et l'état du graphe LangChain.

**Fichiers :** `models/prospect.py`, `models/score.py`, `graph/state.py`
**Validators obligatoires :**
- [ ] `telephone` → normalisation E.164 via `phonenumbers`
- [ ] `email` → regex + blacklist domaines (pagesjaunes.fr, laposte.net, noreply., contact@, info@, mairie. — voir SCORING.md)
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

**Objectif**
Poser l'arborescence complète du projet Python avant que les autres issues du Sprint 1 ne commencent à écrire du code, pour éviter les conflits de structure.

**Créer l'arborescence complète** (voir ARCHITECTURE.md) : `main.py`, `requirements.txt`, `.env.example`, `Makefile`, `config/`, `agents/`, `graph/`, `models/`, `utils/`, `prompts/`, `scripts/`, `tests/`, `docker/`.

**Contraintes**
- Chaque fichier créé à ce stade peut être un stub (docstring + `pass`/`TODO`), l'implémentation réelle est portée par les issues dédiées

**Critères d'acceptance :**
- [ ] `python main.py --help` fonctionne
- [ ] `pip install -r requirements.txt` sans erreur
- [ ] Tous les imports résolus

---

### #7 · Configurer profil ICP + script init_icp.py
**Labels :** `ia` `icp` `sprint-1` `priorité-haute`
**Estimation :** 1 pt

**Objectif**
Fournir le script qui génère l'embedding d'un ICP client (à partir de sa `description_icp` en langage naturel) et le stocke dans Qdrant, pour alimenter la couche 3 du scoring (#21).

**Fichiers :** `config/icp_seed_example.py` (exemple illustratif, pas un défaut produit), `scripts/init_icp.py --client-id <uuid>`

**Contraintes**
- Un client = un ICP = une configuration (CLAUDE.md règle #3) : le script ne doit jamais écrire de valeur ICP en dur, tout vient de `criteres_ciblage`
- Doit pouvoir être ré-exécuté si le client modifie sa `description_icp` (ré-upsert, pas de doublon de point Qdrant)

**Critères d'acceptance :**
- [ ] `python scripts/init_icp.py --client-id <uuid>` → embedding inséré dans Qdrant
- [ ] Collection `icp_profiles` contient 1 vecteur
- [ ] Une seconde exécution pour le même client met à jour le vecteur existant plutôt que d'en créer un second

---

### #8 · Tests unitaires modèles Pydantic
**Labels :** `tests` `sprint-1` `priorité-moyenne`
**Estimation :** 1 pt

**Objectif**
Couvrir par des tests unitaires tous les validators Pydantic critiques introduits dans #5, avant de bâtir le reste du pipeline dessus.

**Fichier :** `tests/test_models.py`
**20 cas à tester :**
- [ ] Téléphone : formats variés → E.164, numéro invalide → `ValidationError`
- [ ] Email : formats valides/invalides, domaines blacklistés → `None`
- [ ] SIRET : 14 chiffres valides, formats invalides → `ValidationError`
- [ ] `to_db_dict()` : types compatibles `asyncpg`

**Critères d'acceptance :**
- [ ] `pytest tests/test_models.py` → 100% pass

---

### #9 · Script smoke_test.py
**Labels :** `tests` `infrastructure` `sprint-1` `priorité-moyenne`
**Estimation :** 1 pt

**Objectif**
Fournir un script unique qui vérifie en une commande que toute la stack (locale ou VPS) est opérationnelle, utilisé en dev comme en prod (voir #28).

**Fichier :** `scripts/smoke_test.py`
**Checks :** PostgreSQL (8 tables) + Qdrant (2 collections) + Ollama (modèle chargé) + embedding test (768 dims) + round-trip BDD (insert/lecture/suppression d'un prospect de test)

**Critères d'acceptance :**
- [ ] Sort en code 0 (vert) si tout est OK, code ≠ 0 sinon avec message explicite par check
- [ ] Passe en vert en local ET sur VPS OVH

---

## Sprint 2 — Collecte & Enrichissement (Sem. 3-4) · 9 issues · 17 pts

### #10 · Implémenter sirene_agent.py
**Labels :** `collecte` `sirene` `sprint-2` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Premier node de collecte du pipeline : interroger l'API Sirene INSEE pour récupérer les établissements correspondant à l'ICP de la campagne en cours (départements + codes NAF chargés par `init_campagne`, #11), et les convertir en objets `Prospect` (#5).

**Endpoint INSEE (NAF et DEPT viennent de `criteres_ciblage`, jamais codés en dur) :**
```
GET https://api.insee.fr/api-sirene/3.11/siret
?q=activitePrincipaleEtablissement:{NAF}
  AND codePostalEtablissement:{DEPT}*
  AND etatAdministratifEtablissement:A
&nombre=100&debut=0

Header : X-INSEE-Api-Key-Integration: {INSEE_API_KEY}
```
> ⚠️ Nouveau portail `portail-api.insee.fr` : base `api-sirene/3.11` (et non
> l'ancien `entreprises/sirene/V3.11`) + auth par header
> `X-INSEE-Api-Key-Integration` (et non OAuth2 bearer). Vérifié le 26/07/2026.
**Fonctions :**
- [ ] `fetch_sirene(etat, api_key)` — node LangChain, itère sur tous les couples (département, code NAF) de l'ICP de la campagne
- [ ] `_fetch_etablissements(client, headers, dept, naf, limit)` — pagination via `debut`/`nombre`
- [ ] `_parser_etablissement(etab)` — parse la réponse JSON INSEE → `Prospect` (mapping `effectif_code`/`effectif_estime`, `code_naf`, `date_creation`, adresse)

**Gestion :** Rate limit 429 → sleep 2s + retry (max 3) · Pagination auto · respect du quota INSEE (30 req/min)

**Contraintes**
- Filtre `etatAdministratifEtablissement:A` obligatoire (établissements actifs uniquement)
- Aucun code NAF ni département codé en dur — uniquement ceux de `criteres_ciblage` de la campagne (CLAUDE.md règle #3)

**Critères :** 50 prospects (ICP pilote, dept. 75 en exemple) en < 30s · 100% SIRET valides

---

### #11 · Node init_campagne — charger critères depuis BDD
**Labels :** `collecte` `database` `sprint-2` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Premier node du graphe LangChain (#23) : charger, pour une campagne donnée, les critères de ciblage du client depuis la BDD, afin qu'aucune valeur ICP ne soit jamais codée en dur dans les nodes suivants (collecte #10, nettoyage #14, scoring #19-21).

**Fichier :** `graph/workflow.py` (premiers nodes)
**Implémentation :**
- [ ] Node `init_campagne(etat: EtatAgent) -> EtatAgent` : lit `campagnes.critere_id` puis charge la ligne `criteres_ciblage` correspondante et le vecteur ICP associé (`icp_profiles.qdrant_point_id`)
- [ ] Peuple `EtatAgent` avec l'objet `CriteresCiblage` complet, utilisé par tous les nodes suivants
- [ ] Gestion d'erreur explicite si `campagne_id` inconnu ou `criteres_ciblage` manquant (fail fast)

**Fixtures SQL de test incluses** (client pilote générique + critères + campagne — nom de test neutre, pas lié à un secteur)

**Critères d'acceptance :**
- [ ] `init_campagne` retourne un `EtatAgent` avec tous les critères de la campagne correctement chargés
- [ ] Erreur claire et explicite si la campagne ou ses critères n'existent pas

---

### #12 · Tests intégration Sirene (50 prospects réels)
**Labels :** `tests` `intégration` `sprint-2` `priorité-moyenne`
**Estimation :** 1 pt

**Objectif**
Valider `sirene_agent.py` (#10) contre la vraie API Sirene INSEE, avec de vraies données, sans dépendre d'un mock qui masquerait un changement de format côté INSEE.

**Fichier :** `tests/test_sirene.py`
**Contenu :**
- [ ] Récupération de 50 prospects réels via l'API (ICP de test, départements + codes NAF réels)
- [ ] Vérification : 100% des SIRET retournés sont valides
- [ ] Vérification de la pagination sur un volume > 100 résultats
- [ ] Vérification du comportement sur rate limit 429 (retry, max 3 tentatives)

**Marker pytest :** `@pytest.mark.integration` (exclu du CI auto — ces tests appellent une vraie API externe et consomment le quota INSEE)

**Critères d'acceptance :**
- [ ] `pytest tests/test_sirene.py -m integration` → 50 prospects réels récupérés, 100% SIRET valides
- [ ] `pytest tests/` (sans le marker `integration`) ignore ces tests

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
**Contraintes :** sources légales uniquement (CLAUDE.md règle #2) — pas de scraping de réseaux sociaux personnels ni de bases achetées (voir `docs/LEGAL.md`) · respecter le quota Tavily (1000 req/mois gratuit), logger la consommation (#18)
**Critères :** > 40% taux enrichissement téléphone

---

### #14 · Implémenter nettoyage_agent.py
**Labels :** `nettoyage` `sprint-2` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Nettoyer et filtrer les prospects avant scoring, en appliquant les exclusions **configurables par client** (jamais codées en dur, CLAUDE.md règle #4) et les contraintes légales (Bloctel).

**Actions :**
- [ ] Dédup SIRET (marque `doublon = TRUE`, ne supprime pas)
- [ ] Normalisation E.164
- [ ] Vérification Bloctel (#15)
- [ ] Exclusions client (`mots_cles_negatifs`, matching par mot entier, pas sous-chaîne — voir #19)
- [ ] Filtre effectif hors cible ICP

**Contraintes**
- Aucune liste de marques/groupes codée en dur — uniquement `criteres_ciblage.mots_cles_negatifs` du client
- Un numéro `bloctel_ok = NULL` (non vérifié) doit être traité comme non-appelable, jamais comme « appelable par défaut »

**Critères d'acceptance :**
- [ ] Aucun doublon SIRET dans `file_appel`
- [ ] Aucun prospect matchant une exclusion ICP de test ne reste `qualifie`
- [ ] 100% des prospects transmis au scoring ont un statut Bloctel connu

---

### #15 · Implémenter utils/bloctel.py ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `bloctel` `compliance` `sprint-2` `priorité-haute`
**Estimation :** 2 pts
**⚠️ Lire LEGAL.md avant de commencer.**

**Objectif**
Implémenter la vérification Bloctel, obligation légale non négociable avant tout appel (CLAUDE.md règle #1, amende jusqu'à 75 000€ en cas de manquement).

**Fonction :** `verifier_batch(numeros: list[str]) -> dict[str, bool]`
- [ ] Format E.164 obligatoire en entrée · batch de max 10 000 numéros par requête
- [ ] Retry sur timeout (max 3 tentatives)
- [ ] Si l'API est indisponible : ne jamais fallback vers « appelable par défaut » — logger un warning critique et laisser `bloctel_ok = NULL`

**Persistance**
- [ ] Met à jour `prospects.bloctel_ok` et `prospects.bloctel_verifie_le`
- [ ] Insère une ligne d'audit dans `bloctel_verifications` (table déjà présente dans `docker/postgres/init/01_schema.sql`) : `prospect_id`, `telephone`, `resultat`, `reference_bloctel` — trace de preuve en cas de contrôle

**Contraintes**
- Trois états pour `bloctel_ok` : `TRUE` (appelable), `FALSE` (interdit, exclu de `file_appel`), `NULL` (non vérifié, également exclu)
- Prérequis de #14 (nettoyage_agent.py), ré-exécuté tous les 30 jours par le job #35

**Critères :** 100 numéros en < 5s · bloctel_ok=False exclu de file_appel · colonne `bloctel_verifie_le` posée pour permettre la re-vérification à 30 jours (voir #35) · chaque vérification laisse une trace dans `bloctel_verifications`

---

### #16 · Intégrer Dropcontact (emails B2B)
**Labels :** `enrichissement` `email` `sprint-2` `priorité-moyenne`
**Estimation :** 2 pts

**Objectif**
Compléter l'enrichissement email (#13) via Dropcontact quand Tavily/Crawl4AI n'ont rien trouvé, en respectant les conditions de coût et de conformité RGPD (`docs/LEGAL.md`).

**Fichier :** `utils/dropcontact.py`
**Flow :** POST /batch → request_id → polling 5s → upsert email
**Condition :** email=None ET nom_dirigeant≠None ET site_web≠None

**Contraintes**
- Dropcontact génère l'email algorithmiquement (prénom.nom@entreprise.fr), certifié RGPD, hébergé en Europe — ne pas appeler ce service hors de la condition ci-dessus
- Logger le nombre d'appels Dropcontact par campagne pour suivre le coût (#18)

**Critères d'acceptance :**
- [ ] Seuls les prospects respectant la condition d'appel déclenchent une requête Dropcontact
- [ ] Le taux d'enrichissement email global atteint la cible PRD (≥20%)

---

### #17 · Test E2E pipeline collecte (100 prospects, ICP pilote)
**Labels :** `tests` `intégration` `sprint-2` `priorité-haute`
**Estimation :** 1 pt

**Objectif**
Valider bout-en-bout la partie « collecte + enrichissement + nettoyage » du pipeline (#10, #11, #13, #14, #15, #16) sur un volume représentatif, avant d'y brancher le scoring en Sprint 3.

**Cibles :** ≥40% tél · ≥20% email · 0 doublon · 0 prospect matchant une exclusion ICP · Bloctel 100% (aucun `bloctel_ok = NULL` en sortie) · < 10 min pour 100 prospects

**Marker pytest :** `@pytest.mark.integration` (exclu du CI auto)

**Critères d'acceptance :**
- [ ] Toutes les cibles ci-dessus sont vérifiées par des assertions automatiques
- [ ] Rapport de run (compteurs par cible) loggé ou exporté pour revue par l'équipe

---

### #18 · Métriques par source
**Labels :** `monitoring` `sprint-2` `priorité-basse`
**Estimation :** 1 pt

**Objectif**
Donner de la visibilité sur la performance et le coût de chaque source de données (Sirene, Tavily, Dropcontact, etc.), pour arbitrer plus tard (ex. ajouter Pappers si le taux d'enrichissement est insuffisant).

**Fichier :** `utils/metrics.py` · Mise à jour table `sources` (`derniere_collecte`, `nb_prospects`) · métriques par source : nombre de prospects apportés, taux de succès, quota consommé le cas échéant

**Critères d'acceptance :**
- [ ] Après un run de campagne, la table `sources` reflète des compteurs à jour pour chaque source utilisée
- [ ] Les métriques sont consultables sans requête SQL manuelle

---

## Sprint 3 — Scoring & Pipeline (Sem. 5-6) · 9 issues · 17 pts

### #19 · Scoring règles métier Python générique (35%)
**Labels :** `scoring` `sprint-3` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Implémenter la 1ʳᵉ couche du scoring hybride (35% du score final) : un barème Python déterministe, entièrement paramétré par l'ICP de la campagne — aucune constante métier codée en dur.

**Fichier :** `agents/scoring_agent.py` → `_score_regles(prospect, criteres) -> int`
**Barème (détail complet dans SCORING.md) :**
- [ ] Contact (max 35 pts) : téléphone (+25), email non blacklisté (+10)
- [ ] Effectif (max 20 pts) via `_score_effectif(effectif, effectif_min, effectif_max)`
- [ ] Ancienneté (max 15 pts) via `_score_anciennete(date_creation, anciennete_min_ans)`
- [ ] Présence digitale (max 10 pts), Géographie (max 10 pts), Mots-clés positifs (max 10 pts)
- [ ] Pénalités : `_matche_exclusion` (mot entier) → score forcé à 0 · aucun contact → -20 · NAF hors cible → -30

**Voir SCORING.md** pour le barème complet — toutes les valeurs (effectif, ancienneté, exclusions) viennent de `criteres_ciblage`, aucune constante métier codée en dur
**Critères :** `_score_effectif` et `_score_anciennete` sont des fonctions pures testées indépendamment (pas de dict jamais lu comme dans une version antérieure du barème) · `_matche_exclusion` teste par mot entier, pas par sous-chaîne

---

### #20 · Prompts Claude scoring LLM générés dynamiquement depuis l'ICP (45%)
**Labels :** `scoring` `llm` `prompt-engineering` `sprint-3` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Implémenter la 2ᵉ couche du scoring hybride (45% du score final, la plus lourde) : un scoring Claude dont le prompt système est **généré dynamiquement** depuis le profil du client et son ICP, pour que le même agent puisse scorer n'importe quel secteur sans changer une ligne de code.

**Fichiers :** `prompts/scorer_system.txt.j2` + `prompts/scorer_user.txt.j2` (templates Jinja, rendus depuis `clients` + `criteres_ciblage`, pas de texte figé)
**Implémentation :**
- [ ] Le prompt système intègre `client.produit_vendu`, `criteres.description_icp`, effectif, ancienneté — jamais de secteur/NAF codé en dur dans le texte
- [ ] Le prompt utilisateur exige un JSON strict (`score`, `justification`, `signaux_positifs`, `signaux_negatifs`, `priorite`)
- [ ] Parsing robuste du JSON avec fallback neutre (`score: 50`) si le parsing échoue
- [ ] Prompt caching activé sur le system prompt rendu (`cache_control: ephemeral`)

**Voir SCORING.md** pour les templates complets
**Contraintes :** modèle Claude configurable via `settings.CLAUDE_SCORING_MODEL`, jamais codé en dur (CLAUDE.md règle #6)
**Critères :** JSON valide 100% · < 0.003€/prospect · justification > 20 mots · prompt caching activé sur le system prompt rendu (économie ~90% après le 1er appel de la campagne) · modèle Claude configurable via `settings.CLAUDE_SCORING_MODEL`, jamais codé en dur

---

### #21 · Scoring embeddings ICP Qdrant (20%)
**Labels :** `scoring` `embeddings` `sprint-3` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Implémenter la 3ᵉ couche du scoring hybride (20% du score final) : la similarité cosinus entre l'embedding du prospect et l'embedding de l'ICP du client, tous deux générés localement via Ollama.

**Fichier :** `agents/scoring_agent.py` → fonction `_score_embedding(prospect, icp_embedding, ollama_client, qdrant_client) -> float`
**Algorithme (détail complet dans SCORING.md, Couche 3) :**
- [ ] Construire un texte de description générique du prospect (nom, activité, effectif, ville/département, ancienneté, présence site web)
- [ ] Générer l'embedding du prospect via `utils/embeddings.py` (#3)
- [ ] Charger l'embedding ICP du client via `get_icp_embedding` (#4), généré par `scripts/init_icp.py` (#7)
- [ ] Calculer la similarité cosinus (`numpy`) entre les deux vecteurs
- [ ] Stocker le vecteur du prospect dans Qdrant
- [ ] Retourner un score `[0-100]`

**Critères :** < 200ms/prospect sur CPU OVH · le score retourné est toujours dans `[0, 100]` · le vecteur du prospect est bien persisté dans Qdrant après chaque appel

---

### #22 · Agrégation score final + historique BDD
**Labels :** `scoring` `database` `sprint-3` `priorité-haute`
**Estimation :** 1 pt

**Objectif**
Combiner les 3 couches de scoring (#19 règles, #20 LLM, #21 embedding) en un score final, déterminer le statut du prospect, et persister l'historique complet pour l'audit qualité (#27).

**Formule :** `round(0.35×règles + 0.45×llm + 0.20×embedding)` — poids stockés dans `campagnes.config_scoring` (JSONB), ajustables **par campagne**, jamais globalement
**Voir SCORING.md** pour l'implémentation complète

**Implémentation :** `agreger_et_sauvegarder(...)` — calcule `score_final` et le statut (`qualifie` ≥60, `invalide` <30, `nouveau` sinon), met à jour `prospects`, insère une ligne dans `scores` (historique), incrémente `campagnes.prospects_qualifies` si qualifié

**Critères d'acceptance :**
- [ ] `score_final` toujours dans `[0, 100]`
- [ ] Chaque scoring génère une ligne d'historique dans `scores`
- [ ] Les seuils de statut (60 / 30) sont respectés exactement

---

### #23 · Assembler graphe LangChain complet (6 nodes)
**Labels :** `workflow` `langchain` `sprint-3` `priorité-haute`
**Estimation :** 3 pts

**Objectif**
Assembler l'ensemble des nodes développés depuis le Sprint 2 en un graphe LangChain unique, exécutable de bout en bout pour une campagne.

**Fichier :** `graph/workflow.py`
**Nodes :** init_campagne (#11) → fetch_sirene (#10) → enrichir (#13, #16) → nettoyer (#14, #15) → scorer (#19, #20, #21, #22) → sauvegarder

**Implémentation :**
- [ ] Câblage des 6 nodes via l'API graphe de LangChain, état partagé `EtatAgent` (#5)
- [ ] Gestion des erreurs par node (logger + décider explicitement de continuer ou stopper)
- [ ] **Fallback obligatoire** : Claude down → scoring règles uniquement (`score_final = 0.80×règles + 0.20×embedding`, voir SCORING.md)

**Critères :** < 15 min pour 100 prospects bout-en-bout · simulation d'une panne Claude API → le pipeline se termine quand même

---

### #24 · Créer main.py CLI argparse
**Labels :** `cli` `sprint-3` `priorité-moyenne`
**Estimation :** 1 pt

**Objectif**
Fournir le point d'entrée unique du pipeline (déjà stubé en #6), qui pilote le graphe LangChain (#23) via `argparse`, paramétré par client et par campagne — jamais par des constantes en dur.

**Usage :**
```bash
python main.py --campagne-id {uuid}
python main.py --depts 75,92 --naf 4520Z --limit 200
python main.py --depts 75 --limit 10 --dry-run
python main.py --list-campagnes
```

**Critères d'acceptance :**
- [ ] Les 4 usages ci-dessus fonctionnent sans erreur
- [ ] `--dry-run` ne modifie aucune table
- [ ] Messages d'erreur clairs si `--campagne-id` invalide ou arguments manquants

---

### #25 · Configurer LangSmith
**Labels :** `monitoring` `sprint-3` `priorité-basse`
**Estimation :** 1 pt

**Objectif**
Tracer chaque exécution du graphe LangChain (#23) — en particulier les appels Claude du scoring (#20) — pour surveiller la latence, les erreurs et le coût par client.

**Configuration :** variables `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_PROJECT=prospection-b2b` · `utils/logger.py` initialise LangSmith au démarrage · `client_id`/`campagne_id` dans les métadonnées de trace

**Critères :** Traces visibles sur smith.langchain.com · Coût par run visible et filtrable par client

---

### #26 · Tests unitaires scoring (20 cas + mock Claude)
**Labels :** `tests` `scoring` `sprint-3` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Couvrir par des tests unitaires (mock Claude, pas d'appel API réel) les 3 couches du scoring (#19, #20, #21) et leur agrégation (#22), avec un ICP de test générique — jamais garage-spécifique, pour prouver que le scoring fonctionne pour n'importe quel secteur cible.

**Fichier :** `tests/test_scoring.py`
**Cas (avec un ICP de test générique, pas garage-spécifique) :**
- Prospect qui matche parfaitement l'ICP de test → score > 75
- Prospect en périphérie de l'ICP (effectif/ancienneté limites) → score < 30
- Prospect matchant un `mots_cles_negatifs` de test → score = 0
- Prospect qualifié sans email (téléphone seul) → score 55-70
- Mock Claude indisponible → fallback règles
- Deux ICP de test différents (secteurs distincts) sur les mêmes prospects → scores cohérents avec chaque ICP respectif

**Contraintes**
- Claude est systématiquement mocké dans ces tests (pas de coût, pas de dépendance réseau)
- Les fixtures d'ICP de test doivent couvrir au moins deux secteurs différents, pour prouver la généricité du scoring (CLAUDE.md règle #3)

**Critères d'acceptance :**
- [ ] `pytest tests/test_scoring.py -v` → 100% de réussite sur les 20 cas
- [ ] Aucun test ne dépend d'une valeur métier codée en dur (NAF, secteur) dans le code de scoring

---

### #27 · Audit qualité scores (100 prospects réels)
**Labels :** `qualité` `validation` `sprint-3` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Vérifier que le scoring hybride (#19-22) produit des résultats fiables sur des données réelles, avant la première campagne en production (#30). Cible PRD : accord humain/score ≥ 75%.

**Méthodologie :**
- [ ] Exécuter le pipeline complet sur 100 prospects réels (ICP du client pilote)
- [ ] Export CSV avec `score_final`, les 3 sous-scores, `justification_llm`, `signaux_positifs/negatifs`
- [ ] 20 prospects revus manuellement (accord/désaccord avec le score IA, sans voir le score avant révision)
- [ ] Calculer le taux d'accord humain/score

**Si accord < 75% :** ajuster les poids `config_scoring` (JSONB) au niveau de la campagne concernée, jamais globalement, puis ré-auditer

**Critères :** Export CSV · 20 revus manuellement · accord humain > 75% (ou plan d'ajustement documenté)

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

**Contraintes**
- Aucun secret (`.env`) commité — transféré au VPS hors git
- Les jobs légaux (#35 re-vérification Bloctel, #36 purge RGPD) doivent être déployés en même temps que la stack, pas après

**Critères d'acceptance :**
- [ ] Stack accessible et fonctionnelle uniquement depuis le VPS (pas de port DB exposé publiquement)
- [ ] `smoke_test.py` vert sur le VPS
- [ ] Premier backup automatique confirmé dans `/opt/backups/`

---

### #29 · Configurer cron campagnes automatiques
**Labels :** `automatisation` `sprint-4` `priorité-moyenne`
**Estimation :** 1 pt

**Objectif**
Automatiser le lancement hebdomadaire des campagnes et la sauvegarde de la base, pour que le pipeline tourne sans intervention manuelle une fois en production (#28).

**Crontab :**
```bash
0 6 * * 1 cd /opt/prospection_b2b && python main.py --campagne-id {uuid} >> /var/log/prospection_b2b.log 2>&1
0 2 * * * docker exec prospection_b2b_postgres pg_dump -U scraper prospection_b2b | gzip > /opt/backups/$(date +%Y%m%d).sql.gz
```

**Actions**
- [ ] `scripts/run_campagne.sh` en wrapper : gère le logging, le code retour, et alerte (log critique) en cas d'échec
- [ ] Rotation des logs et des backups — pas de purge manuelle

**Contraintes**
- Le `campagne-id` par cron reste propre à chaque client actif — pas de campagne générique codée en dur (CLAUDE.md règle #3)
- Un échec du run hebdomadaire doit être visible (log + alerte), pas silencieux

**Critères d'acceptance :**
- [ ] La campagne se lance automatiquement chaque lundi à 6h sans intervention manuelle
- [ ] Un backup PostgreSQL compressé est généré chaque nuit à 2h dans `/opt/backups/`

---

### #30 · 🚀 Première campagne réelle — 500 prospects (client pilote)
**Labels :** `campagne` `production` `sprint-4` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Lancer la toute première campagne réelle en production pour le client pilote, sur un volume de 500 prospects — validation grandeur nature de tout le pipeline (#1 à #28) avant de généraliser à d'autres clients.

**Config :** ICP du client pilote (ex. garages IDF : depts 75,92,93,94, NAF 4520Z,4511Z,4531Z,4532Z) · limit 500 — config lue depuis `criteres_ciblage`, pas en dur dans le script

**Déroulé**
- [ ] Vérifier que le compte Bloctel professionnel est actif et à jour (#S0-5)
- [ ] Lancer `python main.py --campagne-id {uuid}` en production (#28)
- [ ] Suivre l'exécution via LangSmith (#25)
- [ ] Export CSV des prospects qualifiés en fin de run

**Contraintes**
- Aucun appel ne doit être passé sur un numéro dont `bloctel_ok` n'est pas strictement `TRUE`
- Si les cibles ne sont pas atteintes, documenter l'écart avant de relancer

**Objectifs :** 200+ tél (40%) · 100+ emails (20%) · 150+ qualifiés · export CSV livré à l'équipe commerciale

---

### #31 · Synchroniser prospects qualifiés → Airtable
**Labels :** `crm` `airtable` `sprint-4` `priorité-haute`
**Estimation :** 2 pts

**Objectif**
Donner à l'équipe commerciale une vue Airtable des prospects qualifiés, synchronisée automatiquement, sans qu'elle ait besoin d'accéder directement à PostgreSQL.

**Fichier :** `utils/airtable_sync.py`
**Comportement :**
- [ ] Upsert sur SIRET — un prospect déjà présent est mis à jour, pas dupliqué
- [ ] Sync bidirectionnelle du statut — les actions du commercial (RDV/Refus/Absent) redescendent vers `prospects.statut`/`appels`
- [ ] Nouveaux qualifiés seulement — ne pousse que les prospects `statut = 'qualifie'`

**Contraintes**
- Respecter le rate limit de l'API Airtable (batchs)
- Ne synchroniser que les champs nécessaires au commercial (pas `raw_data`)

**Critères d'acceptance :**
- [ ] Un prospect qualifié apparaît dans Airtable après un run de campagne
- [ ] Un changement de statut fait dans Airtable se reflète en base après le prochain sync
- [ ] Aucun doublon créé sur des runs successifs

---

### #32 · Installer Metabase sur VPS (dashboard KPIs)
**Labels :** `monitoring` `metabase` `sprint-4` `priorité-moyenne`
**Estimation :** 2 pts

**Objectif**
Donner au client B2B un dashboard KPIs sans dépendance à un accès SQL direct, hébergé sur le même VPS (profil `monitoring` du docker-compose, #1).

**Déploiement :** service `metabase` activé (port 3000) · connexion Metabase → PostgreSQL (lecture seule recommandée)

**6 questions :** répartition par statut · score moyen par département · taux d'enrichissement par campagne · évolution du volume de prospects dans le temps · top 10 par score · KPIs de campagne (collectés, qualifiés, appels, RDV)

**Critères d'acceptance :**
- [ ] Les 6 questions sont accessibles depuis un dashboard Metabase unique
- [ ] Les chiffres affichés correspondent à ceux obtenus par requête SQL directe

---

### #33 · Rapport hebdomadaire automatique (Brevo)
**Labels :** `reporting` `sprint-4` `priorité-basse`
**Estimation :** 1 pt

**Objectif**
Envoyer chaque semaine un résumé automatique des métriques au client B2B, sans intervention manuelle.

**Fichier :** `scripts/rapport_hebdo.py` · Cron lundi 8h
**Contenu du rapport (par client) :** prospects collectés dans la semaine · taux d'enrichissement tél/email · % qualifiés et score moyen · appels passés et RDV obtenus
**Envoi :** via Brevo (template email + API)

**Critères d'acceptance :**
- [ ] Le script génère et envoie un email par client actif, avec les bonnes métriques de la semaine écoulée

---

### #34 · Rétrospective MVP + plan Phase 2
**Labels :** `planning` `sprint-4` `priorité-haute`
**Estimation :** 1 pt

**Objectif**
Clore le MVP (9 semaines) en comparant les résultats réels aux cibles définies dans le PRD, et préparer la Phase 2.

**Métriques à comparer vs cibles** (voir PRD.md, section 6) : prospects collectés/semaine, taux enrichissement tél/email, % qualifiés et score moyen, accord humain/score IA, coût/prospect qualifié, durée pipeline, taux appels → RDV

**Décisions Phase 2 à trancher :** agent vocal (Retell AI), mailing automatique (Brevo), interface web self-service ICP, retour d'expérience sur le barème générique appliqué au premier client pilote

**Critères d'acceptance :**
- [ ] Un document de rétrospective compare chaque métrique cible vs réel
- [ ] Les décisions Phase 2 sont actées avec un propriétaire et un horizon indicatif

---

### #35 · Job de re-vérification Bloctel (30 jours) ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `bloctel` `compliance` `automatisation` `sprint-4` `priorité-haute`
**Estimation :** 1 pt
**⚠️ Lire LEGAL.md → Règle 5.**

**Objectif**
Automatiser la re-vérification Bloctel périodique : un numéro vérifié il y a plus de 30 jours ne doit plus être appelable sans re-vérification (obligation légale, amende jusqu'à 75 000€). Ce point n'était couvert par aucune tâche dans le plan initial — corrigé ici suite à l'audit de conformité.

**Actions :**
- [ ] Script `scripts/reverifier_bloctel.py` : sélectionne les prospects avec `bloctel_verifie_le` absent ou > 30 jours et appelables (statut qualifié/nouveau)
- [ ] Réutilise `verifier_batch` (#15) et journalise chaque re-vérification dans `bloctel_verifications` (table d'audit déjà présente dans `docker/postgres/init/01_schema.sql`)
- [ ] Repasse `bloctel_ok = NULL` tant que non re-vérifié (donc exclu de `file_appel` — la vue filtre déjà sur `bloctel_verifie_le > NOW() - INTERVAL '30 days'`)
- [ ] Cron quotidien (`crontab` ou `make cron-bloctel`)
- [ ] Log du nombre de prospects re-vérifiés / repassés en attente

**Contraintes**
- Ce job doit être déployé en même temps que la stack de production (#28), pas après — obligation légale dès la mise en service

**Critères d'acceptance :**
- [ ] Un prospect avec `bloctel_verifie_le` > 30 jours disparaît de `file_appel` tant qu'il n'est pas re-vérifié
- [ ] Le job tourne sans intervention manuelle
- [ ] Chaque re-vérification laisse une trace dans `bloctel_verifications`

---

### #36 · Job de purge RGPD automatique ⚠️ LÉGAL OBLIGATOIRE
**Labels :** `légal` `rgpd` `compliance` `automatisation` `sprint-4` `priorité-haute`
**Estimation :** 1 pt
**⚠️ Lire LEGAL.md → Durée de conservation.**

**Objectif**
Automatiser l'application de la politique de rétention RGPD (invalides 6 mois, qualifiés non convertis 3 ans, appels 1 an, logs 3 mois) — documentée dans LEGAL.md mais sans job pour l'appliquer jusqu'ici. Corrigé ici suite à l'audit de conformité.

**Actions :**
- [ ] Script `scripts/purge_rgpd.py` appliquant les 4 règles de rétention
- [ ] Anonymisation ou suppression selon le type de donnée (voir LEGAL.md)
- [ ] Vérifier systématiquement `oppositions_rgpd` avant toute action (un SIRET en opposition ne doit plus jamais être recontacté) — table déjà présente dans le schéma
- [ ] Journal d'audit des suppressions dans `purge_rgpd_log` (`table_cible`, `nb_lignes`, `motif`, déjà présent dans le schéma)
- [ ] Cron quotidien

**Contraintes**
- Ce job doit être déployé en même temps que la stack de production (#28), pas après
- Aucune purge manuelle : uniquement via ce job récurrent (CLAUDE.md règle #9)

**Critères d'acceptance :**
- [ ] Aucun prospect invalide de plus de 6 mois en base après un run
- [ ] Journal d'audit consultable via `purge_rgpd_log`

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
