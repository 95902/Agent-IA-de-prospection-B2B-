# #17 — Tests intégration Sirene (50 prospects réels)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/17
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `tests`, `sprint-2`, `intégration`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 1 pt
**Labels :** tests, intégration, sprint-2

## Objectif
Valider `sirene_agent.py` (#15) contre la vraie API Sirene INSEE, avec de vraies données, sans dépendre d'un mock qui masquerait un changement de format côté INSEE.

## Fichier
`tests/test_sirene.py`

## Contenu
- [ ] Test avec un ICP de test générique (départements + codes NAF réels), récupération de 50 prospects réels via l'API
- [ ] Vérification : 100% des SIRET retournés sont valides (14 chiffres, cohérents avec le SIREN)
- [ ] Vérification de la pagination (`_fetch_etablissements`) sur un volume > 100 résultats
- [ ] Vérification du comportement sur rate limit 429 (retry avec `sleep 2s`, max 3 tentatives)

## Contraintes
- [ ] Marker pytest `@pytest.mark.integration` — ces tests appellent une vraie API externe et consomment le quota INSEE, ils doivent être **exclus du CI automatique** (30 req/min de rate limit, voir `.env.example` / ARCHITECTURE.md)

## Critères d'acceptance
- [ ] `pytest tests/test_sirene.py -m integration` → 50 prospects réels récupérés, 100% SIRET valides
- [ ] `pytest tests/` (sans le marker `integration`) ignore ces tests


