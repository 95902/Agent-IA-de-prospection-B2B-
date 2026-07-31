# #7 — Créer le schéma SQL PostgreSQL — 8 tables complètes

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/7
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `database`, `sprint-1`, `postgresql`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 3 pts
**Labels :** database, postgresql, sprint-1

## Objectif
Écrire le script SQL d'initialisation exécuté automatiquement au premier démarrage de PostgreSQL, à partir de l'ERD validé en Sprint 0 (#3).

## Fichier
`docker/postgres/init/01_schema.sql`

## Contenu
- [ ] Extensions : `uuid-ossp`, `pg_trgm`
- [ ] 8 tables : `clients`, `criteres_ciblage`, `icp_profiles`, `sources`, `campagnes`, `prospects`, `scores`, `appels` (schéma détaillé dans `docs/ARCHITECTURE.md`)
- [ ] Triggers `set_updated_at()` sur `clients`, `campagnes`, `prospects`
- [ ] Index critiques : `idx_prospects_statut`, `idx_prospects_score` (DESC), `idx_prospects_dept`, `idx_prospects_naf`, `idx_prospects_bloctel` (partiel `WHERE bloctel_ok = TRUE`), `idx_prospects_bloctel_verif` (utilisé par le job #40), `idx_prospects_nom_trgm` (GIN trigram)
- [ ] Vue `file_appel` : `WHERE statut = 'qualifie' AND bloctel_ok = TRUE AND telephone IS NOT NULL AND doublon = FALSE ORDER BY score_final DESC`
- [ ] Données initiales table `sources` (5 entrées : `sirene_insee`, `tavily`, `pages_jaunes`, `dropcontact`, `manuel`)

## Contraintes
- Aucune valeur métier (code NAF, secteur) codée en dur dans le schéma — `criteres_ciblage` reste la seule source de vérité pour l'ICP
- Les colonnes `bloctel_ok` (BOOL, nullable → 3 états) et `bloctel_verifie_le` (TIMESTAMPTZ) doivent respecter la sémantique légale de `docs/LEGAL.md` (Règle 5 : `NULL` = non vérifié = pas d'appel)

## Critères d'acceptance
- [ ] `make psql` puis `\dt` → 8 tables présentes
- [ ] Vue `file_appel` requêtable sans erreur
- [ ] Ré-exécuter le script sur une base déjà initialisée ne casse rien (ou est explicitement non supporté et documenté)


