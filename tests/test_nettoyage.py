"""Tests du nettoyage : dédup + Bloctel + filtres (agents/nettoyage_agent.py).

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée.
Couvrira : déduplication (SIRET), vérification Bloctel (mock), exclusion sur
mots-clés négatifs configurés par client (règle #4 — jamais codée en dur).
"""
from __future__ import annotations

import asyncio
import inspect

import pytest


def test_nettoyage_node_is_async_coroutine() -> None:
    """STUB #11 — nettoyage_node est bien une coroutine async (règle #8)."""
    from agents.nettoyage_agent import nettoyage_node

    assert inspect.iscoroutinefunction(nettoyage_node)


def test_nettoyage_node_stub_raises_not_implemented() -> None:
    """STUB #11 — le node lève NotImplementedError (pas une erreur d'import)."""
    from agents.nettoyage_agent import nettoyage_node

    with pytest.raises(NotImplementedError):
        asyncio.run(nettoyage_node({"prospects": []}))