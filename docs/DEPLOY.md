# DEPLOY.md — Mise en production sur VPS OVH (issue #33)

> Runbook de déploiement de la stack Docker sur un VPS CPU OVH, en configuration
> **production sécurisée**, avant la première campagne réelle (#35).
> Ce qui est déjà prêt côté repo est signalé ✅ ; ce qui reste à faire sur le VPS est 🛠️.

---

## 0. Dimensionnement du VPS — À LIRE AVANT D'ACHETER

La stack **auto-héberge Ollama** (embeddings CPU, règle #5) : c'est le poste RAM dominant,
en plus de Postgres + Qdrant + l'app Python + l'OS.

| Offre OVH (2026) | RAM | ~€/mois | Verdict |
|---|---|---|---|
| Starter | 2 Go | 3.99 | ❌ **Insuffisant** — OOM immédiat (Ollama + PG + Qdrant + OS > 2 Go) |
| Value | 4 Go | 5.50 | ⚠️ Minimum viable **avec mem-limits réduits** (§9) ; risque d'OOM sur les 500 prospects (#35) |
| **Essential** | **8 Go** | **10.50** | ✅ **Recommandé** — tient les `mem_limit` du compose, campagne pilote sans OOM |

**Recommandation : Essential 8 Go.** Reste sous le budget VPS prévu (~15–30 €/mois, CLAUDE.md)
et « cancel anytime ». Prendre Ubuntu **22.04 LTS**, région EU (cohérent RGPD / LangSmith EU).

---

## 1. Provisionnement OS + durcissement 🛠️

Connexion initiale en root (mot de passe fourni par OVH), puis :

```bash
# Mises à jour
apt update && apt upgrade -y

# Utilisateur non-root + clé SSH
adduser deploy && usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy   # copie la clé publique

# Pare-feu : tout fermé sauf SSH (les ports DB restent internes, cf. §5)
apt install -y ufw fail2ban
ufw default deny incoming && ufw default allow outgoing
ufw allow OpenSSH && ufw --force enable

# fail2ban : jail sshd par défaut, actif
systemctl enable --now fail2ban
```

Durcir SSH (`/etc/ssh/sshd_config`) puis `systemctl restart ssh` :

```
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
```

> ✅ **Acceptance #33** : SSH par clé uniquement, `ufw` n'ouvre que 22. Les ports 5432/6333
> ne sont **jamais** exposés (liés à `127.0.0.1` par `docker-compose.prod.yml`, cf. §5).

---

## 2. Docker CE 🛠️

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy      # relog pour prendre effet
```

## 3. Python 3.12 pour l'app 🛠️

L'app (`main.py`, scripts) tourne **sur l'hôte** (pas de Dockerfile — décision MVP). Ubuntu 22.04
livre Python 3.10 ; le repo cible 3.12 :

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

## 4. Cloner le repo 🛠️

```bash
sudo mkdir -p /opt && sudo chown deploy:deploy /opt
cd /opt && git clone https://github.com/95902/Agent-IA-de-prospection-B2B-.git prospection-b2b
cd prospection-b2b
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

> ✅ `.gitattributes` force LF sur `*.sh` → pas de piège CRLF sur l'entrypoint Ollama.

## 5. Secrets (`.env`) — hors git 🛠️

Ne **jamais** committer `.env`. Le transférer depuis le poste local :

```bash
# depuis la machine locale
scp .env deploy@<vps-ip>:/opt/prospection-b2b/.env
# sur le VPS
chmod 600 /opt/prospection-b2b/.env
```

⚠️ **Renouveler le jeton Pappers** (celui de dev est expiré → 401). Vérifier que la clé
Claude et `LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com` (compte EU) sont présents.

---

## 6. Déploiement de la stack ✅ (tooling prêt)

```bash
cd /opt/prospection-b2b
make prod            # = docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
make pull-ollama     # télécharge nomic-embed-text (~274 Mo) dans le container Ollama
make status          # tous les services "healthy" ?
make smoke           # scripts/smoke_test.py — 11 tables, Qdrant, Ollama, embedding 768, round-trip
```

- Le schéma SQL (`01_schema.sql`, avec `osm_tags` depuis #103) s'auto-charge au **1er** boot de
  Postgres (volume vide).
- `docker-compose.prod.yml` lie Postgres/Qdrant/Ollama à `127.0.0.1` et met `restart: always` ;
  pgAdmin/Metabase ne sont pas démarrés (pas de profil `dev`/`monitoring`).

## 7. Semer le client pilote 🛠️ (prérequis #35)

```bash
V=/opt/prospection-b2b/.venv/bin/python
cd /opt/prospection-b2b
PYTHONPATH=. $V scripts/seed_icp.py --from-file config/icp_pilote.json   # → CLIENT_ID
PYTHONPATH=. $V scripts/init_icp.py --client-id <CLIENT_ID>              # embarque l'ICP → Qdrant
# Créer la campagne (client + critère + icp_profile → ligne campagnes) : cf. seed_icp / SQL.
# Noter le CAMPAGNE_ID pour le cron (§8).
```

---

## 8. Automatisation (cron) 🛠️ — issues #34 / #41

`crontab -e` (utilisateur `deploy`) :

```cron
# Campagne hebdomadaire — lundi 6h (#34)
0 6 * * 1  /opt/prospection-b2b/scripts/run_campagne.sh <CAMPAGNE_ID> 500 >> /var/log/prospection/campagne.log 2>&1

# Backup PostgreSQL — quotidien 2h (#34, pg_dump compressé → /opt/backups/)
0 2 * * *  cd /opt/prospection-b2b && make backup >> /var/log/prospection/backup.log 2>&1

# Purge RGPD — quotidien 3h (#41, OBLIGATION LÉGALE dès la prod)
0 3 * * *  cd /opt/prospection-b2b && make purge-rgpd >> /var/log/prospection/purge_rgpd.log 2>&1
```

```bash
sudo mkdir -p /var/log/prospection && sudo chown deploy:deploy /var/log/prospection
```

> 🔴 **Le job de purge RGPD (#41) doit être actif dès la mise en service** — pas après. Sans lui,
> la rétention légale (LEGAL.md) n'est pas appliquée.

---

## 9. Réglage mémoire pour un VPS 4 Go (Value) 🛠️

Les `mem_limit` du compose somment à ~7 Go (plafonds, pas des réservations). Sur un VPS 4 Go,
les réduire pour éviter l'OOM sous charge — créer `docker-compose.prod-small.yml` :

```yaml
services:
  ollama:   { mem_limit: 2g }
  postgres: { mem_limit: 1g }
  qdrant:   { mem_limit: 512m }
```

Et déployer avec les trois fichiers :
`docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-small.yml up -d`.
Sur 8 Go (Essential), inutile.

---

## 10. Vérifications finales (acceptance #33)

```bash
make smoke                                   # vert sur le VPS
ls -lh /opt/backups/                          # 1er backup présent après le cron 2h (ou `make backup` manuel)
# Depuis une machine EXTERNE (pas le VPS) :
nmap -Pn <vps-ip> -p 22,5432,6333             # 22 open ; 5432 & 6333 filtered/closed
```

- [ ] `smoke_test.py` vert sur le VPS
- [ ] Scan externe : 5432 (PostgreSQL) et 6333 (Qdrant) **non exposés**
- [ ] Backup automatique confirmé dans `/opt/backups/`
- [ ] Purge RGPD (#41) planifiée en cron

## 11. Restauration d'un backup

```bash
gunzip -c /opt/backups/AAAAMMJJ-HHMM.sql.gz | \
  docker compose exec -T postgres psql -U scraper -d prospection_b2b
```

---

### Récap des dépendances

`#33 (ce runbook)` débloque `#35 (1re campagne)`. `#41 (purge RGPD)` se déploie **avec** la stack
(§8). `run_campagne.sh` (§8) porte `#34`. Le dimensionnement (§0) est à trancher **avant l'achat**.
