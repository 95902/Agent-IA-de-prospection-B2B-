"""Tests du node Sirene INSEE (agents/sirene_agent.py).

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée.

À ce stade ce sont des tests de structure stub (pas d'API INSEE touchée) : on
vérifie seulement que le node est une coroutine async et lève
`NotImplementedError`. Quand l'implémentation réelle tapera l'API INSEE, on
ajoutera `@pytest.mark.integration` (exclu des runs par défaut, voir
`conftest.py`) sur les tests qui font de vraies requêtes.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest


def test_sirene_node_is_async_coroutine() -> None:
    """STUB #11 — sirene_node est bien une coroutine async (règle #8)."""
    from agents.sirene_agent import sirene_node

    assert inspect.iscoroutinefunction(sirene_node)


def test_sirene_node_stub_raises_not_implemented() -> None:
    """STUB #11 — le node lève NotImplementedError (pas une erreur d'import)."""
    from agents.sirene_agent import sirene_node

    with pytest.raises(NotImplementedError):
        asyncio.run(sirene_node({}))