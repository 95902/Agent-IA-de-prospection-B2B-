"""Tests unitaires des validators Pydantic des modèles (#13, couvre #10).

Cible : `models/prospect.py` — `telephone` -> E.164, `email` -> None si KO ou
domaine blacklisté, `siret` -> checksum Luhn — ainsi que `to_db_dict()`.
Aucune dépendance Postgres/Qdrant.

Choix assumé (cf. PR #10, option A) : un **téléphone invalide -> None**
(lenient : on garde le prospect, le tél n'est pas une donnée d'identité),
contrairement au **SIRET** (identité) qui lève `ValidationError`. L'issue #13
mentionnait `ValidationError` pour le tél ; on teste le comportement réel
(None), décidé en #10.
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from models import CriteresCiblage, Prospect, ScoreResult
from utils.db import _PROSPECT_COLUMNS

CID = uuid.uuid4()


def _prospect(**over) -> Prospect:
    """Prospect minimal valide (campagne_id + nom_entreprise NOT NULL)."""
    return Prospect(campagne_id=CID, nom_entreprise="Garage Test", **over)


# --- Téléphone : normalisation E.164 ---------------------------------------
@pytest.mark.parametrize(
    "raw", ["0612345678", "+33612345678", "06 12 34 56 78", "0033612345678"]
)
def test_telephone_formats_vers_e164(raw):
    assert _prospect(telephone=raw).telephone == "+33612345678"


@pytest.mark.parametrize("raw", ["", "   ", "abc", "12", "00000000000000"])
def test_telephone_invalide_vers_none(raw):
    assert _prospect(telephone=raw).telephone is None


# --- Email : valide conservé, sinon None -----------------------------------
def test_email_valide_conserve():
    p = _prospect(email="Jean.Dupont@garage-martin.fr")
    assert p.email == "Jean.Dupont@garage-martin.fr"


@pytest.mark.parametrize(
    "raw",
    [
        "contact@garage.fr",       # générique commerciale
        "info@garage.fr",          # générique commerciale
        "reservation@hotel.fr",    # générique commerciale
        "bonjour@studio.fr",       # générique commerciale
        "reception@hotel.fr",      # générique commerciale
    ],
)
def test_email_generique_commerciale_conservee(raw):
    # Décision D1 / #65 : les boîtes génériques commerciales sont valides.
    assert _prospect(email=raw).email == raw


@pytest.mark.parametrize(
    "raw",
    [
        "notanemail",                    # pas de @
        "a@b",                           # domaine sans point
        "x@pagesjaunes.fr",              # domaine blacklisté
        "x@laposte.net",                 # domaine blacklisté
        "no-reply@noreply.io",           # domaine 'noreply.'
        "noreply@garage.fr",             # rôle automatique (domaine propre)
        "dpo@garage.fr",                 # boîte RGPD
        "rgpd@garage.fr",                # boîte RGPD
        "donnees.personnelles@x.fr",     # boîte RGPD (partie locale composée)
        "cnil@x.fr",                     # boîte RGPD
    ],
)
def test_email_invalide_ou_blackliste_vers_none(raw):
    assert _prospect(email=raw).email is None


@pytest.mark.parametrize(
    "raw",
    [
        "adpont@garage.fr",          # 'adpont' contient la sous-chaîne 'dpo'
        "prrgpdupuis@cabinet.fr",    # contient 'rgpd' en sous-chaîne
    ],
)
def test_email_role_pas_de_faux_positif_par_sous_chaine(raw):
    # La comparaison se fait par token (partie locale scindée sur . - _ +),
    # jamais par sous-chaîne : un rôle noyé dans un mot ne déclenche rien.
    assert _prospect(email=raw).email == raw


# --- SIRET : Luhn strict ----------------------------------------------------
def test_siret_valide_accepte():
    # 73282932000074 : SIRET Luhn-valide (exemple python-stdnum), espaces nettoyés.
    assert _prospect(siret="732 829 320 00074").siret == "73282932000074"


def test_siret_exception_la_poste():
    # SIREN 356000000 : somme des 14 chiffres multiple de 5 (dérogation INSEE).
    assert _prospect(siret="35600000000001").siret == "35600000000001"


@pytest.mark.parametrize(
    "raw",
    [
        "1234567890123",    # 13 chiffres
        "123456789012345",  # 15 chiffres
        "1234567890123A",   # caractère non numérique
        "12345678901234",   # 14 chiffres mais checksum Luhn KO
    ],
)
def test_siret_invalide_leve(raw):
    with pytest.raises(ValidationError):
        _prospect(siret=raw)


# --- statut -----------------------------------------------------------------
def test_statut_invalide_leve():
    with pytest.raises(ValidationError):
        _prospect(statut="statut_inexistant")


# --- to_db_dict() : compatibilité asyncpg -----------------------------------
def test_to_db_dict_not_null_et_types_natifs():
    p = _prospect(
        siret="73282932000074", telephone="0612345678",
        date_creation=date(2020, 1, 1), raw_data={"src": "x"},
    )
    d = p.to_db_dict()
    # Colonnes NOT NULL renseignées
    assert d["campagne_id"] is not None
    assert d["nom_entreprise"] == "Garage Test"
    # Types Python natifs (pas de types Pydantic) pour asyncpg
    assert isinstance(d["campagne_id"], uuid.UUID)
    assert isinstance(d["date_creation"], date)
    assert isinstance(d["raw_data"], dict)


def test_to_db_dict_clefs_sous_ensemble_whitelist():
    assert set(_prospect().to_db_dict()) <= set(_PROSPECT_COLUMNS)


def test_to_db_dict_exclut_les_scores():
    assert not any(k.startswith("score") for k in _prospect().to_db_dict())


# --- Modèles connexes -------------------------------------------------------
def test_criteres_effectif_incoherent_leve():
    with pytest.raises(ValidationError):
        CriteresCiblage(nom="cible", effectif_min=10, effectif_max=5)


def test_score_hors_bornes_leve():
    with pytest.raises(ValidationError):
        ScoreResult(score_regles=150, score_llm=0, score_embedding=0.5, score_final=0)
