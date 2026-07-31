# #24 — Scoring règles métier Python générique (35% du score)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/24
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `scoring`, `sprint-3`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 2 pts
**Labels :** scoring, sprint-3

## Objectif
Implémenter la 1ʳᵉ couche du scoring hybride (35% du score final) : un barème Python déterministe, entièrement paramétré par l'ICP de la campagne — aucune constante métier codée en dur. Voir `docs/SCORING.md` pour le barème complet.

## Fichier
`agents/scoring_agent.py` → `_score_regles(prospect: Prospect, criteres: CriteresCiblage) -> int`

## Barème (détail complet dans SCORING.md)
- [ ] Contact (max 35 pts) : téléphone (+25), email non blacklisté (+10)
- [ ] Effectif (max 20 pts) via `_score_effectif(effectif, criteres.effectif_min, criteres.effectif_max)` — pleins points dans la fourchette ICP, dégressif sinon
- [ ] Ancienneté (max 15 pts) via `_score_anciennete(date_creation, criteres.anciennete_min_ans)` — relatif au seuil minimal défini par le client
- [ ] Présence digitale (max 10 pts) : site web, mention "avis google"
- [ ] Géographie (max 10 pts) : bonus si le département du prospect est dans `criteres.departements`
- [ ] Mots-clés positifs (max 10 pts) via `_score_mots_cles_positifs`
- [ ] Pénalités : `_matche_exclusion` (mot entier, pas sous-chaîne) → score forcé à 0 · aucun contact → -20 · NAF hors cible → -30

## Contraintes
- Toutes les valeurs (effectif, ancienneté, exclusions) viennent de `criteres_ciblage`, aucune constante métier codée en dur (CLAUDE.md règle #3)
- `_score_effectif` et `_score_anciennete` doivent être des fonctions pures, testables indépendamment de `_score_regles`

## Critères d'acceptance
- [ ] `_score_effectif` et `_score_anciennete` sont des fonctions pures testées indépendamment (pas de dict jamais lu comme dans une version antérieure du barème)
- [ ] `_matche_exclusion` teste par mot entier normalisé, pas par sous-chaîne (évite les faux positifs, ex. "Carrefour" ne doit pas exclure "Garage du Carrefour")


