# Relevé d'acceptance — #38 Rapport hebdomadaire automatique (Brevo)

> Le **code** de #38 est sur `main` (`scripts/rapport_hebdo.py`, PR **#114**, merge `813fa99`).
> Ce qui manquait pour **fermer l'issue** : la **planification** (cron hebdomadaire sur le VPS) +
> une preuve d'envoi. Ce document coche les deux. **Mesuré sur le VPS le 2026-08-24, pas déclaré.**
> Clôture **au merge** de cette PR (décision équipe, même schéma que [`DEPLOY_ACCEPTANCE.md`](DEPLOY_ACCEPTANCE.md)).

## Ce qui livre #38

| Élément | État | Preuve |
|---|---|---|
| Script `scripts/rapport_hebdo.py` (`--send` via Brevo) | ✅ sur `main` | PR **#114** (`813fa99`), `git ls-tree origin/main -- scripts/rapport_hebdo.py` |
| Secrets Brevo dans `.env` VPS | ✅ présents (valeurs non imprimées) | `BREVO_API_KEY` = SET (len 90) · `RAPPORT_EMAIL_FROM` = SET · `RAPPORT_EMAIL_TO` = SET |
| Dépendance d'envoi | ✅ | `.venv/bin/python -c "import httpx"` → `httpx 0.28.1` |
| **Cron hebdomadaire installé** | ✅ **2026-08-24** | crontab `ubuntu`, voir ci-dessous |
| **Envoi confirmé (run manuel)** | ✅ **2026-08-24** | exit 0, `✓ Rapport envoyé à …` |

## Cron installé (VPS, utilisateur `ubuntu`)

```cron
0 8 * * 1 cd /opt/prospection-b2b && PYTHONPATH=. .venv/bin/python scripts/rapport_hebdo.py --send >> /var/log/prospection/rapport_hebdo.log 2>&1
```

**Lundi 08:00**, après le backup (02:00) et la purge RGPD (03:00). Même convention que le cron
`purge_rgpd` déjà en place (`.venv/bin/python` en direct + `PYTHONPATH=.` + log dédié).

Vérifié — `crontab -l` (utilisateur `ubuntu`) au 2026-08-24 :

```
0 2 * * * docker exec prospection_b2b_postgres pg_dump -U scraper prospection_b2b | gzip > /opt/backups/$(date +\%Y\%m\%d-\%H\%M).sql.gz 2>> /var/log/prospection/backup.log
30 2 * * * find /opt/backups -name "*.sql.gz" -mtime +30 -delete
0 3 * * * cd /opt/prospection-b2b && PYTHONPATH=. .venv/bin/python scripts/purge_rgpd.py >> /var/log/prospection/purge_rgpd.log 2>&1
0 8 * * 1 cd /opt/prospection-b2b && PYTHONPATH=. .venv/bin/python scripts/rapport_hebdo.py --send >> /var/log/prospection/rapport_hebdo.log 2>&1
```

> ⚠️ **Drift doc↔réalité corrigé** : `DEPLOY.md` §8 documentait le crontab pour un utilisateur
> `deploy`, mais le crontab **opérationnel** (backup + purge RGPD) vit sous **`ubuntu`** sur le VPS
> OVH actuel. Le cron #38 a été ajouté **là où les autres tournent déjà** (`ubuntu`), pas dans un
> crontab `deploy` vide. `DEPLOY.md` §8 est mis à jour en conséquence.

## Run manuel de confirmation (2026-08-24)

Commande **identique à celle du cron**, lancée à la main une fois :

```bash
cd /opt/prospection-b2b && PYTHONPATH=. .venv/bin/python scripts/rapport_hebdo.py --send
```

Résultat : **exit 0**, rapport calculé sur les **400 prospects réels** en BDD (37 qualifiés,
score moyen 67,9), puis :

```
✓ Rapport envoyé à mindnesslab1@gmail.com
```

## Sûreté crédits

**0 crédit externe.** Le rapport = **lecture PostgreSQL + un seul appel Brevo** (email). Aucun
Tavily, Claude ni INSEE n'est touché — cohérent avec le gel du pipeline (quota Tavily épuisé
jusqu'au 1ᵉʳ septembre). Le cron peut donc tourner sans surveiller les crédits.

## Portée

- Base `main`, PR autonome (une PR = une base `main`). `Closes #38` **au merge** (décision équipe).
- Modifs repo : `docs/DEPLOY.md` §8 (ligne cron #38 + note) + ce relevé. Le cron lui-même vit sur
  le VPS (infra), documenté ici.
