"""Modèle Pydantic v2 du prospect (règle #7, issue #10).

Miroir des colonnes de la table `prospects` (`docker/postgres/init/01_schema.sql`),
avec les validators de nettoyage des données scrapées :

- `telephone` / `telephone_2` -> E.164 via `phonenumbers` (None si invalide) ;
- `email` -> validé (lib `email-validator`) puis None si syntaxe KO OU domaine
  blacklisté (cf. `docs/SCORING.md`) — jamais bloquant ;
- `siret` / `siren` -> checksum Luhn via `python-stdnum` (+ exception La Poste) ;
- `to_db_dict()` -> dict natif compatible asyncpg, clés ⊆ whitelist de
  `utils/db.py::_PROSPECT_COLUMNS`.
"""
import re
from datetime import date, datetime
from uuid import UUID

import phonenumbers
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator
from stdnum.fr import siren as _stdnum_siren
from stdnum.fr import siret as _stdnum_siret

# Emails à écarter (score email = 0) — cf. docs/SCORING.md. Mélange de domaines
# et de préfixes de partie locale : matching par sous-chaîne, insensible casse.
EMAIL_BLACKLIST_DOMAINS = (
    "pagesjaunes.fr", "laposte.net", "noreply.", "contact@", "info@", "mairie.",
)

# Statuts autorisés (CHECK de la table prospects).
STATUTS_PROSPECT = (
    "nouveau", "qualifie", "en_attente_appel", "appele", "rdv", "refus",
    "absent", "invalide",
)

# Colonnes émises par to_db_dict — sous-ensemble strict de la whitelist de
# utils/db.py. Exclut les score_* (posés par save_score) et les colonnes
# auto-générées (id, created_at, updated_at).
_DB_FIELDS = {
    "campagne_id", "source_id", "siret", "siren", "nom_entreprise",
    "nom_dirigeant", "code_naf", "libelle_naf", "telephone", "telephone_2",
    "email", "site_web", "adresse", "code_postal", "ville", "departement",
    "latitude", "longitude", "effectif", "effectif_code", "effectif_estime",
    "date_creation", "chiffre_affaire", "statut", "bloctel_ok",
    "bloctel_verifie_le", "doublon", "qdrant_point_id", "notes", "raw_data",
}


def _normalize_phone(raw: str) -> str | None:
    """Numéro FR -> E.164 (`+33…`). None si non parsable ou invalide."""
    try:
        num = phonenumbers.parse(raw, "FR")
    except phonenumbers.NumberParseException:
        return None
    if phonenumbers.is_valid_number(num):
        return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    return None


def _clean_email(raw: str) -> str | None:
    """Email normalisé, ou None si syntaxe invalide ou domaine blacklisté."""
    try:
        normalized = validate_email(raw, check_deliverability=False).normalized
    except EmailNotValidError:
        return None
    if any(token in normalized.lower() for token in EMAIL_BLACKLIST_DOMAINS):
        return None
    return normalized


def _valid_siret(s: str) -> bool:
    """14 chiffres + Luhn, avec l'exception La Poste (SIREN 356000000 :
    somme des 14 chiffres multiple de 5, cf. INSEE)."""
    if not (len(s) == 14 and s.isdigit()):
        return False
    if _stdnum_siret.is_valid(s):
        return True
    return s.startswith("356000000") and sum(int(d) for d in s) % 5 == 0


class Prospect(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Rattachement
    campagne_id: UUID
    source_id: UUID | None = None

    # Identité entreprise
    siret: str | None = None
    siren: str | None = None
    nom_entreprise: str
    nom_dirigeant: str | None = None
    code_naf: str | None = None
    libelle_naf: str | None = None

    # Contact
    telephone: str | None = None
    telephone_2: str | None = None
    email: str | None = None
    site_web: str | None = None

    # Adresse
    adresse: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    departement: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Business
    effectif: str | None = None
    effectif_code: str | None = None
    effectif_estime: int | None = None
    date_creation: date | None = None
    chiffre_affaire: str | None = None

    # Pipeline
    statut: str = "nouveau"
    bloctel_ok: bool | None = None
    bloctel_verifie_le: datetime | None = None
    doublon: bool = False
    qdrant_point_id: UUID | None = None

    # Debug / traçabilité
    notes: str | None = None
    raw_data: dict = Field(default_factory=dict)

    @field_validator("telephone", "telephone_2", mode="before")
    @classmethod
    def _v_phone(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return _normalize_phone(str(v))

    @field_validator("email", mode="before")
    @classmethod
    def _v_email(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return _clean_email(str(v))

    @field_validator("siret", mode="before")
    @classmethod
    def _v_siret(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        s = re.sub(r"\s", "", str(v))
        if not _valid_siret(s):
            raise ValueError("SIRET invalide (14 chiffres + checksum Luhn requis).")
        return s

    @field_validator("siren", mode="before")
    @classmethod
    def _v_siren(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        s = re.sub(r"\s", "", str(v))
        if not (len(s) == 9 and s.isdigit() and _stdnum_siren.is_valid(s)):
            raise ValueError("SIREN invalide (9 chiffres + checksum Luhn requis).")
        return s

    @field_validator("statut")
    @classmethod
    def _v_statut(cls, v: str) -> str:
        if v not in STATUTS_PROSPECT:
            raise ValueError(f"statut invalide : {v!r} (attendu l'un de {STATUTS_PROSPECT}).")
        return v

    def to_db_dict(self) -> dict:
        """dict natif (types Python : UUID, date, dict…) prêt pour asyncpg.
        Clés = sous-ensemble de utils/db.py::_PROSPECT_COLUMNS."""
        return self.model_dump(mode="python", include=_DB_FIELDS)
