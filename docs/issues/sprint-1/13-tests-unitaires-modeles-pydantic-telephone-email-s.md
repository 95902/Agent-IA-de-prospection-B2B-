# #13 — Tests unitaires modèles Pydantic (téléphone, email, SIRET)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/13
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `sprint-1`, `tests`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 1 pt
**Labels :** tests, sprint-1

## Objectif
Couvrir par des tests unitaires tous les validators Pydantic critiques introduits dans #10, avant de bâtir le reste du pipeline dessus.

## Fichier
`tests/test_models.py`

## Cas à couvrir (~20 cas)
- [ ] Téléphone : formats `0612345678`, `+33612345678`, `06 12 34 56 78`, `0033612345678` → tous normalisés en E.164 ; numéro invalide → `ValidationError`
- [ ] Email : formats valides, formats invalides (regex), domaines blacklistés (`pagesjaunes.fr`, `noreply.`, `contact@`, etc.) → `None` plutôt qu'erreur bloquante
- [ ] SIRET : 14 chiffres valides ; 13 ou 15 chiffres, caractères non numériques → `ValidationError`
- [ ] `to_db_dict()` : types retournés compatibles `asyncpg` (pas de `None` sur les champs `NOT NULL`, types Python natifs)

## Critères d'acceptance
- [ ] `pytest tests/test_models.py -v` → 100% de réussite
- [ ] Couverture des trois validators (téléphone, email, SIRET) et de `to_db_dict()`


