"""Tests du node Sirene INSEE (agents/sirene_agent.py).

Issue #11 — structure. L'implémentation réelle a été portée par l'issue #15
(PR #62) : `sirene_node` interroge l'API Sirene 3.11 à partir des critères de
l'état. Les tests qui tapent l'API INSEE réelle sont marqués
`@pytest.mark.integration` (exclu des runs par défaut, voir conftest.py).

Ici on ne vérifie que la structure (pas d'API touchée) :
- le node est une coroutine async (règle #8) ;
- il fail-fast si l'état est incomplet (clé `criteres` ou `campagne_id`
  absente) — cohérent avec la règle #3 (aucune valeur ICP par défaut).
"""
from __future__ import annotations

import asyncio
import inspect

import pytest


def test_sirene_node_is_async_coroutine() -> None:
    """sirene_node est bien une coroutine async (règle #8)."""
    from agents.sirene_agent import sirene_node

    assert inspect.iscoroutinefunction(sirene_node)


def test_sirene_node_fail_fast_si_criteres_absents() -> None:
    """Issue #15 — le node fail-fast si l'état n'est pas peuplé (règle #3).

    `sirene_node` lit `state["criteres"]` : un état vide doit lever une erreur
    explicite (KeyError), jamais fallback sur des valeurs par défaut. On
    n'attend plus NotImplementedError depuis que #15 a implémenté le node.
    """
    from agents.sirene_agent import sirene_node

    # État vide : ni `criteres` ni `campagne_id` → KeyError, pas NotImplementedError.
    with pytest.raises(KeyError):
        asyncio.run(sirene_node({}))