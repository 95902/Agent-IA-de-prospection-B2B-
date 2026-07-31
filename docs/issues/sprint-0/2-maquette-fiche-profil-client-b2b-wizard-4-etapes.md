# #2 — Maquette fiche profil client B2B (wizard 4 étapes)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/2
> État : ✅ Fermée
> Sprint : Sprint 0 — Conception & Design
> Labels : `design`, `maquettes`, `sprint-0`, `enattvalidation`

---

**Sprint :** Sprint 0 — Conception & Design (Sem. 0)
**Points :** 2 pts
**Labels :** design, maquettes, sprint-0

## Objectif
Maquetter le parcours de création d'un profil client B2B (wizard) ainsi que la fiche de suivi de ce client, puisque **un client = un ICP = une configuration** (voir CLAUDE.md, règle absolue #3).

## Écrans à concevoir

### Wizard de création (4 étapes)
- [x] **Étape 1 — Informations client** : nom, secteur, contact
- [x] **Étape 2 — Zone & ciblage** : départements, codes NAF, tranche d'effectif
- [x] **Étape 3 — Profil ICP** : description texte libre (utilisée pour l'embedding), mots-clés positifs / négatifs
- [x] **Étape 4 — Confirmation** : résumé des critères saisis + bouton « Créer le client »

### Fiche profil complète
- [x] KPIs du client (prospects collectés, qualifiés, taux de conversion)
- [x] Historique des campagnes lancées
- [x] Coûts associés (API, enrichissement, etc.)

## Contraintes
- Le formulaire doit permettre de saisir **tous** les champs de `criteres_ciblage` (voir #4 et ARCHITECTURE.md) sans qu'aucun ne soit pré-rempli en dur pour un secteur donné
- Cohérence visuelle avec les maquettes de #1

## Critères d'acceptance
- [x] Wizard 4 étapes maquetté et navigable (au moins en export statique)
- [x] Fiche profil complète avec toutes les sections listées ci-dessus
- [x] Validé par l'équipe avant le démarrage du Sprint 1


