# #22 — Test E2E pipeline collecte (100 prospects, ICP pilote)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/22
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `tests`, `sprint-2`, `intégration`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 1 pt
**Labels :** tests, intégration, sprint-2

## Objectif
Valider bout-en-bout la partie « collecte + enrichissement + nettoyage » du pipeline (nodes #15, #16, #18, #19, #21) sur un volume représentatif, avant d'y brancher le scoring en Sprint 3.

## Portée
100 prospects réels, avec l'ICP du client pilote (départements + codes NAF de test).

## Cibles à vérifier
- [ ] ≥ 40% des prospects ont un téléphone (cible PRD)
- [ ] ≥ 20% des prospects ont un email (cible PRD)
- [ ] 0 doublon SIRET dans le résultat final
- [ ] 0 prospect matchant une exclusion ICP (`mots_cles_negatifs`) parmi les prospects `qualifie`
- [ ] Pipeline complet en moins de 10 minutes pour 100 prospects

## Contraintes
- Marker `@pytest.mark.integration` — appelle de vraies APIs externes (Sirene, Tavily, Dropcontact), exclu du CI automatique

## Critères d'acceptance
- [ ] Toutes les cibles ci-dessus sont vérifiées par des assertions automatiques, pas seulement lues manuellement
- [ ] Rapport de run (compteurs par cible) loggé ou exporté pour revue par l'équipe


