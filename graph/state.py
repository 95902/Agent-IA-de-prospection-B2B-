"""État partagé du graphe LangChain (TypedDict).

Issue #11 — STUB. Implémentation détaillée portée par #28.

L'état circule entre les nodes (agents/) et porte les données prospect +
l'ICP du client (chargé depuis `criteres_ciblage` / `icp_profiles` en base,
jamais codé en dur — règle #3). Voir docs/ARCHITECTURE.md.
"""
from __future__ import annotations

from typing import TypedDict


class EtatAgent(TypedDict, total=False):
    """STUB — état partagé du pipeline de prospection.

    Champs prévus (détail dans #28) :
        client_id: UUID du client (icp_profiles).
        criteres: dict des critères de ciblage chargés depuis la base.
        prospects: list[dict] des entreprises collectées/enrichies/scorées.
        erreurs: list[str] des erreurs non fatales rencontrées.
    """

    client_id: str
    criteres: dict
    prospects: list
    erreurs: list