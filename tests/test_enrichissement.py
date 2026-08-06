"""Tests unitaires du node d'enrichissement (#18).

Couvre l'extraction (regex + mailto + filtre faux positifs), la politique #10
conservée (email générique gardé dans raw_data mais None sur `.email`), l'ordre
de cascade (stop dès email+tél) et le batch. HTTP mocké — aucune vraie API.
"""
from __future__ import annotations

import uuid

import httpx
import pytest

from agents import enrichissement_agent as ea
from agents.enrichissement_agent import (
    Contacts,
    _extract_from_html,
    _extract_from_text,
    enrichissement_node,
)
from models.prospect import Prospect

CID = uuid.uuid4()


def _p(**over) -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise="Garage Test", ville="Paris", **over)


def _fixed_resolver(contacts: Contacts, log: list | None = None, name: str = ""):
    async def _resolver(prospect, client, settings, site_web):
        if log is not None:
            log.append(name)
        return contacts
    return _resolver


# --- Extraction -------------------------------------------------------------
def test_extract_from_text_email_and_phone():
    emails, phones = _extract_from_text("Écrire à jean.dupont@garage-x.fr ou 01 42 55 66 77")
    assert "jean.dupont@garage-x.fr" in emails
    assert phones and "42" in phones[0]


def test_extract_filters_asset_false_positives():
    emails, _ = _extract_from_text("logo image@2x.png sprite@3x.jpg mais vrai@site.fr")
    assert emails == ["vrai@site.fr"]


def test_extract_from_html_prefers_mailto():
    html = '<a href="mailto:contact@garage.fr?subject=x">Nous écrire</a> — tél 06 12 34 56 78'
    emails, phones = _extract_from_html(html)
    assert "contact@garage.fr" in emails
    assert phones  # 06 12 34 56 78 capturé


# --- Politique #10 conservée -----------------------------------------------
@pytest.mark.asyncio
async def test_valid_contact_set_on_prospect(monkeypatch):
    monkeypatch.setattr(ea, "RESOLVERS", [_fixed_resolver(
        Contacts(emails=["jean.dupont@garage-x.fr"], phones=["0612345678"],
                 site_web="http://garage-x.fr", source="tavily")
    )])
    p = _p()
    await ea._enrich_prospect(p, None, ea.get_settings())
    assert p.email == "jean.dupont@garage-x.fr"
    assert p.telephone == "+33612345678"      # normalisé E.164
    assert p.site_web == "http://garage-x.fr"
    assert p.raw_data["enrichissement"]["sources"] == ["tavily"]


@pytest.mark.asyncio
async def test_generic_email_kept_in_rawdata_but_nulled(monkeypatch):
    # contact@ : politique #10 -> None sur .email, MAIS gardé dans raw_data.
    monkeypatch.setattr(ea, "RESOLVERS", [_fixed_resolver(
        Contacts(emails=["contact@garage.fr"], phones=[], source="tavily")
    )])
    p = _p()
    await ea._enrich_prospect(p, None, ea.get_settings())
    assert p.email is None
    assert "contact@garage.fr" in p.raw_data["enrichissement"]["emails"]


# --- Cascade ----------------------------------------------------------------
@pytest.mark.asyncio
async def test_cascade_stops_when_email_and_phone_found(monkeypatch):
    log: list[str] = []
    monkeypatch.setattr(ea, "RESOLVERS", [
        _fixed_resolver(Contacts(emails=["a@b.fr"], phones=["0612345678"], source="r1"), log, "r1"),
        _fixed_resolver(Contacts(emails=["c@d.fr"], phones=["0698765432"], source="r2"), log, "r2"),
    ])
    await ea._enrich_prospect(_p(), None, ea.get_settings())
    assert log == ["r1"]  # r2 jamais appelé


@pytest.mark.asyncio
async def test_cascade_falls_through_when_first_empty(monkeypatch):
    log: list[str] = []
    monkeypatch.setattr(ea, "RESOLVERS", [
        _fixed_resolver(Contacts(source="r1"), log, "r1"),  # rien
        _fixed_resolver(Contacts(emails=["x@y.fr"], phones=["0612345678"], source="r2"), log, "r2"),
    ])
    p = _p()
    await ea._enrich_prospect(p, None, ea.get_settings())
    assert log == ["r1", "r2"]
    assert p.email == "x@y.fr"


# --- Node (batch) -----------------------------------------------------------
@pytest.mark.asyncio
async def test_node_enriches_batch(monkeypatch):
    monkeypatch.setattr(ea, "RESOLVERS", [_fixed_resolver(
        Contacts(emails=["x@y.fr"], phones=["0612345678"], source="tavily")
    )])
    state = {"prospects": [_p(), _p(), _p()]}
    out = await enrichissement_node(state, batch_size=2)
    assert all(p.email == "x@y.fr" and p.telephone == "+33612345678" for p in out["prospects"])


@pytest.mark.asyncio
async def test_node_empty_prospects_noop():
    assert (await enrichissement_node({"prospects": []}))["prospects"] == []


# --- Filtre de précision (page = bonne entreprise) --------------------------
def test_name_matches_domain():
    assert ea._name_matches_domain("Garagex Pro", "garagex.fr")
    assert ea._name_matches_domain("BAYARD AUTOMOBILE", "groupe-bayard.com")
    assert not ea._name_matches_domain("INTEGRAL PARE BRISE", "carygroup.com")
    assert not ea._name_matches_domain("XAVIER SUZZONI", "essec.edu")
    # nom trop générique → non confirmable → False (on préfère ne rien retenir)
    assert not ea._name_matches_domain("Garage Auto", "unsite.fr")


# --- Résolveur Tavily (HTTP mocké) -----------------------------------------
@pytest.mark.asyncio
async def test_tavily_resolver_extracts_when_domain_matches_name():
    def handler(request):
        return httpx.Response(200, json={"results": [
            {"url": "http://essec.edu", "raw_content": "pavie@essec.edu"},          # autre entité → rejeté
            {"url": "http://garagex.fr", "raw_content": "pro@garagex.fr — 01 42 55 66 77"},
        ]})
    prospect = Prospect(campagne_id=CID, nom_entreprise="Garagex Pro", ville="Paris")
    settings = ea.Settings(tavily_api_key="test-key")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        contacts = await ea._resolve_tavily(prospect, client, settings, None)
    assert contacts.emails == ["pro@garagex.fr"]           # essec.edu écarté
    assert contacts.site_web == "http://garagex.fr"
    assert contacts.phones                                 # tél de la page confirmée
