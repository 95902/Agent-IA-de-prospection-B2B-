# Rétrospective MVP + Plan Phase 2 — issue #39

> **Date :** 23 août 2026 · **Périmètre :** Sprints 0 → 4 (MVP 9 semaines)
> **État du dépôt au moment de la rédaction :** `origin/main = 907c3ce`, **9 PR ouvertes, 0 fusionnée**
> **Méthode :** chaque chiffre de ce document provient d'une commande et de sa sortie
> (SQL sur le Postgres du VPS, `gh`, `curl`, log CI, `git show origin/<branche>:<fichier>`).
> Aucun run de pipeline n'a été lancé pour l'écrire (gate crédits — quota Tavily épuisé).

---

## 1. Résumé exécutif

Le MVP est **techniquement livré et tourne en production**. Les huit briques prévues existent,
sont déployées et vérifiables : pipeline, scoring hybride, VPS, API, front, accès public,
Metabase, Airtable.

Sur les 9 KPI du PRD §6, le bilan mesuré est : **1 atteint, 4 manqués, 3 non mesurés, 1 à la limite.**

**Mais le principal manqué n'est pas un défaut du pipeline — c'est un défaut de configuration.**
La chaîne d'enrichissement gratuite (OSM), construite, validée et fusionnée sur `main`, **n'a jamais
été activée dans aucune des trois campagnes mesurées**. Les taux d'enrichissement du MVP mesurent donc
une configuration dégradée, pas la capacité réelle du produit. C'est démontré en §4 et c'est le
point n° 1 de la Phase 2 — il coûte 0 €.

Deux autres constats structurants : le **compteur de qualifiés s'érode tout seul** dès qu'un
commercial saisit un résultat d'appel (§5.1), et la table `appels` **n'a jamais reçu une seule ligne**
(§5.2).

---

## 2. Ce qui a été livré (vérifié)

### 2.1 Pipeline & scoring
- Pipeline LangChain **6 nodes** (init_campagne → collecte Sirene → nettoyage → enrichissement →
  scoring → persistance), piloté par `main.py --campagne-id`.
- **Scoring hybride 3 couches** : règles métier (35 %) + Claude Haiku 4.5 (45 %) + embeddings Qdrant (20 %).
- **Généricité validée inter-secteurs** : hôtels 5510Z vs agences de com 7311Z, 150 prospects chacun,
  **zéro ligne de code changée** — seul le JSON d'ICP diffère. Les scores Claude sont quasi identiques
  d'un secteur à l'autre (p50 = 45, max = 85 **à l'identique**), et Claude met bien à 0 le hors-NAF
  (SCI/holdings enregistrées en 5510Z) et les exclusions d'ICP dans **les deux** secteurs.
  → La thèse « le secteur est une configuration, pas du code » (`agents.md`, PRD §7) est **validée par la mesure**.
- 3 bugs mode-campagne trouvés et corrigés en Sprint 3 (NAF non normalisé = −30 sur tout prospect réel ;
  `osm_tags` absent du schéma ; `init_icp` UPDATE sur colonne inexistante → couche embedding muette).
  Le fix NAF seul a rendu **+5,9 pts** de score final moyen et **+3 qualifiés / 100**.

### 2.2 Production (VPS OVH) — état vérifié le 23/08/2026

| Élément | Vérification | Résultat |
|---|---|---|
| Service API | `systemctl is-enabled/is-active prospection-api` | `enabled` / `active` |
| Service tunnel | `systemctl is-enabled/is-active ngrok-prospection` | `enabled` / `active` |
| Santé API | `curl 127.0.0.1:8000/api/health` | **200** |
| Santé Metabase | `curl 127.0.0.1:3000/api/health` | **200** |
| Accès public | `curl https://bobbed-matted-jab.ngrok-free.dev/` | **302 → `idp.ngrok.com/oauth2/authn`** |
| API publique | `curl .../api/kpis` | **302** (rien ne fuit) |
| Crons | `crontab -l` | 3 crons, **tous locaux, 0 appel API** |

VPS-2 OVH (4 vCore / 8 Go / Ubuntu 26.04, ~8,49 €/mois). Ports 5432/6333 liés à `127.0.0.1`
uniquement (scan externe validé), ufw + fail2ban + auth par clé. Backup `pg_dump` quotidien +
rétention 30 j + purge RGPD quotidienne.

### 2.3 Front ↔ back
Intégration **complète, lecture et écriture**, vérifiée en direct : dashboard (KPI + distribution des
scores + campagnes réelles), liste prospects avec filtres et badge « joignable », fiche détail (identité,
contact, justification Claude, décomposition par couche), console d'appel (RDV / Refus / Absent + notes
qui écrivent réellement), création de campagne (formulaire ICP → brouillon, 0 collecte, 0 crédit).

Tout le mock fabriqué a été retiré (colonne « € » fictive, courbe de croissance inventée, estimations
de campagne, et le **« Profil LinkedIn lié »** qui était un NO-GO légal). **Restent mock :** onboarding
workspace, pages Support / Info / Paramètres.

### 2.4 Accès public
`https://bobbed-matted-jab.ngrok-free.dev` — FastAPI sert le front (`dist/`) **et** l'API en same-origin,
derrière une passerelle **Google OAuth + allowlist e-mail**. Zéro DNS touché sur `soveratech.fr`
(Cloudflare Access écarté : le tier gratuit imposait une migration NS complète = risque e-mail).
Ajouter un testeur = 3 commandes. **Plafond gratuit : 5 MAU.**

### 2.5 Observabilité & diffusion
- **Metabase (#37)** : déployé, admin + datasource Postgres configurés, dashboard « Prospection — KPIs »
  vivant, accès tunnel-only. Deux pièges corrigés : Docker contournait ufw (publication `0.0.0.0`) et
  la JVM tombait en OOM crash-loop à `mem_limit: 1g`.
- **Airtable (#36)** : `scripts/sync_airtable.py`, upsert idempotent sur clé SIRET, batché/async.
  **Testé sur le vrai VPS : 27 créés puis 27 mis à jour.**
- **Rapport hebdo (#38)** : générateur KPIs (texte + HTML), **envoi Brevo vérifié en vrai** (rc=0).
- **LangSmith (#30)** : traces `score_llm_claude` confirmées (endpoint EU).
- **CI (#121)** : GitHub Actions, pytest unitaire sur chaque PR — **304 passed, 12 deselected**, vert
  (run `32595109799`).

### 2.6 RGPD
Purge automatique (#41) selon les 4 durées de `LEGAL.md`, journal `purge_rgpd_log`, table
`oppositions_rgpd` **jamais purgée**, `--dry-run`. C'était le bloqueur légal de la mise en prod.

---

## 3. Ce qui est mesuré — KPI du PRD §6 vs réel

**Base de mesure :** 3 campagnes en production sur le VPS, **400 prospects au total**.
Requête SQL du 23/08/2026 sur `prospection_b2b`.

| Campagne | Collectés | Score ≥ 60 | Moy. des ≥ 60 | Moy. globale | Tél | E-mail | Site web | Joignables |
|---|---|---|---|---|---|---|---|---|
| Hôtels 5510Z (re-run) | 150 | **23** (15,3 %) | 69,8 | 41,0 | 22 (14,7 %) | 19 (12,7 %) | 41 (27,3 %) | 28 (18,7 %) |
| Agences com 7311Z | 150 | **7** (4,7 %) | 66,6 | 35,3 | 5 (3,3 %) | 14 (9,3 %) | 26 (17,3 %) | 17 (11,3 %) |
| Campagne test VPS | 100 | **13** (13,0 %) | 71,5 | 43,1 | 15 (15,0 %) | 14 (14,0 %) | 27 (27,0 %) | 21 (21,0 %) |
| **TOTAL** | **400** | **43 (10,8 %)** | **69,8** | — | **42 (10,5 %)** | **47 (11,8 %)** | **94 (23,5 %)** | **66 (16,5 %)** |

### Tableau de bord PRD

| # | KPI | Cible | Réel mesuré | Verdict |
|---|---|---|---|---|
| 1 | Prospects collectés / semaine | ≥ 500 | Plus gros run réel = **150** ; 400 cumulés ; cron hebdo (#34) **non activé** | ❌ **Non atteint** (gaté crédits) |
| 2 | Taux enrichissement **téléphone** | ≥ 40 % | **14,7 %** (hôtels) · 3,3 % (agences) · 10,5 % global | ❌ **Non atteint** |
| 3 | Taux enrichissement **e-mail** | ≥ 20 % | **12,7 %** (hôtels) · 9,3 % (agences) · 11,8 % global | ❌ **Non atteint** |
| 4 | % qualifiés (score ≥ 60) | ≥ 30 % | **15,3 %** (hôtels) · 4,7 % (agences) · 10,8 % global | ❌ **Non atteint** |
| 5 | Score moyen des qualifiés | ≥ 65/100 | **69,8** (69,8 / 66,6 / 71,5 — les 3 campagnes au-dessus) | ✅ **Atteint** |
| 6 | Accord humain / score IA | ≥ 75 % | **Jamais mesuré** — aucune campagne de labellisation humaine | ⬜ **Non mesuré** |
| 7 | Coût / prospect qualifié | ≤ 0,15 € | **Non instrumenté.** Estimation ~0,03–0,05 € (Claude ≈ 1 €/500 + VPS amorti) | ⬜ **Estimé, non mesuré** |
| 8 | Durée pipeline 500 prospects | ≤ 45 min | **Jamais couru à 500.** Extrapolé de 3 runs : **45–50 min** (5,4–6,0 s/prospect) | ⚠️ **À la limite** |
| 9 | Taux appels → RDV | ≥ 2 % | 6 clics de démo, **0 appel réel**. L'appel est Phase 2 par décision | ⬜ **Hors périmètre MVP** |

**Bilan : 1 atteint · 4 manqués · 3 non mesurés · 1 à la limite.**

Lecture honnête du KPI 5 : le scoring **fait bien son travail** — quand un prospect est qualifié,
il est bon (69,8 de moyenne, au-dessus de la cible). Le problème n'est pas la qualité du tri,
c'est le **volume de matière première joignable** qui entre dans le tri. Voir §4.

---

## 4. 🔴 Le constat central : la chaîne gratuite n'a jamais été activée

Les KPI 2, 3 et 4 sont manqués **ensemble**, et ils ont **la même cause unique**, mesurée :

### 4.1 La preuve

```sql
SELECT c.nom, ct.osm_tags, ct.codes_naf FROM campagnes c
  JOIN criteres_ciblage ct ON ct.id = c.critere_id;
```

```
Comparaison hotels 5510Z (re-run) | {} | {5510Z}
Campagne test VPS                 | {} | {5510Z}
Comparaison agences com 7311Z     | {} | {7311Z}
```

`osm_tags` est **vide sur les trois campagnes**. Or dans `agents/enrichissement_agent.py` (sur `main`) :

```python
osm_tags = list(getattr(criteres, "osm_tags", None) or [])
if osm_tags:                      # <-- liste vide = falsy = pré-passe SAUTÉE
    stats = await enrichir_par_osm(prospects, osm_tags, ...)
```

**La pré-passe OSM n'a donc tourné dans aucun des 400 prospects mesurés.**

Pourquoi elle est toujours vide : `scripts/seed_icp.py` écrit exactement **11 colonnes** dans
`criteres_ciblage` — `osm_tags` n'en fait pas partie — et **aucun fichier JSON d'ICP ne possède
la clé** (`config/icp_test.json`, `config/icp_agences_com.json`). Le seul moyen de la remplir
aujourd'hui est un `UPDATE` SQL manuel.

La colonne existe (ajoutée par le fix #103), le code la lit, `utils/osm.py` est écrit et validé
en réel — **il manque uniquement le chaînon de configuration qui allume le tout.**

### 4.2 Ce que ça coûte

Deuxième aggravant, mesuré sur le VPS : `crawl4ai` est **ABSENT** (dépendance optionnelle, hors
`requirements.txt`). La cascade réelle en production n'est donc pas
« OSM → Tavily → Crawl4AI → DDG » mais **« Tavily → DDG »**. Et Tavily est épuisé.

Or la chaîne OSM avait été mesurée proprement (n = 40 hôtels parisiens non domiciliés) :

| Étape | Mesuré | KPI PRD correspondant |
|---|---|---|
| Jointure géographique OSM | **75 %** | — |
| Téléphone (tag OSM, fiable) | **32 %** | cible ≥ 40 % — proche |
| E-mail au bon domaine | **30 %** | cible ≥ 20 % — **dépassée** |

**Conclusion :** le MVP a mesuré 12,7 % d'e-mail là où la chaîne prévue en donne 30 % — c'est-à-dire
**au-dessus de la cible PRD**. Les KPI d'enrichissement du MVP ne décrivent pas le produit conçu ;
ils décrivent le produit avec sa meilleure source éteinte.

### 4.3 Le confondant Tavily (à ne pas confondre avec le point précédent)

Le run agences a subi **60 échecs Tavily `HTTP 432` sur 150** (quota mensuel gratuit 1000 épuisé),
là où le run hôtels — passé **en premier** — n'en a eu aucun. La couverture contact des agences est
donc dégradée **par l'ordre d'exécution**, pas seulement par le secteur.

→ La comparaison hôtels vs agences reste **directionnelle, pas propre**. Pour un verdict honnête :
rejouer **les agences en premier** (ou randomiser l'ordre) après le reset du quota.

Ce qui **n'est pas** confondu et reste solide : la couche Claude généralise parfaitement
(p50 et max identiques entre secteurs), et l'embedding ne discrimine pas en mono-secteur — deux
conclusions indépendantes du quota.

---

## 5. Deux défauts structurels trouvés en écrivant cette rétro

### 5.1 Le compteur de qualifiés s'érode tout seul

```
statut : nouveau 281 · invalide 76 · qualifie 37 · rdv 2 · refus 2 · absent 2   (total 400)
score_final >= 60 : 43
```

Les comptes se réconcilient : **43 = 37 + 6**. Les 6 prospects sortis du compteur `qualifie` sont
exactement les 6 qui ont reçu un résultat d'appel pendant la démo — et **tous les 6 ont un score ≥ 60**.

`POST /api/prospects/{id}/outcome` fait un `UPDATE prospects SET statut = ...`. Or `/api/kpis` **et**
`scripts/rapport_hebdo.py` comptent les qualifiés avec `WHERE statut = 'qualifie'`.

**Conséquence :** chaque résultat d'appel saisi par un commercial **décrémente le nombre de qualifiés
affiché — y compris un RDV obtenu, c'est-à-dire un succès.** Le KPI n° 4 baisse quand le produit marche.
Le PRD définit pourtant le qualifié par le **score ≥ 60**, pas par un statut de workflow mutable.

### 5.2 La table `appels` n'a jamais reçu une ligne

`SELECT count(*) FROM appels;` → **0**, alors que 6 résultats d'appel ont été saisis. L'endpoint
`outcome` écrit un statut sur le prospect, jamais un enregistrement d'appel.

Conséquences : aucun historique d'appel, aucun horodatage, pas de trace d'un prospect appelé deux fois,
et la rétention « appels : 1 an » de `LEGAL.md` porte sur une table structurellement vide. Le rapport
hebdo contourne en dérivant les appels du `statut` — ce qui fonctionne mais confond « état actuel »
et « un appel a eu lieu ».

---

## 6. Ce qui est ouvert ou gaté

### 6.1 Les 9 PR en attente de revue — le risque n° 1 aujourd'hui

`origin/main = 907c3ce`. **Rien n'est fusionné.** L'ordre est balisé dans les titres :

| PR | Objet | Ordre |
|---|---|---|
| **#119** | API d'écriture (contient aussi la lecture, **supersède #117 fermé**) | **1/2** |
| **#120** | Déploiement Slice 3 codifié (front servi par l'API + ngrok OAuth) | **2/2 — après #119** |
| #112 | ICP agences de com (7311Z) | fusion libre |
| #113 | Relevé d'acceptance #33 (`Closes #33`) | fusion libre |
| #114 | Générateur de rapport hebdo (#38) | fusion libre |
| #115 | Metabase lié 127.0.0.1 + runbook (#37) | fusion libre |
| #118 | Front câblé sur l'API réelle | fusion libre |
| #121 | CI GitHub Actions (vérifiée verte) | fusion libre |
| #122 | Sync Airtable (#36) | fusion libre |

🪤 **Piège à ne pas rater au merge :** `api/` vit sur le VPS en **untracked (scp)**. Avant le
`git pull` qui suit la fusion de #119 → **`rm -rf api/` sur le VPS**, sinon le pull est bloqué
(c'est exactement ce qui s'était produit avec `config/icp_test.json`).

⚠️ Rappel du piège des PR empilées : après chaque fusion, **vérifier le contenu sur `main`**
(`git merge-base --is-ancestor` + `git ls-tree`), jamais le badge « merged » — deux PR affichées
« merged » n'étaient jamais arrivées sur `main`, dont un filtre légal.

**Tant que ces PR ne sont pas fusionnées, la production tourne sur du code non tracé.** Une
reconstruction du VPS perdrait l'API, le front servi et la configuration ngrok.

### 6.2 Quota Tavily
Épuisé depuis le 21/08 (`HTTP 432`, quota gratuit 1000/mois). **Aucun run dépendant de Tavily n'est
possible avant le reset mensuel.** La date exacte du reset n'a pas été vérifiée (une sonde consomme
un crédit) — **à sonder avant de planifier quoi que ce soit**.

### 6.3 Pilote #35 — non lancé, et c'est une décision métier
La première campagne réelle 500 prospects attend un **vrai client pilote**. La décision d'équipe D5
a acté qu'il n'y a **aucun client et aucun volume annoncé** : le projet sert à valider le travail
d'équipe et finaliser le produit. #35 est donc **bloqué en amont du technique**. La comparaison
hôtels/agences peut servir de démo commerciale en attendant.

**MàJ 23/08 — la config d'ICP pilote existe désormais** : `config/icp_hotels_pilote.json`,
**PR #123** (`chore/icp-hotels-pilote-35`, base `main`, `Refs #35`, non fusionnée) — 10ᵉ PR ouverte.
Vérifiée indépendamment : merge-base = `907c3ce` exactement (pas d'empilement), 1 commit / 1 fichier
/ +17, et `seed_icp --dry-run` **rejoué ici = exit 0**. Restent à faire avant de semer : remplacer le
client placeholder, et **ajouter** les champs `contact_*` (ils sont absents du fichier, pas à remplacer).

⚠️ **Une réserve de fond sur cette PR.** Elle ajoute `5520Z` (hébergement courte durée) à côté du
5510Z mesuré, en justifiant que le tail micro (gîtes, meublés, chambres d'hôtes) « tombe par
`effectif_min=2` ». **Ce garde-fou est inactif la plupart du temps** : `_hors_cible_effectif` retourne
`False` quand l'effectif est inconnu (« on ne conclut pas »), et l'effectif vient de
`trancheEffectifsUniteLegale`, souvent absent. **Mesuré sur les données réelles : effectif inconnu pour
63,3 % des hôtels (95/150)**, 88,7 % des agences, 59 % de la campagne test. Sur 5520Z — dominé par des
unités non employeuses — le taux d'inconnus sera *plus* élevé, pas moins. Le tail retombe donc sur la
**couche LLM**, pas sur l'effectif. Claude fait effectivement ce travail (mesuré en #32 et le 21/08),
mais diluer le lot fait mécaniquement baisser le **% de qualifiés** — précisément le KPI sur lequel
#35 sera jugé. La PR embarque déjà le revert à `["5510Z"]` en 1 ligne : **corriger la justification et
surveiller le 1er batch**, plutôt que bloquer.

### 6.4 Légal / CNIL

| Sujet | État |
|---|---|
| **Loi 2025-594** (Bloctel abrogé, démarchage tél. B2C → opt-in, échéance **11 août 2026 — déjà passée**) | 🔴 `docs/LEGAL.md` **ne la mentionne pas**. B2B reste opt-out, mais **auto-entrepreneurs et mobiles perso comptent comme consommateurs**. À réconcilier **avant** toute fonction d'appel |
| **Opposition commerciale** (art. R123-232) | Filtre `utils/opposition_commerciale.py` présent, mais **jeton Pappers expiré (401)** sur les 3 runs → **opposition non vérifiée sur les 400 prospects**. Mesuré ailleurs : **49 % d'opposés**, et **87 % sur les SIREN récents** |
| **Auth API** | 🔴 L'API n'a **aucune authentification propre** (CORS `*`). La seule barrière est la passerelle OAuth ngrok. Suffisant en MVP fermé, **insuffisant dès une exposition élargie** |
| **PII → Airtable (US)** | Acceptable en MVP, **à durcir avant tout usage commercial** |
| **Checklist CNIL complète** | Exigée avant lancement commercial — **non commencée** |
| **Clé API `cr_...` exposée** | Régénérée ✅ |
| **NDA / IP / périmètre** | Pas de SAS, aucun accord signé. À traiter **avant** toute donnée client réelle ou argent |

### 6.5 Vocal — Phase 2, et pas la prochaine étape
`agents.md` est explicite : appel vocal = Phase 2, **uniquement pour confirmer des leads déjà qualifiés**,
**pas vendu séparément tant que la V1 n'a pas de clients payants**. S'y ajoutent trois prérequis
techniques et légaux : la loi 2025-594 (§6.4), la table `appels` qui n'existe qu'en schéma (§5.2), et
le fait que la base est **call-centric** (`file_appel`, `appels`, `bloctel_ok`) alors que le produit a
été tranché **email-first** (D6). Ce désalignement est à revisiter **quand** l'appel sera construit.

### 6.6 Autres dettes connues
Onboarding + pages Support/Info/Paramètres encore statiques · plafond ngrok **5 MAU** ·
`crawl4ai` absent du VPS · Makefile appelle `python` au lieu de `.venv/bin/python` ·
SSH `PasswordAuthentication` encore actif · formulaire ICP expose des codes NAF à un client final
(à abstraire côté studio) · une version non poussée chez un coéquipier à réintégrer.

---

## 7. Plan Phase 2 — priorisé

Principe de tri : **d'abord ce qui coûte 0 € et change ce que les chiffres disent**, ensuite ce qui
demande du quota, en dernier ce qui demande un client.

### P0 — Fusionner le train de PR *(0 €, aucun code nouveau)*
Fusionner **#119 puis #120**, les 7 autres en fusion libre. Sur le VPS : `rm -rf api/` **avant**
`git pull`, puis basculer le service sur `deploy.serve:app` et re-`scp dist/`. **Vérifier le contenu
sur `main` après chaque fusion**, pas le badge.
→ *Pourquoi d'abord :* la prod tourne sur du code non tracé. C'est le seul risque de perte sèche.
**Propriétaire : l'équipe (John arbitre) · Horizon : cette semaine.**

### P1 — Allumer la chaîne OSM *(0 €, petit PR, plus fort levier du projet)*
Ajouter `osm_tags` au schéma JSON d'ICP **et** à l'upsert de `seed_icp.py` (12ᵉ colonne), renseigner
`tourism=hotel` pour l'ICP hôtels et l'équivalent agences, backfill des campagnes existantes.
Puis **re-mesurer**.
→ *Attendu, d'après la mesure n = 40 :* e-mail 12,7 % → **~30 %** et téléphone 14,7 % → **~32 %**,
c'est-à-dire **KPI 3 dépassé et KPI 2 approché**. Un seul changement de configuration fait basculer
le tableau de bord. **Propriétaire : Claude Code + John · Horizon : dès P0 fusionné.**

### P2 — Réparer la définition des KPI *(0 €)*
Compter les qualifiés par `score_final >= 60` (définition du PRD) et non par `statut`, dans
`/api/kpis` **et** `scripts/rapport_hebdo.py`. Écrire une vraie ligne dans `appels` à chaque `outcome`.
→ Sans ça, tout chiffre de Phase 2 sera faux dès que l'équipe commerciale utilisera l'outil.
**Propriétaire : Claude Code · Horizon : avec P1.**

### P3 — Re-mesurer proprement *(nécessite le reset Tavily)*
Sonder le quota, puis rejouer la comparaison inter-secteurs **agences en premier** (ou ordre randomisé)
pour lever le confondant §4.3. Enchaîner sur un run **500 borné** — qui mesure du même coup le KPI 8
(durée) et le KPI 7 (coût), aujourd'hui tous deux non mesurés.
**Propriétaire : Claude Code, sur accord explicite de John (gate crédits) · Horizon : après reset.**

### P4 — Instrumenter le coût par run *(0 €)*
LangSmith est déjà câblé et les traces confirmées : extraire le coût par campagne et l'exposer dans le
rapport hebdo. Clôt honnêtement le KPI 7. **Propriétaire : Claude Code · Horizon : avec P3.**

### P5 — Mesurer l'accord humain / IA *(0 €, aucun appel API)*
Labelliser à la main ~100 prospects déjà scorés (2 relecteurs indépendants), comparer aux bandes de
score. C'est le dernier KPI du PRD jamais mesuré, et le moins cher.
**Propriétaire : l'équipe (2 relecteurs) · Horizon : 1 séance.**

### P6 — Mise en conformité avant tout mouvement commercial
Mettre `docs/LEGAL.md` à jour pour la loi 2025-594 · renouveler le jeton Pappers pour **réactiver le
contrôle d'opposition commerciale** (49 % d'opposés mesurés : c'est une **obligation**, pas une option) ·
ajouter une authentification propre à l'API · trancher PII → Airtable US · démarrer la checklist CNIL ·
**tenir la conversation NDA / IP / périmètre avant toute donnée client réelle**.
**Propriétaire : John · Horizon : avant le pilote #35.**

### P7 — Produit & UX
Séparer deux interfaces : **admin studio** (formulaire ICP technique actuel, à garder) et **client**
(sélecteurs métier — « hôtels indépendants à Paris » — traduits en NAF en coulisse, éventuellement par
Claude). Finir onboarding + Support/Info/Paramètres. Passer à Cloudflare (50 utilisateurs) si l'on
dépasse 5 testeurs. **Propriétaire : l'équipe front · Horizon : Phase 2 milieu.**

### P8 — Vocal (Retell AI) — **à différer explicitement**
**Recommandation : ne pas démarrer maintenant.** Conditions d'entrée, toutes non remplies à ce jour :
(1) V1 avec **clients payants** ; (2) loi 2025-594 réconciliée ; (3) table `appels` réellement écrite
(P2) ; (4) arbitrage du désalignement email-first vs schéma call-centric. Le mailing Brevo, déjà câblé
et vérifié, est le prolongement naturel **avant** le vocal.
**Propriétaire : John (décision) · Horizon : Phase 2b, après premier client.**

---

## 8. Décisions à acter (critère d'acceptance #39)

| # | Décision | Recommandation | Propriétaire | Horizon |
|---|---|---|---|---|
| 1 | Fusionner les 9 PR | **Oui**, ordre #119 → #120 puis libre | Équipe | Cette semaine |
| 2 | Activer la chaîne OSM | **Oui** — plus fort levier, 0 € | Claude Code | Dès P0 |
| 3 | Agent vocal (Retell AI) | **Différer** à Phase 2b, après premier client payant | John | Non planifié |
| 4 | Mailing automatique (Brevo) | **Oui** — déjà câblé et vérifié, prolongement naturel | Équipe | Phase 2 milieu |
| 5 | Interface self-service ICP | **Oui, en deux UI** (studio / client), pas avant P0-P2 | Équipe front | Phase 2 milieu |
| 6 | Barème générique adapté au secteur ? | **Oui — validé par la mesure** : Claude généralise sans changement de code (p50/max identiques). Le barème n'est pas le problème, la **couverture contact** l'est | — | Acté |
| 7 | Lancer le pilote #35 | **Bloqué en amont** : pas de client (D5). À rouvrir quand un pilote existe | John | Ouvert |

---

## 9. Ce que la rétro apprend sur la méthode

- **La réconciliation arithmétique paie encore une fois.** C'est l'écart 43 vs 37 — deux compteurs
  censés dire la même chose — qui a fait tomber le défaut §5.1. Le « tout est vert » ne l'aurait pas montré.
- **Un composant fusionné n'est pas un composant actif.** OSM était codé, testé, mesuré, fusionné —
  et éteint par une colonne vide. Entre « le code est sur `main` » et « la fonction tourne en prod »,
  il reste un chaînon de configuration que rien ne vérifie aujourd'hui.
  → *Garde-fou proposé :* un test d'intégration qui échoue si une campagne est lancée avec `osm_tags` vide
  alors que l'ICP décrit un commerce physique.
- **Mesurer dans le désordre fabrique de fausses conclusions sectorielles.** Le run agences paraissait
  structurellement plus faible ; une part de l'écart n'est que l'ordre de passage face au quota.
- **9 PR non fusionnées, c'est une dette de production, pas une dette de revue.** La prod tourne sur
  du `scp` non tracé.

---

*Document rédigé le 23/08/2026 pour clore l'issue #39. Toutes les mesures sont reproductibles :
requêtes SQL sur le Postgres du VPS, `gh pr/issue list`, `gh run view`, `curl` sur les endpoints de santé,
et `git show origin/<branche>:<fichier>` pour le contenu des PR non fusionnées.*
