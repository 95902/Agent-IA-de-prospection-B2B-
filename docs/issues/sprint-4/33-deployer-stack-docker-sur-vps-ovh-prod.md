# #33 — Déployer stack Docker sur VPS OVH (prod)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/33
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `déploiement`, `vps`, `sprint-4`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 3 pts
**Labels :** déploiement, vps, sprint-4

## Objectif
Déployer la stack complète (#6) sur le VPS CPU OVH en configuration production sécurisée, avant la première campagne réelle (#35).

## Checklist
- [ ] Ubuntu 22.04 + Docker CE + Docker Compose installés
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- [ ] Hardening : `fail2ban` + `ufw` (uniquement les ports nécessaires ouverts) + authentification SSH par clé uniquement (désactiver mot de passe)
- [ ] Ports 5432 (PostgreSQL) et 6333 (Qdrant) liés à `127.0.0.1` UNIQUEMENT — jamais exposés publiquement
- [ ] Backup PostgreSQL en cron quotidien à 2h (`pg_dump` compressé, voir #34)
- [ ] `scripts/smoke_test.py` (#14) passe en vert sur le VPS

## Contraintes
- Aucun secret (`.env`) commité — transféré au VPS hors git (ex. scp sécurisé ou gestionnaire de secrets)
- Les jobs légaux (#40 re-vérification Bloctel, #41 purge RGPD) doivent être déployés en même temps que la stack, pas après (obligation légale dès la mise en prod)

## Critères d'acceptance
- [ ] Stack accessible et fonctionnelle uniquement depuis le VPS (pas de port DB exposé publiquement, vérifié par un scan externe)
- [ ] `smoke_test.py` vert sur le VPS
- [ ] Premier backup automatique confirmé dans `/opt/backups/`


