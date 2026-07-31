# #40 — Job de re-vérification Bloctel (30 jours) ⚠️ LÉGAL OBLIGATOIRE

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/40
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `légal`, `bloctel`, `sprint-4`, `automatisation`, `compliance`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 1 pt
**Labels :** légal, bloctel, compliance, automatisation, sprint-4

## ⚠️ Lire LEGAL.md → Règle 5.

## Objectif
Automatiser la re-vérification Bloctel périodique : un numéro vérifié il y a plus de 30 jours ne doit plus être appelable sans re-vérification (obligation légale, amende jusqu'à 75 000€). Ce point n'était couvert par aucune tâche dans le plan initial — corrigé ici suite à l'audit de conformité.

## Actions
- [ ] Script `scripts/reverifier_bloctel.py` : sélectionne les prospects avec `bloctel_verifie_le` absent ou > 30 jours et appelables (statut `qualifie`/`nouveau`)
- [ ] Réutilise `verifier_batch` (#20) et journalise chaque re-vérification dans `bloctel_verifications` (table d'audit déjà présente dans `docker/postgres/init/01_schema.sql`)
- [ ] Repasse `bloctel_ok = NULL` tant que non re-vérifié (donc exclu de `file_appel` — la vue filtre déjà sur `bloctel_verifie_le > NOW() - INTERVAL '30 days'`)
- [ ] Cron quotidien (`crontab` ou `make cron-bloctel`)
- [ ] Log du nombre de prospects re-vérifiés / repassés en attente

## Contraintes
- Ce job doit être déployé en même temps que la stack de production (#28), pas après — c'est une obligation légale dès la mise en service, pas une amélioration optionnelle

## Critères d'acceptance
- [ ] Un prospect avec `bloctel_verifie_le` > 30 jours disparaît de `file_appel` tant qu'il n'est pas re-vérifié
- [ ] Le job tourne sans intervention manuelle
- [ ] Chaque re-vérification laisse une trace dans `bloctel_verifications`


