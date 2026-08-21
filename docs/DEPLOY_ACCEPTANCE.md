# Relevé d'acceptance — #33 Déploiement stack VPS (prod)

> Preuves de mise en production, à réviser par l'équipe avant clôture de l'issue **#33**.
> Le runbook est dans [`DEPLOY.md`](DEPLOY.md) ; ce document coche sa checklist §10 avec des
> preuves datées, mesurées sur le VPS. **Mesuré, pas déclaré.**

## Cible retenue

**OVH VPS-2** — 4 vCore / **8 Go RAM** / 75 Go NVMe / **Ubuntu 26.04** / EU (Strasbourg),
~8,49 €/mois, Automated Backup (offerte) en filet whole-VM. Sous budget CLAUDE.md (~15–30 €/mois).

- App (`main.py`, scripts) sur l'hôte, **venv `.venv`** (Python système 3.14 d'Ubuntu 26.04).
- Stack conteneurisée via `docker-compose.yml` + `docker-compose.prod.yml`.
- Repo cloné dans `/opt/prospection-b2b`, `HEAD = origin/main` (`907c3ce` au 21/08/2026).

## Checklist acceptance (DEPLOY.md §10)

| # | Critère | Statut | Preuve (datée) |
|---|---|---|---|
| 1 | `smoke_test.py` **vert** sur le VPS | ✅ | **21/08/2026** — 11 tables, 2 collections Qdrant, modèle Ollama `nomic-embed-text` chargé, embedding 768 dims, round-trip BDD OK. « OK — stack opérationnelle. » |
| 2 | Ports 5432 (PostgreSQL) / 6333 (Qdrant) **non exposés** | ✅ | Scan **externe** (machine hors-VPS) le **20/08** : 22 open ; 5432 & 6333 filtered. Confirmé **en interne 21/08** : `ss -tlnp` → `LISTEN 127.0.0.1:5432` et `LISTEN 127.0.0.1:6333` uniquement (binding via `docker-compose.prod.yml`). |
| 3 | Backup automatique confirmé | ✅ | `crontab` `0 2 * * *` (pg_dump gzip → `/opt/backups/`). Backups présents dont **20260821-0200.sql.gz (57 Ko)** — cron exécuté. Rétention `30 2 * * *` (−30 j). |
| 4 | Purge RGPD (#41) planifiée en cron | ✅ | `crontab` `0 3 * * *` → `scripts/purge_rgpd.py` (via `.venv/bin/python`). Obligation légale active dès la prod (LEGAL.md). |

## Durcissement (DEPLOY.md §1)

- **ufw actif**, seul **OpenSSH** autorisé (v4 + v6) ; tout le reste refusé en entrée.
- **fail2ban** actif (jail sshd).
- **Auth SSH par clé** (clé de déploiement dédiée, sans passphrase). Les ports DB ne quittent jamais `127.0.0.1`.
- 3 conteneurs `Up (healthy)` en continu (34 h au moment du relevé).

## Preuve fonctionnelle end-to-end (au-delà de la checklist)

Le pipeline **tourne réellement en prod**, pas seulement « up » :

- **Run de validation** (100 prospects) : 539 s, 0 erreur, vraie API Claude — mesure le débit d'embedding Ollama CPU (inconnue clé pour #35). ✔️
- **Comparaison inter-secteurs** (21/08, 2 × 150 prospects réels) : hôtels 5510Z (839 s) + agences 7311Z (893 s), **0 erreur pipeline**, scoring hybride (règles + Claude + embedding) + persistance OK. A validé la **généralisation multi-secteurs** du produit.

## Crons actifs (tous locaux — 0 appel API, 0 crédit)

```
0 2  * * *   pg_dump gzip        → /opt/backups
30 2 * * *   rétention 30 jours
0 3  * * *   purge RGPD (#41)
```

> 🔴 **Aucun cron consommateur d'API.** Le cron campagne hebdomadaire (**#34**, INSEE+Tavily+Claude)
> reste **volontairement non activé** — à mettre en place seulement avec l'ICP pilote (#35), un
> `--limit` borné et l'accord explicite du porteur (gate crédits). VPS idle = coût fixe seul.

## Reste (hors périmètre #33, suivis ailleurs)

- **#34** cron campagne (gaté crédits + quota Tavily gratuit à surveiller).
- **#35** 1ʳᵉ campagne réelle (décision métier : ICP du vrai client pilote).
- Jeton **Pappers** expiré (401) → opposition commerciale non vérifiée (non bloquant) ; à renouveler.
- Durcissement final optionnel : désactiver `PasswordAuthentication` (auth par clé déjà confirmée).
