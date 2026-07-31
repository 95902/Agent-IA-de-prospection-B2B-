# #8 — Configurer Ollama + nomic-embed-text v2 (embeddings CPU)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/8
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `ia`, `sprint-1`, `embeddings`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 2 pts
**Labels :** ia, embeddings, sprint-1

## Objectif
Mettre en place la génération d'embeddings 100% locale sur CPU (aucune API OpenAI, voir CLAUDE.md règle #5), utilisée par la couche 3 du scoring (similarité ICP, voir #26) et par `scripts/init_icp.py` (#12).

## Fichiers
- [ ] Service `ollama` dans `docker-compose.yml` avec volume persistant pour les modèles
- [ ] Script entrypoint qui `ollama pull nomic-embed-text` au démarrage du container (idempotent)
- [ ] `utils/embeddings.py` — `async def get_embedding(text: str) -> list[float]`, appelle `POST http://localhost:11434/api/embed` avec `{"model": "nomic-embed-text", "input": text}`

## Contraintes
- Modèle recommandé MVP : `nomic-embed-text` (137MB, 768 dims, Apache 2.0). `qwen3-embedding` (1024 dims) reste une alternative si besoin de meilleure précision multilingue, à arbitrer plus tard
- Le nom du modèle doit être configurable, pas codé en dur partout où il est utilisé

## Critères d'acceptance
- [ ] `curl -X POST localhost:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'` → vecteur de 768 dimensions
- [ ] `utils/embeddings.py::get_embedding` retourne une liste de 768 floats
- [ ] Temps de réponse < 500ms sur CPU OVH (à mesurer, pas seulement supposer)


