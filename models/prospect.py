"""Modèle Prospect — Pydantic v2 + validators (règle #7).

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée
(Sprint 1). Validators prévus : SIRET (14 chiffres), SIREN (9 chiffres),
téléphone (E.164), code NAF (format NAF/NES). L'ICP (codes NAF, mots-clés…)
ne vit PAS ici — il vient de `criteres_ciblage` en base (règle #3).
"""
from __future__ import annotations

from pydantic import BaseModel


class Prospect(BaseModel):
    """STUB — modèle prospect. À implémenter (issue dédiée)."""

    # TODO: siret: str (validator 14 chiffres)
    # TODO: siren: str (validator 9 chiffres)
    # TODO: nom_entreprise: str
    # TODO: code_naf: str (validator format NAF)
    # TODO: telephone: str | None (validator E.164)
    # ...
    pass