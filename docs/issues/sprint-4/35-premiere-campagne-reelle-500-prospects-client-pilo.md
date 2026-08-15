# #35 — 🚀 Première campagne réelle — 500 prospects (client pilote)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/35
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `sprint-4`, `campagne`, `production`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 2 pts
**Labels :** campagne, production, sprint-4

## 🚀 Objectif
Lancer la toute première campagne réelle en production pour le client pilote, sur un volume de 500 prospects — validation grandeur nature de tout le pipeline (#1 à #33) avant de généraliser à d'autres clients.

## Config
ICP du client pilote (ex. garages IDF : depts 75,92,93,94, NAF 4520Z,4511Z,4531Z,4532Z) · `limit` 500 — config lue depuis `criteres_ciblage`, jamais en dur dans le script (CLAUDE.md règle #3)

## Déroulé
- [ ] Lancer `python main.py --campagne-id {uuid}` en production (VPS, #28)
- [ ] Suivre l'exécution via LangSmith (#25) et les logs
- [ ] Export CSV des prospects qualifiés en fin de run, pour revue par l'équipe commerciale

## Objectifs quantitatifs
200+ tél (40%) · 100+ emails (20%) · 150+ qualifiés (score ≥ 60) · export CSV livré

## Contraintes
- Si les cibles ne sont pas atteintes, documenter l'écart avant de relancer (ne pas re-tenter en boucle sans diagnostic)

## Critères d'acceptance
- [ ] Les objectifs quantitatifs ci-dessus sont atteints ou l'écart est documenté avec cause probable
- [ ] Le CSV des prospects qualifiés est livré à l'équipe commerciale
- [ ] Aucune anomalie légale (RGPD) constatée sur le run


