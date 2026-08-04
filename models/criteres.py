"""Modèle Pydantic v2 de l'ICP configurable par client (règle #3, issue #10).

Miroir de la table `criteres_ciblage`. Chargé depuis la BDD par `init_campagne`
(#16), injecté dans `EtatAgent`, puis consommé par le scoring règles (#24).
**Toute** valeur métier (NAF, effectif, mots-clés) vient d'ici — jamais du code.
"""
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CriteresCiblage(BaseModel):
    id: UUID | None = None
    client_id: UUID | None = None
    nom: str
    description_icp: str | None = None
    codes_naf: list[str] = Field(default_factory=list)
    departements: list[str] = Field(default_factory=list)
    effectif_min: int = Field(default=1, ge=0)
    effectif_max: int = Field(default=500)
    anciennete_min_ans: int = Field(default=0, ge=0)
    exiger_site_web: bool = False
    exiger_email: bool = False
    mots_cles_positifs: list[str] = Field(default_factory=list)
    mots_cles_negatifs: list[str] = Field(default_factory=list)
    actif: bool = True

    @model_validator(mode="after")
    def _check_effectifs(self) -> "CriteresCiblage":
        if self.effectif_max < self.effectif_min:
            raise ValueError("effectif_max doit être >= effectif_min.")
        return self
