# Runbook — #35 (1er run réel 500 prospects) + #34 (cron hebdo) — prêt pour le 1er sept

> **Préparé le 24/08/2026. RIEN N'A ÉTÉ LANCÉ.** Ce document rend le run réel **exécutable
> en une seule action** dès que le quota Tavily se réinitialise. Tant que la porte crédits
> (ci-dessous) n'est pas ouverte, on ne lance rien.

---

## 🔴 PORTE CRÉDITS — à lire en premier

- **Quota gratuit Tavily ÉPUISÉ** (HTTP 432 « exceeds your plan's set usage limit »), mesuré le
  21/08. Réinitialisation mensuelle = **1er du mois → 1er septembre 2026**.
- **Aucun run pipeline avant le 1er sept.** `main.py --campagne-id …` et `scripts/run_campagne.sh`
  consomment **INSEE + Tavily + Claude**. `--dry-run` de `main.py` **n'aide pas** : il évite
  seulement les écritures DB, mais **appelle quand même les API** (donc consomme). Le seul dry‑run
  gratuit est celui de `seed_icp.py` (validation Pydantic pure, 0 réseau).
- Le VPS **au repos ne coûte rien** (~8,49 €/mois flat ; containers locaux sans appel externe).

**État vérifié (24/08) :** `origin/main = 7472c7d`, **VPS HEAD = 7472c7d** (réconcilié), config #35
mergée et présente sur le VPS, services up (postgres/qdrant/ollama/metabase healthy,
`prospection-api` actif, `/api/health` = `{"status":"ok"}`).

---

## ✅ PRÉ-CÂBLÉ le 24/08 — le 1er sept se réduit à UNE commande

Les 2 étapes gratuites (créer la campagne + embedding) **ont déjà été exécutées** (0 crédit).
La campagne pilote existe en base en **`brouillon`** (collectés 0 / qualifiés 0 = rien lancé),
son ICP est embarqué dans Qdrant.

| | Valeur |
|---|---|
| **CAMPAGNE_ID** | **`b3d7b46e-110f-49e8-adbc-aaed7f9faa9c`** |
| client_id | `ae951e03-813e-4ef5-850f-a8fdec5afa3e` |
| icp_profile_id | `9a2dfa37-f842-48fd-bf68-0329c7b0f78b` (embedding `nomic-embed-text`, 768 dims) |

**→ Le 1er sept (après GO de John), UNE SEULE commande sur le VPS (⚠️ consomme les crédits) :**

```bash
cd /opt/prospection-b2b && ./scripts/run_campagne.sh b3d7b46e-110f-49e8-adbc-aaed7f9faa9c 500
```

> Puis export CSV (gratuit) — cf. §« Export CSV » plus bas (mettre `campagne_id='b3d7b46e-…'`).
> Retrouver l'id à tout moment : `.venv/bin/python main.py --list-campagnes` (ligne « pilote #35 »).
> ⚠️ **Ne PAS re-créer la campagne** le 1er sept (la §« Séquence » ci-dessous, étapes 1–2, est déjà
> faite) — sinon on crée un doublon client+campagne. Si tu veux repartir de zéro (ex. vrai client),
> re-crée et relance `init_icp`.

---

## Accès VPS (rappel)

```bash
IP=$(tr -d '[:space:]' < /c/Users/gdzsp/.vps_ip)
ssh -i /c/Users/gdzsp/.ssh/vps_deploy -o BatchMode=yes ubuntu@"$IP"
# Repo : /opt/prospection-b2b · venv : .venv · user : ubuntu (sudo+docker sans mdp)
```

---

# PARTIE 1 — #35 : premier run réel (500 prospects, hôtels)

## Ce qui est prêt

- **Config ICP :** [`config/icp_hotels_pilote.json`](../config/icp_hotels_pilote.json)
  — NAF `5510Z` + `5520Z`, dép `75`/`92`, effectif `2–50`, ancienneté `≥2 ans`,
  `exiger_site_web`/`exiger_email` = false.
- **Validée sans crédit** le 24/08 :
  ```bash
  PYTHONIOENCODING=utf-8 PYTHONPATH=. .venv/bin/python scripts/seed_icp.py \
    --from-file config/icp_hotels_pilote.json --dry-run
  # → [dry-run] Payload validé ✓   EXIT=0
  ```

## ⚠️ La seule entrée à finaliser — identité du client (décision John)

Les champs « côté client » de la config sont un **placeholder** :
`nom_entreprise = "Client Pilote — Hôtellerie indépendante"`, `produit_vendu = "Solution SaaS de
gestion hôtelière"`, `zone_intervention = "Île-de-France (Paris & Hauts-de-Seine)"`, et
`contact_nom / contact_email / contact_telephone` **absents**.

**Décision John (24/08) : pas de société cliente externe** — le pilote est un **run de validation
du produit** (la solution de prospection est elle‑même le produit). Ces champs décrivent le client
payeur, pas les prospects (= les hôtels indépendants, définis par `criteres_ciblage`).

→ **Pour un run de validation : le placeholder suffit** (la config valide, le pipeline tourne).
→ **Avant tout pilote COMMERCIAL** avec un vrai client : remplacer `nom_entreprise` et *ajouter*
`contact_*` (édition de 30 s, puis re‑valider en dry‑run gratuit), et propager sur le VPS
(merge main + `git pull`, ou scp du seul fichier config).

## Séquence de lancement (sur le VPS, dans `/opt/prospection-b2b`)

> **NB : les étapes 1–2 sont DÉJÀ FAITES** (pré-câblées le 24/08, cf. encart ✅ ci-dessus,
> `CAMPAGNE_ID = b3d7b46e-110f-49e8-adbc-aaed7f9faa9c`). Le 1er sept, sauter directement à
> l'**étape 3**. La séquence complète ci-dessous ne sert qu'à **repartir de zéro** (ex. vrai client).
>
> Étapes 1 et 2 = **GRATUITES** (0 crédit). Étape 3 = **la seule action qui consomme des crédits.**

```bash
cd /opt/prospection-b2b

# 1. (GRATUIT) Créer la campagne — config seulement, 0 appel API/run/embedding.
#    Réutilise le normaliseur de seed_icp ; crée client+critères+icp_profile+campagne ;
#    renvoie les IDs. (POST /api/campagnes, cf. api/main.py.)
RESP=$(curl -s -X POST http://127.0.0.1:8000/api/campagnes \
         -H 'Content-Type: application/json' \
         --data @config/icp_hotels_pilote.json)
echo "$RESP"
CAMPAGNE_ID=$(echo "$RESP" | .venv/bin/python -c "import sys,json;print(json.load(sys.stdin)['campagne_id'])")
CLIENT_ID=$(echo "$RESP"   | .venv/bin/python -c "import sys,json;print(json.load(sys.stdin)['client_id'])")
echo "CAMPAGNE_ID=$CAMPAGNE_ID"

# 2. (GRATUIT) Générer l'embedding ICP (Ollama local — sinon la couche embedding du scoring
#    reste muette, cf. #26/#39).
PYTHONPATH=. .venv/bin/python scripts/init_icp.py --client-id "$CLIENT_ID"
```

### 🚀 3. LA commande de lancement (⚠️ consomme INSEE + Tavily + Claude)

```bash
./scripts/run_campagne.sh "$CAMPAGNE_ID" 500
```

- `run_campagne.sh <campagne-id> [limit]` — wrapper #34 : `cd` repo, choisit `.venv/bin/python`,
  `PYTHONPATH=.`, exécute `main.py --campagne-id <id> --limit 500`. **`limit` par défaut = 500**
  (donc `run_campagne.sh "$CAMPAGNE_ID"` suffit, mais on l'écrit explicitement pour #35).
- Durée attendue ~ **45–55 min** pour 500 (mesuré ~14–15 min/150, Ollama CPU).
- Si tu préfères vérifier l'id avant : `.venv/bin/python main.py --list-campagnes`.

### 4. (GRATUIT) Export CSV des qualifiés → équipe commerciale (acceptance #35)

Aucun script d'export n'existe encore ; export direct depuis Postgres (0 crédit) :

```bash
docker exec prospection_b2b_postgres psql -U scraper -d prospection_b2b -c \
"\copy (SELECT siret,nom_entreprise,nom_dirigeant,telephone,telephone_2,email,site_web,\
adresse,code_postal,ville,score_final,statut FROM prospects \
WHERE campagne_id='$CAMPAGNE_ID' AND (statut='qualifie' OR score_final>=60) \
ORDER BY score_final DESC) TO STDOUT WITH CSV HEADER" \
  > qualifies_35_$(date +%Y%m%d).csv
wc -l qualifies_35_$(date +%Y%m%d).csv
```

## Ce qu'on regarde au 1er batch (jugement #35)

- **% qualifiés** : cible PRD 30 % (score ≥ 60). Mesure comparable (150) = **15,3 %**. Écart connu ;
  **documenter avant de relancer**, ne pas boucler (contrainte #35).
- **5520Z non mesuré** : s'il dilue le % qualifiés, **revenir à `["5510Z"]`** (1 ligne dans la config)
  — cf. [`memory/icp-hotels-pilote.md`].
- Couverture tél/email : dépend de Tavily complet (le confound du 21/08 est levé après reset).
- Vérifier `statut` / KPI (piège #39 : `POST /outcome` décrémente les qualifiés) avant de citer un chiffre.

---

# PARTIE 2 — #34 : cron campagne hebdo (lundi 6h) — PRÉPARÉ, **DÉSACTIVÉ**

## Décision : NON installé (porte crédits)

Le cron campagne lance `run_campagne.sh` **chaque lundi 6h** → il **consomme des crédits à chaque
tirage**. Il ne doit être activé **que par John, après le 1er sept**, avec un `--limit` borné, et
seulement quand un tirage hebdo récurrent est réellement voulu. **Il n'est PAS dans la crontab live.**

## État des crons sur le VPS (vérifié 24/08) — aucun cron consommateur de crédits

| Cron (ubuntu) | Horaire | Effet | Crédits |
|---|---|---|---|
| Backup pg_dump gzip → `/opt/backups/` | `0 2 * * *` | local | **0** |
| Rétention backups > 30 j (`find … -delete`) | `30 2 * * *` | local | **0** |
| Purge RGPD (`scripts/purge_rgpd.py`) | `0 3 * * *` | local | **0** |
| Rapport hebdo KPIs (Brevo, `rapport_hebdo.py --send`) | `0 8 * * 1` | **1 email** | **0** (aucun Tavily/Claude/INSEE) |

- **root crontab : vide.** `/etc/cron.d` : seulement `e2scrub_all` (système). `cron.daily/weekly` :
  jobs système standard.
- **Aucun `main.py` / `run_campagne` planifié nulle part** (grep = « NONE — no pipeline cron active »).
- ℹ️ Le rapport hebdo #38 (lundi 8h) ne figurait pas dans la liste « backup/retention/purge » du
  brief — il a été ajouté depuis (email uniquement, 0 crédit pipeline). Signalé, non bloquant.

## Entrée crontab prête (à coller SEULEMENT à l'activation, après le 1er sept)

Fichier : [`deploy/cron/prospection-campagne.cron.disabled`](../deploy/cron/prospection-campagne.cron.disabled)

```cron
# Campagne hebdomadaire — lundi 6h (#34). DÉSACTIVÉ tant que non voulu (consomme des crédits).
# <CAMPAGNE_ID> = UUID d'une campagne EXISTANTE. La campagne pilote pré-câblée
# (b3d7b46e-110f-49e8-adbc-aaed7f9faa9c) peut être réutilisée, OU en créer une dédiée (cf. Partie 1 §1).
0 6 * * 1  /opt/prospection-b2b/scripts/run_campagne.sh <CAMPAGNE_ID> 500 >> /var/log/prospection/campagne.log 2>&1
```

### Procédure d'activation (par John, après le 1er sept)

```bash
# 1. Avoir une campagne existante (UUID). Réutiliser celle du run #35, ou en créer une (gratuit) :
#    voir Partie 1 §1. Récupérer l'UUID : .venv/bin/python main.py --list-campagnes
# 2. Éditer la crontab ubuntu et coller la ligne ci-dessus avec le vrai UUID + un --limit borné :
crontab -e
# 3. Vérifier :
crontab -l | grep run_campagne
```

> **Borne le `--limit`.** 500/semaine = ~2000 prospects/mois → surveiller le quota Tavily (1000/mois
> gratuit). Pour un hebdo soutenable en gratuit, viser `--limit` ~200 (à trancher selon le plan Tavily).

## Rotation des logs (préparée, à installer une fois — 0 crédit)

`campagne.log` (et les logs existants) grossissent sans borne. Config prête :
[`deploy/logrotate/prospection`](../deploy/logrotate/prospection).

```bash
sudo cp /opt/prospection-b2b/deploy/logrotate/prospection /etc/logrotate.d/prospection
sudo logrotate --debug /etc/logrotate.d/prospection   # vérif à sec, n'écrit rien
```

---

# DÉCISIONS QUI RESTENT À JOHN

1. **Identité du client réel** — *statut : ouvert (aucune société externe, run de validation produit).*
   Le placeholder suffit pour valider le produit ; à remplacer avant un pilote **commercial**.
2. **Le GO du 1er sept** — lancer l'unique commande payante :
   `run_campagne.sh b3d7b46e-110f-49e8-adbc-aaed7f9faa9c 500`. Personne ne la lance sans ton feu vert.
3. **Activer ou non le cron hebdo #34** — après le 1er sept, avec un `--limit` borné. Désactivé par défaut.
4. ✅ **Pré-câblage « one-shot » — FAIT le 24/08** (étapes 1–2 gratuites exécutées ;
   `CAMPAGNE_ID = b3d7b46e-110f-49e8-adbc-aaed7f9faa9c`, campagne en `brouillon`, embedding OK).
   Le 1er sept = une seule commande. *(Si tu préfères un vrai client d'abord : re-créer + `init_icp`.)*

---

## Annexe — preuves (24/08/2026)

- `seed_icp --dry-run` sur `icp_hotels_pilote.json` → **EXIT 0**, payload validé.
- VPS `git rev-parse HEAD` = `7472c7d` = `origin/main` ; working tree propre (2 untracked voulus).
- `crontab -l` (ubuntu) = 4 lignes ci-dessus ; root crontab vide ; `/etc/cron.d` = système ;
  grep pipeline cron = **aucun**.
- `curl 127.0.0.1:8000/api/health` = `{"status":"ok"}` ; `docker ps` = postgres/qdrant/ollama/metabase up ;
  Ollama joignable (init_icp OK).
- `/var/log/prospection/` existe (backup/purge/rapport logs) ; pas encore de `campagne.log` (cron jamais lancé).
- **Pré-câblage 24/08 (0 crédit) :** `POST /api/campagnes` → `campagne_id=b3d7b46e-110f-49e8-adbc-aaed7f9faa9c` ;
  `init_icp` → embedding `nomic-embed-text` 768 dims (`qdrant_point_id=9a2dfa37-…`) ; DB confirme
  `statut=brouillon, collectés=0, qualifiés=0` (aucun run). `logrotate --debug` du fichier prospection = OK.
