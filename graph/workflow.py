"""Graphe LangChain complet — assemblage des 6 nodes (issue #28).

Issue #11 — STUB. L'assemblage réel (StateGraph, edges conditionnels,
points d'entrée/sortie) est porté par #28. `main.py` (#29) appellera
`run()` pour exécuter une campagne.
"""
from __future__ import annotations

from graph.state import EtatAgent


def build_graph():  # type: ignore[no-untyped-def]
    """STUB — construit le StateGraph LangChain. À implémenter (#28)."""
    raise NotImplementedError("graph/workflow.build_graph non implémenté — voir #28.")


async def run(state: EtatAgent) -> EtatAgent:
    """STUB — exécute le graphe complet pour une campagne. À implémenter (#28/#29)."""
    raise NotImplementedError("graph/workflow.run non implémenté — voir #28/#29.")