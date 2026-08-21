"""DTO Pydantic de l'API de lecture (#116).

Mappent le schéma DB (snake_case) vers des objets de réponse JSON stables pour le
front. Le front garde la responsabilité de son shape d'affichage (Hot/Warm/Cold,
etc.) via un adaptateur — l'API expose des champs domaine, pas de la présentation.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class CampagneDTO(BaseModel):
    id: UUID
    nom: str
    statut: str
    prospects_collectes: int
    prospects_qualifies: int


class ProspectRowDTO(BaseModel):
    """Ligne de la file d'appel (liste)."""
    id: UUID
    nom_entreprise: str
    ville: str | None = None
    departement: str | None = None
    code_naf: str | None = None
    score_final: int
    statut: str
    telephone: str | None = None
    email: str | None = None
    site_web: str | None = None


class ProspectDetailDTO(ProspectRowDTO):
    """Fiche prospect détaillée (+ scores par couche et justification Claude)."""
    nom_dirigeant: str | None = None
    libelle_naf: str | None = None
    telephone_2: str | None = None
    effectif: str | None = None
    adresse: str | None = None
    code_postal: str | None = None
    date_creation: date | None = None
    score_regles: int
    score_llm: int
    score_embedding: float
    justification_llm: str | None = None


class ProspectPage(BaseModel):
    """Page de résultats (pagination)."""
    total: int
    limit: int
    offset: int
    items: list[ProspectRowDTO]


class KPIsDTO(BaseModel):
    portee: str
    collectes: int
    qualifies: int
    taux_tel: float
    taux_email: float
    pct_qualifies: float
    score_moy_qualifies: float | None = None
    cout_estime_eur: float


# --- Corps de requête (écriture, #116 A) ----------------------------------
class OutcomeIn(BaseModel):
    """Résultat d'appel : met à jour prospects.statut."""
    statut: str


class NoteIn(BaseModel):
    note: str


class CampagneCreatedOut(BaseModel):
    client_id: UUID
    critere_id: UUID
    icp_profile_id: UUID
    campagne_id: UUID
    nom: str
