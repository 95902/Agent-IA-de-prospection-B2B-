"""Node LangChain — scoring hybride 3 couches (règles + Claude + embeddings).

Issue #11 — STUB. Implémentation détaillée portée par les issues de scoring
(cf. docs/SCORING.md, docs/ISSUES.md).

Rappels (CLAUDE.md règles #5, #6) :
- Embeddings locaux sur CPU via Ollama + nomic-embed-text (utils/embeddings.py).
- LLM scorer en cloud : Claude API uniquement (modèle configurable dans
  config/settings.py, jamais codé en dur dans les prompts).
- Les prompts sont rendus dynamiquement depuis l'ICP du client
  (prompts/scorer_system.txt.j2, prompts/scorer_user.txt.j2).
"""
from __future__ import annotations


async def scoring_node(state: dict) -> dict:
    """STUB — node de scoring hybride. À implémenter (issues dédiées)."""
    raise NotImplementedError("scoring_agent non implémenté — voir issue dédiée.")