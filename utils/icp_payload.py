"""Modèle de validation d'un payload ICP (Pydantic v2 — règle #7).

Ce module est volontairement découplé de la base de données : il valide et
normalise une configuration ICP *avant* qu'elle n'atteigne `utils/db.py`.
Cela permet de tester la logique de validation sans Postgres (tests unitaires
rapides) et garantit qu'aucune valeur métier n'est insérée en base sans
passer par les contraintes définies ici.

Colonnes cibles : `criteres_ciblage` + `icp_profiles` (voir
`docker/postgres/init/01_schema.sql`). Aucune valeur métier codée en dur
ici (règle #3) — toutes les valeurs proviennent du payload fourni.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Format des codes NAF français : 4 chiffres + 1 lettre majuscule.
_NAF_RE = re.compile(r"^\d{4}[A-Z]$")

# Départements français : 2 chiffres (01-95), Corse (2A, 2B = 1 chiffre + A/B),
# ou 3 chiffres pour les DROM/COM (971-988). Refuse 2C, 1A, 99, etc.
_DEPARTEMENT_RE = re.compile(r"^(\d{2}|2[AB]|\d{3})$")


class IcpPayload(BaseModel):
    """Payload ICP validé, prêt à être inséré en base.

    Représente une configuration de ciblage par client : qui on cherche.
    Ne contient *aucune* valeur métier par défaut — tout vient de l'appelant
    (script CLI, fichier seed, ou futur front). Les valeurs « neutres »
    (effectif_min=1, effectif_max=500) reflètent uniquement les defaults
    techniques du schéma SQL, pas un ICP métier.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # --- Côté client (table `clients`) ---
    nom_entreprise: str = Field(min_length=1)
    secteur: str = Field(min_length=1)
    produit_vendu: str = Field(min_length=1)
    zone_intervention: str = Field(min_length=1)
    contact_nom: Optional[str] = None
    contact_email: Optional[str] = None
    contact_telephone: Optional[str] = None

    # --- Côté critères de ciblage (table `criteres_ciblage`) ---
    nom: str = Field(min_length=1)  # nom du critère (ex. "Garages Île-de-France")
    description_icp: Optional[str] = None
    codes_naf: tuple[str, ...] = ()
    departements: tuple[str, ...] = ()
    effectif_min: int = 1
    effectif_max: int = 500
    anciennete_min_ans: int = 0
    exiger_site_web: bool = False
    exiger_email: bool = False
    mots_cles_positifs: tuple[str, ...] = ()
    mots_cles_negatifs: tuple[str, ...] = ()

    # --- Validateurs ---

    @field_validator("codes_naf", "departements", "mots_cles_positifs",
                     "mots_cles_negatifs", mode="before")
    @classmethod
    def _coerce_tuples(cls, v):
        """Accepte listes/tuples/chaîne CSV en entrée, stocke en tuple immuable.

        Filtre les entrées vides (cohérent entre CSV et liste JSON) et déduplique
        en préservant l'ordre de première occurrence.
        """
        if v is None:
            return ()
        if isinstance(v, str):
            parts = [part.strip() for part in v.split(",")]
        else:
            parts = [str(part).strip() for part in v]
        # Filtrer les vides + dédupliquer en préservant l'ordre.
        seen: set[str] = set()
        out: list[str] = []
        for p in parts:
            if p and p not in seen:
                seen.add(p)
                out.append(p)
        return tuple(out)

    @field_validator("codes_naf")
    @classmethod
    def _validate_codes_naf(cls, v):
        # Normalise en majuscules (ergonomie saisie : "4520z" → "4520Z").
        normalized = tuple(c.upper() for c in v)
        for code in normalized:
            if not _NAF_RE.match(code):
                raise ValueError(
                    f"Code NAF invalide '{code}' — format attendu : 4 chiffres "
                    f"suivis d'une lettre majuscule (ex. 4520Z)."
                )
        return normalized

    @field_validator("departements")
    @classmethod
    def _validate_departements(cls, v):
        for dep in v:
            if not _DEPARTEMENT_RE.match(dep):
                raise ValueError(
                    f"Département invalide '{dep}' — format attendu : 2 chiffres "
                    f"(ex. 75), 2A/2B (Corse), ou 3 chiffres (DROM ex. 974)."
                )
        return v

    @model_validator(mode="after")
    def _validate_consistency(self):
        """Contraintes cross-champs qui ne tiennent pas dans un field_validator."""
        # Bornes d'effectif : alignées sur le CHECK SQL (effectif_min >= 0).
        if self.effectif_min < 0:
            raise ValueError(
                f"effectif_min ({self.effectif_min}) ne peut pas être négatif."
            )
        if self.effectif_max < 0:
            raise ValueError(
                f"effectif_max ({self.effectif_max}) ne peut pas être négatif."
            )
        if self.effectif_max < self.effectif_min:
            raise ValueError(
                f"effectif_max ({self.effectif_max}) < effectif_min "
                f"({self.effectif_min}) — la borne haute doit être >= borne basse."
            )
        if self.anciennete_min_ans < 0:
            raise ValueError(
                f"anciennete_min_ans ({self.anciennete_min_ans}) ne peut pas "
                f"être négatif."
            )
        # Un ICP sans aucun critère de ciblage n'a pas de sens : on n'aurait
        # aucun filtre à appliquer à la source Sirene.
        if not self.codes_naf and not self.departements:
            raise ValueError(
                "Un ICP doit définir au moins un de codes_naf ou departements "
                "(sinon aucun ciblage n'est possible sur la source Sirene)."
            )
        return self

    def to_client_row(self) -> dict:
        """Dict aligné sur les colonnes NOT NULL de `clients`."""
        return {
            "nom_entreprise": self.nom_entreprise,
            "secteur": self.secteur,
            "produit_vendu": self.produit_vendu,
            "zone_intervention": self.zone_intervention,
            "contact_nom": self.contact_nom,
            "contact_email": self.contact_email,
            "contact_telephone": self.contact_telephone,
        }

    def to_criteres_row(self) -> dict:
        """Dict aligné sur `criteres_ciblage` (hors client_id / id / timestamps)."""
        return {
            "nom": self.nom,
            "description_icp": self.description_icp,
            "codes_naf": list(self.codes_naf),
            "departements": list(self.departements),
            "effectif_min": self.effectif_min,
            "effectif_max": self.effectif_max,
            "anciennete_min_ans": self.anciennete_min_ans,
            "exiger_site_web": self.exiger_site_web,
            "exiger_email": self.exiger_email,
            "mots_cles_positifs": list(self.mots_cles_positifs),
            "mots_cles_negatifs": list(self.mots_cles_negatifs),
        }


def normalize(payload: dict) -> IcpPayload:
    """Valide un dict brut et retourne un `IcpPayload` prêt pour la base.

    Lève `pydantic.ValidationError` (avec détails par champ) si le payload
    ne respecte pas les contraintes. Point d'entrée utilisé par `seed_icp.py`.
    """
    return IcpPayload.model_validate(payload)