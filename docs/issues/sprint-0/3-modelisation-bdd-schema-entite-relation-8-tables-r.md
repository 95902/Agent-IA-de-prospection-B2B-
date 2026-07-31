# #3 — Modélisation BDD — schéma entité-relation (8 tables + relations + cardinalités)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/3
> État : ✅ Fermée
> Sprint : Sprint 0 — Conception & Design
> Labels : `sprint-0`, `database`, `conception`, `enattvalidation`

---

**Sprint :** Sprint 0 — Conception & Design (Sem. 0)
**Points :** 2 pts
**Labels :** database, conception, sprint-0

## Objectif
Concevoir le schéma de données complet (PostgreSQL + Qdrant) avant l'écriture du SQL en Sprint 1 (#2 dans docs/ISSUES.md Sprint 1).

## Livrables

- [x] **Diagramme ERD** — 8 tables (clients, criteres_ciblage / icp_profiles, campagnes, prospects, scores, appels, sources, historique) avec relations et cardinalités. Voir `docs/ARCHITECTURE.md` pour la base de départ.
- [x] **Liste des index critiques**, justifiés un par un (ex. index sur `statut`, `score`, `departement`, `code_naf`, index trigram sur les champs texte recherchés)
- [x] **Validation des types de données** : UUID pour les clés primaires, JSONB pour les champs flexibles (ex. mots-clés), arrays PostgreSQL le cas échéant
- [x] **Schéma Qdrant** — 2 collections (`icp_profiles`, `prospects_embeddings` ou équivalent), dimensions des vecteurs (768 pour nomic-embed-text v2), métrique de distance (cosine)

## Contraintes
- Aucune valeur métier (codes NAF, secteur) ne doit apparaître dans le schéma lui-même — les critères de ciblage sont des données, stockées dans `criteres_ciblage` / `icp_profiles`, pas des colonnes fixes par secteur
- Le schéma doit prévoir les colonnes nécessaires à la conformité légale : `bloctel_ok`, `bloctel_verifie_le` (re-vérification 30 jours, voir `docs/LEGAL.md` et issue #35), champs de rétention RGPD (issue #36)

## Critères d'acceptance
- [x] ERD exporté en PNG ou Mermaid, versionné dans le repo (ex. `docs/erd.png` ou `docs/erd.mmd`)
- [x] Toutes les foreign keys documentées (table source, table cible, cardinalité)
- [x] Validé par l'équipe avant l'écriture du SQL (issue #2 du Sprint 1)


