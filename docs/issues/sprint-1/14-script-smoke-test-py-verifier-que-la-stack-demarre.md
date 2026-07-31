# #14 — Script smoke_test.py — vérifier que la stack démarre

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/14
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `infrastructure`, `sprint-1`, `tests`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 1 pt
**Labels :** tests, infrastructure, sprint-1

## Objectif
Fournir un script unique qui vérifie en une commande que toute la stack (locale ou VPS) est opérationnelle, utilisé en dev comme en prod (voir #33).

## Fichier
`scripts/smoke_test.py`

## Checks à implémenter
- [ ] PostgreSQL — connexion OK + les 8 tables du schéma (#7) sont présentes
- [ ] Qdrant — connexion OK + les 2 collections (`prospects_embeddings`, `icp_profiles`) existent
- [ ] Ollama — le modèle `nomic-embed-text` est bien chargé
- [ ] Génération d'un embedding de test (via `utils/embeddings.py`, #8) et vérification de la dimension (768)
- [ ] Round-trip BDD : insertion d'un prospect de test via `upsert_prospect` (#9), relecture, suppression du test

## Critères d'acceptance
- [ ] Le script sort en code 0 (vert) si tout est OK, code ≠ 0 sinon avec message explicite par check
- [ ] Passe en vert en local (`make dev`) ET sur le VPS OVH une fois déployé (#33)


