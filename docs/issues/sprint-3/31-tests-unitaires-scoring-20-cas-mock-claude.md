# #31 — Tests unitaires scoring — 20 cas (mock Claude)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/31
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `tests`, `scoring`, `sprint-3`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 2 pts
**Labels :** tests, scoring, sprint-3

## Objectif
Couvrir par des tests unitaires (avec mock Claude, pas d'appel API réel) les 3 couches du scoring (#24, #25, #26) et leur agrégation (#27), avec un ICP de test générique — jamais garage-spécifique, pour vérifier que le scoring fonctionne pour n'importe quel secteur cible.

## Fichier
`tests/test_scoring.py`

## Cas à couvrir (20 cas, avec un ICP de test générique)
- [ ] Prospect qui matche parfaitement l'ICP de test → score > 75
- [ ] Prospect en périphérie de l'ICP (effectif/ancienneté limites) → score < 30
- [ ] Prospect matchant un `mots_cles_negatifs` de test → score = 0
- [ ] Prospect qualifié sans email (téléphone seul) → score 55-70
- [ ] Mock Claude indisponible → fallback règles (voir #23)
- [ ] Deux ICP de test différents (secteurs distincts) sur les mêmes prospects → scores cohérents avec chaque ICP respectif

## Contraintes
- Claude est systématiquement mocké dans ces tests (pas de coût, pas de dépendance réseau) — les tests d'intégration réels avec l'API Claude ne font pas partie de cette issue
- Les fixtures d'ICP de test doivent explicitement couvrir au moins deux secteurs différents, pour prouver la généricité du scoring (CLAUDE.md règle #3)

## Critères d'acceptance
- [ ] `pytest tests/test_scoring.py -v` → 100% de réussite sur les 20 cas
- [ ] Aucun test ne dépend d'une valeur métier codée en dur (NAF, secteur) dans le code de scoring lui-même


