"""Vérification Bloctel (liste rouge) — OBLIGATOIRE LÉGALEMENT (règle #1).

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée.

Rappels légaux (docs/LEGAL.md, CLAUDE.md règle #1) :
- Bloctel OBLIGATOIRE avant tout appel prospect.
- Re-vérification tous les 30 jours max pour tout prospect non encore appelé
  (job récurrent, issue #35 — pas une tâche manuelle).
- Un prospect inscrit Bloctel → non éligible à l'appel (exclu de file_appel).
"""
from __future__ import annotations


async def verifier_bloctel(telephone: str) -> bool:
    """STUB — vérifie un numéro contre la liste Bloctel. À implémenter.

    Returns:
        True si le numéro est appelable (non inscrit Bloctel), False sinon.
    """
    raise NotImplementedError("utils/bloctel non implémenté — voir issue dédiée.")