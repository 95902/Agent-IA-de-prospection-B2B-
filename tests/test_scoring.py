"""Tests du scoring hybride (agents/scoring_agent.py + docs/SCORING.md).

Issue #11 — STUB. Implémentation détaillée portée par les issues de scoring.
Couvrira à terme : 20 cas + mock Claude (score règles, score LLM, score
embedding, combinaison pondérée, exclusion mots-clés négatifs → score 0).
"""
from __future__ import annotations

import asyncio
import inspect

import pytest


def test_scoring_node_is_async_coroutine() -> None:
    """STUB #11 — scoring_node est bien une coroutine async (règle #8)."""
    from agents.scoring_agent import scoring_node

    assert inspect.iscoroutinefunction(scoring_node)


def test_scoring_node_stub_raises_not_implemented() -> None:
    """STUB #11 — le node lève NotImplementedError (pas une erreur d'import)."""
    from agents.scoring_agent import scoring_node

    with pytest.raises(NotImplementedError):
        asyncio.run(scoring_node({"prospects": []}))