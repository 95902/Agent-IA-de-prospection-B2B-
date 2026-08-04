"""Node LangChain — collecte Sirene INSEE (api-sirene/3.11).

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée
(cf. docs/ISSUES.md Sprint 1). Aucun ICP codé en dur : les critères de ciblage
(codes NAF, effectif, ancienneté, zone) viennent de `criteres_ciblage` en base.

API INSEE — pièges connus (CLAUDE.md) :
- Portail `api-sirene/3.11` (et non l'ancien `entreprises/sirene/V3.11`).
- Header `X-INSEE-Api-Key-Integration` (et non OAuth2).
- 30 req/min.
"""
from __future__ import annotations

# TODO: async def sirene_node(state: EtatAgent) -> EtatAgent:
#     """Collecte les entreprises Sirene selon les critères du client (base)."""
#     ...


async def sirene_node(state: dict) -> dict:
    """STUB — node de collecte Sirene INSEE. À implémenter (issue dédiée)."""
    raise NotImplementedError("sirene_agent non implémenté — voir issue dédiée.")