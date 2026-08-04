"""Tests unitaires de `utils/icp_payload.py` (validation Pydantic, sans DB).

Couvre la I/O Matrix du spec : happy path + effectif inversé + aucun
ciblage + NAF mal formé. Aucune dépendance Postgres/Qdrant nécessaire.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from utils.icp_payload import IcpPayload, normalize


def _base() -> dict:
    """Payload minimal valide — chaque test le dérive."""
    return {
        "nom_entreprise": "Cie", "secteur": "s", "produit_vendu": "p",
        "zone_intervention": "z", "nom": "Cible test",
        "codes_naf": ["4520Z"], "departements": ["75"],
        "effectif_min": 2, "effectif_max": 15, "anciennete_min_ans": 3,
    }


# --- Happy path --------------------------------------------------------------

def test_normalize_happy_path():
    p = normalize(_base())
    assert isinstance(p, IcpPayload)
    assert p.codes_naf == ("4520Z",)
    assert p.effectif_min == 2 and p.effectif_max == 15


def test_string_list_coercion():
    """Une chaîne CSV est acceptée et normalisée (ergonomie CLI/fichier)."""
    raw = _base()
    raw["codes_naf"] = "4520Z, 4511Z ,4531Z"
    raw["departements"] = "75,92"
    p = normalize(raw)
    assert p.codes_naf == ("4520Z", "4511Z", "4531Z")
    assert p.departements == ("75", "92")


def test_to_criteres_row_returns_lists():
    p = normalize(_base())
    row = p.to_criteres_row()
    assert row["codes_naf"] == ["4520Z"]
    assert row["effectif_max"] == 15
    assert isinstance(row["codes_naf"], list)


# --- Error cases (I/O Matrix) ------------------------------------------------

def test_effectif_inversed_rejected():
    raw = _base()
    raw["effectif_min"], raw["effectif_max"] = 20, 10
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "effectif_max" in str(exc_info.value)


def test_no_ciblage_rejected():
    """codes_naf ET departements vides → refus (aucun ciblage Sirene possible)."""
    raw = _base()
    raw["codes_naf"] = []
    raw["departements"] = []
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "codes_naf ou departements" in str(exc_info.value)


def test_only_departements_is_valid():
    """Un ICP avec départements mais sans NAF est légitime (ciblage géo pur)."""
    raw = _base()
    raw["codes_naf"] = []
    raw["departements"] = ["75", "92"]
    p = normalize(raw)
    assert p.codes_naf == () and p.departements == ("75", "92")


def test_bad_naf_format_rejected():
    raw = _base()
    raw["codes_naf"] = ["4520"]  # manque la lettre
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "4520" in str(exc_info.value)


def test_bad_departement_rejected():
    raw = _base()
    raw["departements"] = ["7A5"]  # lettre au milieu
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "7A5" in str(exc_info.value)


def test_extra_field_forbidden():
    """`extra='forbid'` : un champ inconnu est rejeté (anti-injection)."""
    raw = _base()
    raw["champ_malveillant"] = "x"
    with pytest.raises(ValidationError):
        normalize(raw)


# --- P3 : effectif négatif rejeté par Pydantic (aligné sur CHECK SQL) -------

def test_effectif_min_negative_rejected():
    raw = _base()
    raw["effectif_min"] = -5
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "effectif_min" in str(exc_info.value)


def test_effectif_max_negative_rejected():
    raw = _base()
    raw["effectif_max"] = -1
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "effectif_max" in str(exc_info.value)


# --- P4 : NAF minuscules normalisés en majuscules ---------------------------

def test_naf_lowercase_normalized():
    raw = _base()
    raw["codes_naf"] = ["4520z"]
    p = normalize(raw)
    assert p.codes_naf == ("4520Z",)


# --- P5 : doublons dédupliqués ----------------------------------------------

def test_duplicates_dedup():
    raw = _base()
    raw["codes_naf"] = ["4520Z", "4520Z", "4511Z"]
    p = normalize(raw)
    assert p.codes_naf == ("4520Z", "4511Z")


# --- P6 : Corse (2A/2B) acceptée --------------------------------------------

def test_corse_departements_accepted():
    raw = _base()
    raw["departements"] = ["2A", "2B"]
    p = normalize(raw)
    assert p.departements == ("2A", "2B")


def test_invalid_corse_variant_rejected():
    """2C n'est pas un département réel → rejeté."""
    raw = _base()
    raw["departements"] = ["2C"]
    with pytest.raises(ValidationError) as exc_info:
        normalize(raw)
    assert "2C" in str(exc_info.value)


# --- P7 : chaînes required vides rejetées (min_length=1) --------------------

def test_empty_nom_rejected():
    raw = _base()
    raw["nom"] = ""
    with pytest.raises(ValidationError):
        normalize(raw)


def test_empty_nom_entreprise_rejected():
    raw = _base()
    raw["nom_entreprise"] = "   "  # strip puis min_length=1
    with pytest.raises(ValidationError):
        normalize(raw)


# --- P8 : cohérence CSV vs liste sur entrées vides --------------------------

def test_list_with_empty_entries_filtered():
    """Une liste JSON avec entrées vides est filtrée (cohérent avec CSV)."""
    raw = _base()
    raw["departements"] = ["75", "", "92"]
    p = normalize(raw)
    assert p.departements == ("75", "92")