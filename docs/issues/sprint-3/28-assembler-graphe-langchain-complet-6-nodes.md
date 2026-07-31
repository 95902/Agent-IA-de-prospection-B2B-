# #28 — Assembler graphe LangChain complet (6 nodes)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/28
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `sprint-3`, `workflow`, `langchain`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 3 pts
**Labels :** workflow, langchain, sprint-3

## Objectif
Assembler l'ensemble des nodes développés depuis le Sprint 2 en un graphe LangChain unique, exécutable de bout en bout pour une campagne.

## Fichier
`graph/workflow.py`

## Nodes (dans l'ordre)
```
init_campagne (#16) → fetch_sirene (#15) → enrichir (#18, #21) → nettoyer (#19, #20) → scorer (#24, #25, #26, #27) → sauvegarder
```

## Implémentation
- [ ] Câblage des 6 nodes via l'API graphe de LangChain, état partagé `EtatAgent` (#10)
- [ ] Gestion des erreurs par node (un node qui échoue ne doit pas planter tout le pipeline silencieusement — logger + décider explicitement de continuer ou stopper)
- [ ] **Fallback obligatoire** : si l'API Claude est indisponible pendant le node `scorer`, basculer sur scoring règles uniquement (`score_final = 0.80×règles + 0.20×embedding`, voir SCORING.md « Fallback si Claude API down ») plutôt que de faire échouer toute la campagne

## Critères d'acceptance
- [ ] Pipeline complet exécuté de bout en bout pour 100 prospects en moins de 15 minutes
- [ ] Simulation d'une panne Claude API → le pipeline se termine quand même, avec un score basé sur règles + embedding uniquement


