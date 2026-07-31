# #30 — Configurer LangSmith (traces + coûts LLM)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/30
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `monitoring`, `sprint-3`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 1 pt
**Labels :** monitoring, sprint-3

## Objectif
Tracer chaque exécution du graphe LangChain (#28) — en particulier les appels Claude du scoring (#25) — pour surveiller la latence, les erreurs et le coût par client (voir PRD, persona « admin tech »).

## Configuration
- [ ] Variables d'environnement `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_PROJECT=prospection-b2b` (voir `.env.example` / ARCHITECTURE.md)
- [ ] `utils/logger.py` : initialisation LangSmith au démarrage du pipeline
- [ ] Vérifier que le `client_id`/`campagne_id` apparaît dans les métadonnées de trace pour pouvoir filtrer les coûts par client

## Critères d'acceptance
- [ ] Les traces d'un run `main.py` sont visibles sur smith.langchain.com
- [ ] Le coût (tokens Claude) est visible par run et agrégeable par client


