"""Tests de l'enrichissement email Dropcontact (#21) — utils/dropcontact.py.

Fallback PAYANT : on vérifie surtout la GARDE (éligibilité + opposition) qui décide
quand on dépense, et l'appariement ordonné de la réponse. `soumettre`/`resultat`
sont monkeypatchés — aucun appel réseau, aucun crédit consommé.
"""
from __future__ import annotations

import uuid

import pytest

from utils import dropcontact as dc
from utils.dropcontact import _eligibles, _email_de, _payload, enrichir_emails
from models.prospect import Prospect

CID = uuid.uuid4()


def _p(nom_dirigeant="Jean Dupont", email=None, oppose=False, contactable=True, **o) -> Prospect:
    """Prospect avec verdict d'opposition posé dans raw_data (comme le fait #19).
    `contactable=True` -> oppose=False vérifié ; `contactable=False` -> non vérifié."""
    p = Prospect(campagne_id=CID, nom_entreprise="ACME SAS",
                 nom_dirigeant=nom_dirigeant, email=email, **o)
    if contactable:
        p.raw_data = {"opposition_commerciale": {"oppose": oppose}}
    return p


# --- Garde d'éligibilité ----------------------------------------------------
def test_eligible_si_sans_email_avec_dirigeant_et_contactable():
    assert len(_eligibles([_p()])) == 1


def test_non_eligible_si_email_deja_present():
    assert _eligibles([_p(email="a@b.fr")]) == []


def test_non_eligible_si_pas_de_dirigeant():
    assert _eligibles([_p(nom_dirigeant=None)]) == []


def test_non_eligible_si_oppose():
    # Garde légale : un prospect opposé ne doit jamais partir chez Dropcontact.
    assert _eligibles([_p(oppose=True)]) == []


def test_non_eligible_si_opposition_non_verifiee():
    # Fermé par défaut : non vérifié -> non contactable -> non soumis.
    assert _eligibles([_p(contactable=False)]) == []


# --- Payload / parsing ------------------------------------------------------
def test_payload_full_name_company_siren():
    p = _p(siren="552081317")
    item = _payload([p])[0]
    assert item["full_name"] == "Jean Dupont"
    assert item["company"] == "ACME SAS"
    assert item["num_siren"] == "552081317"


def test_email_de_liste_et_vide():
    assert _email_de({"email": [{"email": "jean.dupont@acme.fr", "qualification": "ok"}]}) == "jean.dupont@acme.fr"
    assert _email_de({"email": []}) is None
    assert _email_de({}) is None


# --- Orchestrateur (réseau mocké) -------------------------------------------
def _mock_api(monkeypatch, data, request_id="rid-1"):
    calls = {"soumis_payload": None}

    async def _soumettre(payload, client, settings):
        calls["soumis_payload"] = payload
        return request_id

    async def _resultat(rid, client, settings, poll_interval=5.0, max_attempts=24):
        return data

    monkeypatch.setattr(dc, "soumettre", _soumettre)
    monkeypatch.setattr(dc, "resultat", _resultat)
    return calls


@pytest.mark.asyncio
async def test_enrichir_pose_email_trouve(monkeypatch):
    _mock_api(monkeypatch, [{"email": [{"email": "jean.dupont@acme.fr"}]}])
    p = _p()
    stats = await enrichir_emails([p], settings=_SettingsAvecCle())
    assert p.email == "jean.dupont@acme.fr"
    assert p.raw_data["dropcontact"]["retenu"] is True
    assert stats == {"eligibles": 1, "soumis": 1, "emails": 1}


@pytest.mark.asyncio
async def test_appariement_ordonne(monkeypatch):
    _mock_api(monkeypatch, [
        {"email": [{"email": "a.un@acme.fr"}]},
        {"email": []},  # 2e sans résultat
    ])
    p1 = _p(nom_dirigeant="A Un")
    p2 = _p(nom_dirigeant="B Deux")
    await enrichir_emails([p1, p2], settings=_SettingsAvecCle())
    assert p1.email == "a.un@acme.fr"
    assert p2.email is None


@pytest.mark.asyncio
async def test_opposes_pas_soumis(monkeypatch):
    calls = _mock_api(monkeypatch, [{"email": [{"email": "x@acme.fr"}]}])
    ok = _p(nom_dirigeant="OK Un")
    oppose = _p(nom_dirigeant="Non Deux", oppose=True)
    await enrichir_emails([ok, oppose], settings=_SettingsAvecCle())
    # Seul le prospect contactable figure dans le payload soumis.
    noms = [i["full_name"] for i in calls["soumis_payload"]]
    assert noms == ["OK Un"]


@pytest.mark.asyncio
async def test_budget_plafonne_les_soumis(monkeypatch):
    calls = _mock_api(monkeypatch, [{"email": []}])
    ps = [_p(nom_dirigeant=f"D {i}") for i in range(5)]
    stats = await enrichir_emails(ps, settings=_SettingsAvecCle(), budget=2)
    assert stats["soumis"] == 2
    assert len(calls["soumis_payload"]) == 2


@pytest.mark.asyncio
async def test_sans_cle_api_ne_soumet_pas(monkeypatch):
    calls = _mock_api(monkeypatch, [{"email": [{"email": "x@acme.fr"}]}])
    p = _p()
    stats = await enrichir_emails([p], settings=_SettingsSansCle())
    assert stats == {"eligibles": 1, "soumis": 0, "emails": 0}
    assert calls["soumis_payload"] is None  # jamais soumis
    assert p.email is None


# --- Doubles de settings ----------------------------------------------------
class _SettingsAvecCle:
    dropcontact_api_key = "test-token"


class _SettingsSansCle:
    dropcontact_api_key = ""
