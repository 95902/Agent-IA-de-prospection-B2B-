"""Modèle Pydantic v2 du résultat de scoring (règle #7, issue #10).

Agrège les 3 couches du scoring hybride (règles / LLM / embedding) et la sortie
structurée du LLM (justification, signaux, priorité). Voir `docs/SCORING.md`.
"""
from typing import Literal

from pydantic import BaseModel, Field


class ScoreResult(BaseModel):
    # Sous-scores des 3 couches
    score_regles: int = Field(ge=0, le=100)
    score_llm: int = Field(ge=0, le=100)
    score_embedding: float = Field(ge=0.0, le=1.0)  # similarité cosinus
    score_final: int = Field(ge=0, le=100)

    # Sortie structurée du LLM (cf. docs/SCORING.md)
    justification_llm: str = ""
    signaux_positifs: list[str] = Field(default_factory=list)
    signaux_negatifs: list[str] = Field(default_factory=list)
    priorite: Literal["haute", "moyenne", "basse"] = "moyenne"
