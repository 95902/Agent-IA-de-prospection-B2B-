# #25 — Prompts Claude scoring LLM générés dynamiquement depuis l'ICP (45%)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/25
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `scoring`, `sprint-3`, `llm`, `prompt-engineering`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 3 pts
**Labels :** scoring, llm, prompt-engineering, sprint-3

## Objectif
Implémenter la 2ᵉ couche du scoring hybride (45% du score final, la plus lourde) : un scoring Claude dont le prompt système est **généré dynamiquement** depuis le profil du client et son ICP, pour que le même agent puisse scorer n'importe quel secteur sans changer une ligne de code.

## Fichiers
`prompts/scorer_system.txt.j2` + `prompts/scorer_user.txt.j2` (templates Jinja, rendus depuis `clients` + `criteres_ciblage`, pas de texte figé) · `agents/scoring_agent.py` → `_score_llm(prospect, criteres, client)`

Voir `docs/SCORING.md` pour les templates complets.

## Implémentation
- [ ] Le prompt système intègre `client.produit_vendu`, `criteres.description_icp`, `criteres.effectif_min/max`, `criteres.anciennete_min_ans` — jamais de secteur ou NAF codé en dur dans le texte du prompt
- [ ] Le prompt utilisateur transmet les données du prospect et exige un JSON strict (`score`, `justification`, `signaux_positifs`, `signaux_negatifs`, `priorite`)
- [ ] Parsing robuste du JSON avec fallback (`score: 50` neutre) si le parsing échoue
- [ ] Prompt caching activé sur le system prompt rendu (`cache_control: {"type": "ephemeral"}`) — un même system prompt sert tous les prospects d'une campagne

## Contraintes
- Modèle Claude configurable via `settings.CLAUDE_SCORING_MODEL`, jamais codé en dur dans le prompt ou le code (CLAUDE.md règle #6)
- Le prompt système ne doit jamais contenir de secteur, code NAF ou mot-clé métier écrit en dur — tout vient du rendu Jinja

## Critères d'acceptance
- [ ] JSON valide 100% (avec fallback si parsing échoue)
- [ ] Coût < 0.003€/prospect (à surveiller via LangSmith, #25 sprint monitoring)
- [ ] `justification` > 20 mots
- [ ] Prompt caching activé sur le system prompt rendu (économie ~90% après le 1er appel de la campagne)


