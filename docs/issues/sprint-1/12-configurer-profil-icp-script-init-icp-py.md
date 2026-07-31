# #12 — Configurer profil ICP + script init_icp.py

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/12
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `ia`, `icp`, `sprint-1`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 1 pt
**Labels :** ia, icp, sprint-1

## Objectif
Fournir le script qui génère l'embedding d'un ICP client (à partir de sa `description_icp` en langage naturel) et le stocke dans Qdrant, pour alimenter la couche 3 du scoring (#26).

## Fichiers
- [ ] `config/icp_seed_example.py` — exemple illustratif pour bootstrap d'un nouveau client (ex. garages indépendants, voir SCORING.md), **pas une valeur par défaut utilisée en prod**
- [ ] `scripts/init_icp.py --client-id <uuid>` — lit `criteres_ciblage.description_icp` du client, génère l'embedding via `utils/embeddings.py` (#8), l'upsert dans la collection Qdrant `icp_profiles` et enregistre le `qdrant_point_id` sur `icp_profiles`

## Contraintes
- Un client = un ICP = une configuration (CLAUDE.md règle #3) : le script ne doit jamais écrire de valeur ICP en dur, tout vient de `criteres_ciblage`
- Doit pouvoir être ré-exécuté si le client modifie sa `description_icp` (ré-upsert, pas de doublon de point Qdrant)

## Critères d'acceptance
- [ ] `python scripts/init_icp.py --client-id <uuid>` → embedding inséré dans Qdrant
- [ ] La collection `icp_profiles` contient bien 1 vecteur pour ce client
- [ ] Une seconde exécution pour le même client met à jour le vecteur existant plutôt que d'en créer un second


