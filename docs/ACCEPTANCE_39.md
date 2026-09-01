# Relevé d'acceptance — #39 Rétrospective MVP + plan Phase 2 (clôture en review)

> #39 est **livrée** (`docs/RETROSPECTIVE_MVP.md`, PR #124) mais a été **volontairement gardée
> ouverte** (PR #125 = `Refs #39`, pas `Closes`) jusqu'à ce que la **1ʳᵉ vraie campagne de 500**
> (#35) valide ses conclusions sur des données réelles. **Ce run a eu lieu le 2026-09-01 et est
> mesuré ci-dessous.** Ce document débloque la clôture. **Mesuré, pas déclaré.**

## Le run pilote #35 (la condition d'ouverture de #39)

- **Campagne** : « Hôtels indépendants — Paris & Hauts-de-Seine (pilote #35) », NAF 5510Z/5520Z,
  dép 75/92, effectif 2-50 (`CAMPAGNE_ID=b3d7b46e-…`). 500 prospects collectés.
- **Nouveauté clé** : `criteres_ciblage.osm_tags = {tourism=hotel}` **activé pour la 1ʳᵉ fois en
  prod** — c'est le « levier n°1 gratuit » que la rétro avait identifié comme **jamais allumé**
  (cf. `docs/RETROSPECTIVE_MVP.md`, §« OSM jamais activé »).

### Transparence — l'incident et sa réparation (mesuré)

Le 1ᵉʳ passage a tourné avec une **clé Anthropic expirée** : les 500 scorings ont basculé en
**repli règles-only**, `401` capturé, résumé `erreurs: 0`. **Résultat dégradé, aucun signal** —
l'illustration exacte de la leçon de la rétro (« un composant fusionné n'est pas un composant
actif »). Détecté par inspection du log, **pas** par le pipeline. Clé corrigée, puis **re-score en
place des 500** (Claude seul, **0 Tavily** ; réutilise `score_regles`/`score_embedding` déjà
persistés) : **499/500 scorings LLM réels, 1 repli, 0 erreur.**

## Résultat RÉEL mesuré (2026-09-01)

| Métrique | Valeur |
|---|---|
| Prospects collectés | 500 |
| Scorings Claude réels | **499 / 500** (1 repli) |
| **Qualifiés (score_final ≥ 60)** | **72 — 14,4 %** |
| Score moyen (tous / qualifiés) | 42,1 / 70,7 |
| Couverture contact (OSM activé) | **tél 15,8 % · email 14,4 % · site 31,4 %** |

## Ce que ça valide / affine dans la rétro

1. **OSM a enfin tourné.** Couverture en hausse modeste vs le run hôtels sans OSM (14,7 / 12,7 / 27,3)
   — mais la **qualification est restée ~14,4 %** (cible #35 = 30 %). **Conclusion affinée : le goulot
   pour atteindre 30 % n'est PAS la couverture contact (OSM l'a aidée) mais l'adéquation ICP / calibrage
   du scoring.** C'est une direction Phase 2 concrète (recalibrer l'ICP / les poids, pas chasser plus de
   sources d'enrichissement).
2. **La leçon « fusionné ≠ actif » est désormais outillée** : l'incident clé-expirée a produit un
   **garde-fou préflight** (sonde Anthropic + Tavily + INSEE, annule le run si une clé casse) — **PR #128**.

## MàJ 2026-09-01 — tests de suivi (affine la conclusion 1)

Après le pilote, une série de tests a **corrigé la conclusion 1** (goulot = scoring → **goulot = joignabilité**) :

- **Recompute des 500 (0 crédit)** : reweighter vers Claude double les qualifiés-fit (72 → 137) mais les qualifiés
  **joignables** restent ~55. Le **taux actionnable = fit ≥ 60 ET joignable (email/tél) ≈ 11 %** et **ne bouge PAS
  avec les poids**. → le goulot n'est **pas** le scoring.
- **Vrai goulot = la JOIGNABILITÉ** (couverture contact 22 %), qui suit la **taille / visibilité**, pas le secteur.
- **Test secteur** (agences immo 6831Z, 150) : pire — actionnable **2 %** (NAF « sale », beaucoup de SCI/holdings).
- **Test taille** (hôtels effectif ≥ 10, 150, via **PR #130**) : actionnable **19,3 %** (~×2), joignables **33 %**
  (vs 22), qualifiés fit≥60 **24,7 %** (vs 14,4). ✅

**Conclusion Phase 2 corrigée** : le levier du rendement actionnable est de **cibler des établissements ÉTABLIS
(effectif ≥ 10)** et des secteurs riches en présence numérique — **pas** de recalibrer le scoring. Redéfinir
« qualifié » = **fit ET joignable**. ICP gagnant testé = **hôtels effectif ≥ 10** (cf. PR #130). Levier crédits
restant : renouveler Pappers pour enrichir les ~78 % non joignables.

## Portée

- **Document uniquement**, base `main`, PR autonome. **`Closes #39` au merge** (décision équipe).
- Remplace la mise en attente `Refs #39` de la PR #125 : la condition (1ᵉʳ vrai run de 500 mesuré) est
  remplie. Le **§8 (plan Phase 2)** peut être ratifié dans cette même review.
- Suivis ailleurs : **cibler établissements établis / joignabilité** (Phase 2 — cf. MàJ ci-dessus, PR #130),
  garde-fou préflight (#128), renouvellement Pappers pour l'enrichissement.
