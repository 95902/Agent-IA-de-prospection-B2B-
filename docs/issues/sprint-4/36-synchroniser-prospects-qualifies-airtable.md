# #36 — Synchroniser prospects qualifiés → Airtable

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/36
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `sprint-4`, `crm`, `airtable`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 2 pts
**Labels :** crm, airtable, sprint-4

## Objectif
Donner à l'équipe commerciale une vue Airtable des prospects qualifiés, synchronisée automatiquement, sans qu'elle ait besoin d'accéder directement à PostgreSQL.

## Fichier
`utils/airtable_sync.py`

## Comportement
- [ ] **Upsert sur SIRET** — un prospect déjà présent dans Airtable est mis à jour, pas dupliqué
- [ ] **Sync bidirectionnelle du statut** — les actions du commercial dans Airtable (RDV obtenu / Refus / Absent) doivent redescendre vers `prospects.statut` et/ou `appels` en base
- [ ] **Nouveaux qualifiés seulement** — ne pousse vers Airtable que les prospects `statut = 'qualifie'` (pas les `invalide`/`nouveau`)

## Contraintes
- Respecter le rate limit de l'API Airtable (batchs, pas d'appel un par un sur de gros volumes)
- Ne synchroniser que les champs nécessaires au commercial (pas de données brutes internes type `raw_data`)

## Critères d'acceptance
- [ ] Un prospect qualifié apparaît dans Airtable après un run de campagne
- [ ] Un changement de statut fait dans Airtable par le commercial se reflète en base après le prochain sync
- [ ] Aucun doublon créé sur des runs successifs


