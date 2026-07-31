# #32 — Audit qualité scores — 100 prospects réels

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/32
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `sprint-3`, `qualité`, `validation`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 2 pts
**Labels :** qualité, validation, sprint-3

## Objectif
Vérifier que le scoring hybride (#24-27) produit des résultats fiables sur des données réelles, avant la première campagne en production (#35). Cible PRD : accord humain/score ≥ 75%.

## Méthodologie
- [ ] Exécuter le pipeline complet sur 100 prospects réels (ICP du client pilote)
- [ ] Export CSV avec `score_final`, les 3 sous-scores, `justification_llm`, `signaux_positifs/negatifs`
- [ ] 20 prospects revus manuellement par l'équipe (accord/désaccord avec le score IA, sans voir le score avant révision — éviter le biais d'ancrage)
- [ ] Calculer le taux d'accord humain/score

## Si accord < 75% (voir SCORING.md, Calibration)
- [ ] Ajuster les poids `config_scoring` (JSONB) **au niveau de la campagne concernée**, jamais globalement
- [ ] Ré-exécuter l'audit sur un nouvel échantillon après ajustement

## Critères d'acceptance
- [ ] CSV d'audit exporté et versionné (ou archivé) pour traçabilité
- [ ] Taux d'accord humain/score ≥ 75%, ou plan d'ajustement documenté si non atteint


