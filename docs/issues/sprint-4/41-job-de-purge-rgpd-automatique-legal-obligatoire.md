# #41 — Job de purge RGPD automatique ⚠️ LÉGAL OBLIGATOIRE

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/41
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `légal`, `sprint-4`, `automatisation`, `compliance`, `rgpd`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 1 pt
**Labels :** légal, rgpd, compliance, automatisation, sprint-4

## ⚠️ Lire LEGAL.md → Durée de conservation.

## Objectif
Automatiser l'application de la politique de rétention RGPD (invalides 6 mois, qualifiés non convertis 3 ans, appels 1 an, logs 3 mois) — documentée dans LEGAL.md mais sans job pour l'appliquer jusqu'ici. Corrigé ici suite à l'audit de conformité.

## Actions
- [ ] Script `scripts/purge_rgpd.py` appliquant les 4 règles de rétention (voir `docs/LEGAL.md`)
- [ ] Anonymisation ou suppression selon le type de donnée
- [ ] Vérifier systématiquement `oppositions_rgpd` avant toute action (un SIRET en opposition ne doit plus jamais être recontacté, indépendamment de la purge) — table déjà présente dans `docker/postgres/init/01_schema.sql`
- [ ] Journal d'audit des suppressions dans `purge_rgpd_log` (`table_cible`, `nb_lignes`, `motif`, déjà présent dans le schéma) — nombre de lignes, motif, date
- [ ] Cron quotidien

## Contraintes
- Ce job doit être déployé en même temps que la stack de production (#28), pas après — c'est une obligation légale dès la mise en service
- Aucune purge manuelle : uniquement via ce job récurrent (CLAUDE.md règle #9)

## Critères d'acceptance
- [ ] Aucun prospect invalide de plus de 6 mois en base après un run
- [ ] Journal d'audit consultable via `purge_rgpd_log`


