"""Tests des validators Pydantic (models/prospect.py, models/score.py).

Issue #11 — STUB. Implémentation détaillée portée par les issues dédiées
(Sprint 1). Ces tests valident l'état actuel (stubs) : les modèles sont des
BaseModel Pydantic v2 instanciables. Les validators métier (SIRET, E.164,
NAF) viendront avec l'implémentation.
"""
from __future__ import annotations

from pydantic import BaseModel


def test_prospect_is_pydantic_model() -> None:
    """STUB #11 — Prospect est bien un BaseModel Pydantic v2 (règle #7)."""
    from models.prospect import Prospect

    assert issubclass(Prospect, BaseModel)
    # Instanciable sans argument à ce stade (aucun champ requis défini).
    Prospect()


def test_score_result_is_pydantic_model() -> None:
    """STUB #11 — ScoreResult est bien un BaseModel Pydantic v2 (règle #7)."""
    from models.score import ScoreResult

    assert issubclass(ScoreResult, BaseModel)
    ScoreResult()