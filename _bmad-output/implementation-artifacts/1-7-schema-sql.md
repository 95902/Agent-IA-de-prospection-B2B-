---
story_key: 1-7-schema-sql
issue: 7
sprint: 1
status: done
baseline_commit: 14c8631
---

# Story 1-7 — Créer le schéma SQL PostgreSQL (8 tables complètes)

> Source : GitHub issue #7 — `docs/issues/sprint-1/7-creer-le-schema-sql-postgresql-8-tables-completes.md`
> Fichier : `docker/postgres/init/01_schema.sql` (préexistant depuis issue #2, vérifié + complété)

## Story

Script SQL d'initialisation exécuté au 1er démarrage PostgreSQL, à partir de
l'ERD validé en Sprint 0 (#3). 8 tables core + tables de compliance (issues
#35/#36), triggers, index critiques, vue `file_appel`, données initiales.

## Acceptance Criteria

- **AC1** — `make psql` + `\dt` → 8 tables présentes ✅ (11 au total : 8 core + 3 compliance)
- **AC2** — Vue `file_appel` requêtable sans erreur ✅ (`SELECT count(*) FROM file_appel` → 0 ligne, OK)
- **AC3** — Ré-exécuter le script sur une base déjà initialisée ne casse rien ✅ (0 ERROR)

## Contraintes

- Aucune valeur métier codée en dur ✅ (criteres_ciblage = seule source ICP)
- `bloctel_ok` nullable (3 états) + `bloctel_verifie_le` TIMESTAMPTZ ✅ (LEGAL.md règle 5)

## Tasks/Subtasks

- [x] T1 — Extensions `uuid-ossp`, `pg_trgm`
- [x] T2 — 8 tables core : clients, criteres_ciblage, icp_profiles, sources, campagnes, prospects, scores, appels (+ 3 compliance : bloctel_verifications, oppositions_rgpd, purge_rgpd_log)
- [x] T3 — Triggers `set_updated_at()` sur clients, campagnes, prospects (+ criteres_ciblage)
- [x] T4 — Index critiques ajoutés : `idx_prospects_score` (DESC), `idx_prospects_bloctel` (partiel WHERE bloctel_ok=TRUE), `idx_prospects_bloctel_verif` (job #40)
- [x] T5 — Vue `file_appel` (statut=qualifie, bloctel_ok=TRUE, vérifié <30j, tel NOT NULL, doublon=FALSE, pas d'opposition RGPD, ORDER BY score_final DESC)
- [x] T6 — Données initiales `sources` (6 entrées : 5 de l'issue + pappers, source légale CLAUDE.md règle #2)
- [x] T7 — Idempotence : CREATE IF NOT EXISTS + INSERT ON CONFLICT DO NOTHING + CREATE OR REPLACE + DROP TRIGGER IF EXISTS avant CREATE TRIGGER
- [x] T8 — Vérification runtime : \dt, vue, ré-exécution, trigger updated_at

## Dev Notes

- Le schéma préexistait (commit 580a089, issue #2). Issue #7 = vérification +
  complétion des index manquants + idempotence des triggers.
- `CREATE TRIGGER` n'a pas de `IF NOT EXISTS` en PostgreSQL → `DROP TRIGGER IF
  EXISTS` + `CREATE TRIGGER` pour la ré-exécution manuelle (AC3).
- Vue `file_appel` plus stricte que l'énoncé #7 (ajoute filtre 30 jours +
  exclusion RGPD) — conforme LEGAL.md règle 5 et issues #35/#36/#40.
- `pappers` ajouté aux sources (CLAUDE.md règle #2 liste Pappers comme source
  légale) ; l'issue #7 n'en listait que 5.

## File List

- `docker/postgres/init/01_schema.sql` (modified)

## Dev Agent Record

### Implementation Plan
Complétion du schéma existant : ajout de 3 index manquants (score DESC,
bloctel partiel, bloctel_verif pour le job 30j), idempotence des triggers via
DROP IF EXISTS, documentation de l'idempotence, commentaire justifiant pappers.

### Debug Log
- Fresh init → 11 tables, 6 sources, vue file_appel requêtable (0 ligne).
- Index prospects : idx_prospects_score, idx_prospects_bloctel,
  idx_prospects_bloctel_verif présents (pg_indexes).
- Ré-exécution du script → DROP TRIGGER x4 + CREATE TRIGGER x4 + CREATE VIEW,
  0 ERROR (AC3 ✅).
- Trigger updated_at : INSERT puis UPDATE → updated_at > created_at (trigger_ok=t).

### Completion Notes
- AC1, AC2, AC3 validés en runtime sur container postgres:16-alpine.
- Aucune valeur métier codée en dur. Sémantique Bloctel 3 états respectée.

## Change Log

- 2026-07-31 — Vérification + complétion schéma (T4 index manquants, T7
  idempotence triggers). AC1-AC3 validés. Status → done.