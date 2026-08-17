# #19 — Implémenter nettoyage_agent.py (dédup + filtres groupes)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/19
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `sprint-2`, `nettoyage`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 2 pts
**Labels :** nettoyage, sprint-2

## Objectif
Nettoyer et filtrer les prospects avant scoring, en appliquant les exclusions **configurables par client** (jamais codées en dur, CLAUDE.md règle #4).

## Fichier
`agents/nettoyage_agent.py`

## Actions
- [ ] **Dédoublonnage** par SIRET (marque `prospects.doublon = TRUE` sur les doublons, ne les supprime pas)
- [ ] **Normalisation E.164** des téléphones (réutilise le validator de #10)
- [ ] **Exclusions client** — applique `criteres_ciblage.mots_cles_negatifs` via `_matche_exclusion` (matching par mot entier, pas sous-chaîne — voir SCORING.md et #24) ; un prospect qui matche → score forcé à 0 en aval
- [ ] **Filtre effectif hors cible** — exclut (ou marque `invalide`) les prospects hors de la fourchette `effectif_min`/`effectif_max` de l'ICP de la campagne

## Contraintes
- Aucune liste de marques/groupes codée en dur — uniquement `criteres_ciblage.mots_cles_negatifs` du client (CLAUDE.md règle #4)

## Critères d'acceptance
- [ ] Aucun doublon SIRET dans `file_appel`
- [ ] Aucun prospect matchant une exclusion ICP de test ne reste `qualifie`


