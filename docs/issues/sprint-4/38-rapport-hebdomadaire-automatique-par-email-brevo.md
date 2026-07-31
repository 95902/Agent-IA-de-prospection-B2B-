# #38 — Rapport hebdomadaire automatique par email (Brevo)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/38
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `sprint-4`, `reporting`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 1 pt
**Labels :** reporting, sprint-4

## Objectif
Envoyer chaque semaine un résumé automatique des métriques au client B2B (user story PRD : « je veux recevoir un rapport hebdomadaire par email »), sans intervention manuelle.

## Fichier
`scripts/rapport_hebdo.py`

## Contenu du rapport (par client)
- [ ] Prospects collectés dans la semaine
- [ ] Taux d'enrichissement téléphone/email
- [ ] % de prospects qualifiés (score ≥ 60) et score moyen des qualifiés
- [ ] Nombre d'appels passés et de RDV obtenus (si disponible via Airtable/`appels`)

## Envoi
- [ ] Via Brevo (template email + API)
- [ ] Cron hebdomadaire, lundi 8h (voir #34 pour l'exemple de crontab)

## Critères d'acceptance
- [ ] Le script génère et envoie un email par client actif, avec les bonnes métriques de la semaine écoulée
- [ ] Un client sans activité dans la semaine reçoit un rapport à zéro plutôt qu'aucun email (pas de silence ambigu) — ou ce choix est explicitement documenté si le comportement retenu est différent


