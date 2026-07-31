# #27 — Agrégation score final + historique BDD

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/27
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `database`, `scoring`, `sprint-3`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 1 pt
**Labels :** scoring, database, sprint-3

## Objectif
Combiner les 3 couches de scoring (#24 règles, #25 LLM, #26 embedding) en un score final, déterminer le statut du prospect, et persister l'historique complet pour l'audit qualité (#32).

## Formule
```
score_final = round(0.35 × score_regles + 0.45 × score_llm + 0.20 × score_embedding)
score_final = max(0, min(100, score_final))
```
Poids stockés dans `campagnes.config_scoring` (JSONB) — ajustables **par campagne**, jamais globalement (voir SCORING.md, Calibration).

## Implémentation
`agents/scoring_agent.py` → `agreger_et_sauvegarder(prospect, score_regles, score_llm, score_embedding, justification_llm, pool, qdrant_client)`
- [ ] Calcule `score_final` et le `statut` associé : `qualifie` si ≥ 60, `invalide` si < 30, `nouveau` sinon
- [ ] Met à jour `prospects.score_final/score_regles/score_llm/score_embedding` et `statut`
- [ ] Insère une ligne dans `scores` (historique) : les 3 sous-scores, `score_final`, `justification_llm`, `prompt_version`, `details` (JSONB)
- [ ] Si `statut = 'qualifie'`, incrémente `campagnes.prospects_qualifies`

## Critères d'acceptance
- [ ] `score_final` toujours dans `[0, 100]`
- [ ] Chaque scoring génère une ligne d'historique dans `scores`, jamais un simple écrasement sans trace
- [ ] Les seuils de statut (60 / 30) sont respectés exactement


