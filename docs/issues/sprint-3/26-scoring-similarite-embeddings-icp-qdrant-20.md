# #26 — Scoring similarité embeddings ICP Qdrant (20%)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/26
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `scoring`, `sprint-3`, `embeddings`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 2 pts
**Labels :** scoring, embeddings, sprint-3

## Objectif
Implémenter la 3ᵉ couche du scoring hybride (20% du score final) : la similarité cosinus entre l'embedding du prospect et l'embedding de l'ICP du client, tous deux générés localement via Ollama.

## Fichier
`agents/scoring_agent.py` → fonction `_score_embedding(prospect, icp_embedding, ollama_client, qdrant_client) -> float`

## Algorithme (détail complet dans `docs/SCORING.md`, Couche 3)
- [ ] Construire un texte de description générique du prospect (nom, activité, effectif, ville/département, ancienneté, présence site web) — aucun champ spécifique à un secteur
- [ ] Générer l'embedding du prospect via `utils/embeddings.py` (#8)
- [ ] Charger l'embedding ICP du client via `get_icp_embedding` (#9), lui-même généré par `scripts/init_icp.py` (#12)
- [ ] Calculer la similarité cosinus (`numpy`) entre les deux vecteurs
- [ ] Stocker le vecteur du prospect dans Qdrant (`upsert_prospect_embedding`, payload : `nom_entreprise`, `code_naf`, `departement`, `effectif`, `campagne_id`, `score_final`)
- [ ] Retourner un score `[0-100]` (`max(0, similarite) * 100`)

## Critères d'acceptance
- [ ] < 200ms par prospect sur CPU OVH (embedding + calcul de similarité)
- [ ] Le score retourné est toujours dans `[0, 100]`
- [ ] Le vecteur du prospect est bien persisté dans Qdrant après chaque appel


