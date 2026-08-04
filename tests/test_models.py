"""Tests des modèles Pydantic v2 (models/prospect.py, models/score.py).

Issue #11 — STUB de tests de structure. Les modèles réels sont implémentés
par l'issue #10 (déjà sur main) : Prospect (validators SIRET/E.164/email) et
ScoreResult (scoring hybride). Ici on valide seulement le contrat Pydantic v2
(sous-classe de BaseModel + champs attendus), pas les validators métier qui
sont couverts par les tests dédiés de #10 / #13.
"""
from __future__ import annotations

from pydantic import BaseModel


def test_prospect_is_pydantic_model() -> None:
    """Prospect est un BaseModel Pydantic v2 avec les champs attendus (règle #7)."""
    from models.prospect import Prospect

    assert issubclass(Prospect, BaseModel)
    # Champs minimaux du contrat Prospect (issue #10) — pas une instanciation
    # (Prospect a des champs requis, on ne le construit pas sans données valides).
    expected = {"siret", "siren", "nom_entreprise", "code_naf"}
    assert expected.issubset(Prospect.model_fields.keys())


def test_score_result_is_pydantic_model() -> None:
    """ScoreResult est un BaseModel Pydantic v2 avec les 3 couches de scoring."""
    from models.score import ScoreResult

    assert issubclass(ScoreResult, BaseModel)
    expected = {"score_regles", "score_llm", "score_embedding", "score_final"}
    assert expected.issubset(ScoreResult.model_fields.keys())