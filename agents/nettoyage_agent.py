"""Node LangChain — nettoyage : dédup + Bloctel + filtres.

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée.

Rappels légaux (CLAUDE.md règle #1, #4) :
- Bloctel OBLIGATOIRE avant tout appel, re-vérification tous les 30 jours max
  pour tout prospect non encore appelé (cf. utils/bloctel.py, issue #35).
- Exclusions configurables par client (`criteres_ciblage.mots_cles_negatifs`),
  jamais de liste codée en dur. Un prospect qui matche une exclusion → score 0.
"""
from __future__ import annotations


async def nettoyage_node(state: dict) -> dict:
    """STUB — node de nettoyage/dédup/Bloctel. À implémenter (issue dédiée)."""
    raise NotImplementedError("nettoyage_agent non implémenté — voir issue dédiée.")