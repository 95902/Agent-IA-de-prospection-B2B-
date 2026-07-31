# #34 — Configurer cron campagnes automatiques (lundi 6h)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/34
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `sprint-4`, `automatisation`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 1 pt
**Labels :** automatisation, sprint-4

## Objectif
Automatiser le lancement hebdomadaire des campagnes et la sauvegarde de la base, pour que le pipeline tourne sans intervention manuelle une fois en production (#28).

## Crontab
```bash
0 6 * * 1 cd /opt/prospection_b2b && python main.py --campagne-id {uuid} >> /var/log/prospection_b2b.log 2>&1
0 2 * * * docker exec prospection_b2b_postgres pg_dump -U scraper prospection_b2b | gzip > /opt/backups/$(date +%Y%m%d).sql.gz
```

## Actions
- [ ] Installer la crontab sur le VPS (root ou utilisateur dédié `prospection`)
- [ ] `scripts/run_campagne.sh` en wrapper : gère le logging, le code retour, et alerte (log critique) en cas d'échec
- [ ] Rotation des logs (`/var/log/prospection_b2b.log`) pour éviter une croissance illimitée
- [ ] Rotation des backups (`/opt/backups/`) — conserver une profondeur raisonnable, pas une purge manuelle

## Contraintes
- Le `campagne-id` par cron reste propre à chaque client actif — pas de campagne générique codée en dur (CLAUDE.md règle #3)
- Un échec du run hebdomadaire doit être visible (log + éventuellement alerte), pas silencieux

## Critères d'acceptance
- [ ] La campagne se lance automatiquement chaque lundi à 6h sans intervention manuelle
- [ ] Un backup PostgreSQL compressé est généré chaque nuit à 2h dans `/opt/backups/`


