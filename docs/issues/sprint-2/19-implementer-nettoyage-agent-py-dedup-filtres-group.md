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
Nettoyer et filtrer les prospects avant scoring, en appliquant les exclusions **configurables par client** (jamais codées en dur, CLAUDE.md règle #4) et les contraintes légales (Bloctel).

## Fichier
`agents/nettoyage_agent.py`

## Actions
- [x] **Dédoublonnage** par SIRET (marque `prospects.doublon = TRUE` sur les doublons, ne les supprime pas)
- [x] **Garde d'opposition commerciale** — ⚠️ Bloctel supprimé (loi 2025-594) : remplacé par `utils/opposition_commerciale.py::marquer_opposition` (art. R123-232, `peut_etre_contacte()` fermé par défaut). Budgété en crédits Pappers, exécuté **uniquement sur les survivants** des filtres locaux (min-argent).
- [x] **Exclusions client** — applique `criteres_ciblage.mots_cles_negatifs` via `_matche_exclusion` (matching par mot entier, pas sous-chaîne — voir SCORING.md et #24) ; marqué dans `raw_data['nettoyage']`, score forcé à 0 en aval par le scoring (#24)
- [x] **Filtre effectif hors cible** — marque (ne supprime pas) les prospects hors `effectif_min`/`effectif_max` ; effectif inconnu → non écarté
- [x] **Marquage domiciliation** (#68) intégré à la même passe (qualité)
- [ ] ~~Normalisation E.164~~ : déjà faite par le validator du modèle (#10) à la construction du `Prospect` — pas de re-normalisation ici

## Contraintes
- Aucune liste de marques/groupes codée en dur — uniquement `criteres_ciblage.mots_cles_negatifs` du client (CLAUDE.md règle #4)
- Opposition **fermée par défaut** : un prospect non vérifié n'est pas contactable — `peut_etre_contacte()`, jamais `not est_oppose()` (voir `docs/LEGAL.md`)

## Critères d'acceptance
- [x] Aucun doublon SIRET actif transmis au contact (marqué `doublon = TRUE`)
- [x] Aucun prospect matchant une exclusion ICP de test n'est envoyé aux enrichisseurs tiers / à la file de contact
- [x] Les prospects écartés localement (dédup/exclusion/effectif) ne consomment aucun crédit d'opposition


