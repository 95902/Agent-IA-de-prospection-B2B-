# #20 — Implémenter utils/bloctel.py ⚠️ LÉGAL OBLIGATOIRE

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/20
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `sprint-2`, `légal`, `bloctel`, `compliance`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 2 pts
**Labels :** légal, bloctel, compliance, sprint-2

## ⚠️ Lire LEGAL.md avant de commencer.

## Objectif
Implémenter la vérification Bloctel, obligation légale non négociable avant tout appel (CLAUDE.md règle #1, amende jusqu'à 75 000€ en cas de manquement — voir `docs/LEGAL.md`).

## Fonction
`verifier_batch(numeros: list[str]) -> dict[str, bool]`
- [ ] Format E.164 obligatoire en entrée
- [ ] Batch de max 10 000 numéros par requête (limite API Bloctel)
- [ ] Retry sur timeout (max 3 tentatives)
- [ ] Si l'API est indisponible : ne jamais fallback vers "appelable par défaut" — logger un warning critique et laisser `bloctel_ok = NULL`

## Persistance
- [ ] Mettre à jour `prospects.bloctel_ok` et `prospects.bloctel_verifie_le` après chaque vérification
- [ ] Insérer une ligne d'audit dans `bloctel_verifications` (table déjà présente dans `docker/postgres/init/01_schema.sql`) : `prospect_id`, `telephone`, `resultat`, `reference_bloctel` — trace de preuve en cas de contrôle

## Contraintes
- Trois états possibles pour `bloctel_ok` : `TRUE` (appelable), `FALSE` (interdit, exclu de `file_appel`), `NULL` (non vérifié, également exclu de `file_appel` — voir `docs/LEGAL.md` Règle 2)
- Cette vérification est un prérequis de #14 (nettoyage_agent.py) et sera ré-exécutée tous les 30 jours par le job #35

## Critères d'acceptance
- [ ] 100 numéros vérifiés en < 5s
- [ ] `bloctel_ok = False` exclut systématiquement le prospect de la vue `file_appel`
- [ ] Chaque vérification laisse une trace dans `bloctel_verifications`


