# #9 — Initialiser collections Qdrant + utils/db.py

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/9
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `database`, `sprint-1`, `qdrant`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 3 pts
**Labels :** database, qdrant, sprint-1

## Objectif
Fournir la couche d'accès aux données (PostgreSQL + Qdrant) utilisée par tous les nodes du graphe LangChain (#28) et les scripts.

## Fichier
`utils/db.py`

## Fonctions à implémenter
- [ ] `get_pg_pool()` — pool `asyncpg` singleton
- [ ] `get_qdrant()` — `AsyncQdrantClient` singleton
- [ ] `_ensure_collections()` — crée les collections `prospects_embeddings` (768 dims, cosine, HNSW m=16) et `icp_profiles` si absentes, idempotent
- [ ] `upsert_prospect(data: dict) -> str` — `INSERT ... ON CONFLICT (siret) DO UPDATE`
- [ ] `get_file_appel(limit: int) -> list[dict]` — lit la vue `file_appel` (#7)
- [ ] `save_score(prospect_id, score_data)` — insère dans `scores` + met à jour `prospects.score_final/score_regles/score_llm/score_embedding`
- [ ] `upsert_prospect_embedding(prospect_id, embedding, payload)` — payload indexé sur `departement`, `code_naf`, `score_final`, `campagne_id`
- [ ] `search_similar_prospects(query_embedding, top_k, departement?)` — recherche vectorielle Qdrant avec filtre optionnel
- [ ] `get_icp_embedding(icp_id) -> list[float]` — lit le vecteur ICP du client depuis `icp_profiles`

## Contraintes
- Tout est async (`asyncpg`, `AsyncQdrantClient`) — voir CLAUDE.md règle #8
- `_ensure_collections()` ne doit jamais planter si les collections existent déjà

## Critères d'acceptance
- [ ] Premier lancement → 2 collections créées dans Qdrant
- [ ] Deuxième lancement → aucune erreur (idempotent)
- [ ] `upsert_prospect` fonctionne en round-trip (insert puis lecture)


