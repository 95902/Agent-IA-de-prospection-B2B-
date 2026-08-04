"""Modèle ScoreResult — Pydantic v2 (règle #7).

Issue #11 — STUB. Implémentation détaillée portée par les issues de scoring
(cf. docs/SCORING.md). Porte le résultat du scoring hybride 3 couches :
règles + Claude + embeddings. Le modèle LLM est configurable dans
config/settings.py (jamais codé en dur — règle #6).
"""
from __future__ import annotations

from pydantic import BaseModel


class ScoreResult(BaseModel):
    """STUB — résultat du scoring hybride. À implémenter (issues dédiées)."""

    # TODO: score_regles: int      # 0-100, couche 1
    # TODO: score_llm: int         # 0-100, couche 2 (Claude)
    # TODO: score_embedding: float # 0-1,   couche 3 (Qdrant)
    # TODO: score_final: int       # 0-100, combinaison pondérée
    # TODO: justification_llm: str
    # TODO: prompt_version: str
    pass