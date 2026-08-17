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
from models.criteres import CriteresCiblage
from models.prospect import Prospect

CID = uuid.uuid4()


def _p(**over) -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise="Garage Test", ville="Paris", **over)


def _fixed_resolver(contacts: Contacts, log: list | None = None, name: str = ""):
    async def _resolver(prospect, client, settings, site_web, generic):
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
async def test_generic_commercial_email_kept(monkeypatch):
    # #65 / D1 : contact@ (générique commerciale) est désormais accepté sur
    # .email, et toujours conservé dans raw_data.
    monkeypatch.setattr(ea, "RESOLVERS", [_fixed_resolver(
        Contacts(emails=["contact@garage.fr"], phones=[], source="tavily")
    )])
    p = _p()
    await ea._enrich_prospect(p, None, ea.get_settings())
    assert p.email == "contact@garage.fr"
    assert "contact@garage.fr" in p.raw_data["enrichissement"]["emails"]


@pytest.mark.asyncio
async def test_rgpd_email_nulled_but_kept_in_rawdata(monkeypatch):
    # Une boîte RGPD (dpo@) reste mise à None sur .email — pire destinataire —
    # mais est conservée dans raw_data pour traçabilité.
    monkeypatch.setattr(ea, "RESOLVERS", [_fixed_resolver(
        Contacts(emails=["dpo@garage.fr"], phones=[], source="tavily")
    )])
    p = _p()
    await ea._enrich_prospect(p, None, ea.get_settings())
    assert p.email is None
    assert "dpo@garage.fr" in p.raw_data["enrichissement"]["emails"]


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


# --- Vocabulaire non discriminant dérivé de l'ICP (règle #3) ----------------
def _criteres(positifs: list[str], negatifs: list[str] | None = None) -> CriteresCiblage:
    return CriteresCiblage(
        nom="ICP de test",
        mots_cles_positifs=positifs,
        mots_cles_negatifs=negatifs or [],
    )


# ICP pilote « garages » : son vocabulaire sectoriel n'identifie aucun prospect.
GARAGES = ea.generic_tokens(_criteres(["garage", "auto", "pare-brise"], ["groupe"]))


def test_generic_tokens_come_from_icp_not_code():
    assert "garage" in GARAGES and "brise" in GARAGES     # mots-clés ICP
    assert "sarl" in GARAGES                              # boilerplate juridique
    # Rien de sectoriel n'est présent sans l'ICP correspondant.
    assert "garage" not in ea.generic_tokens(None)
    # Un autre ICP → un autre vocabulaire générique.
    boulangeries = ea.generic_tokens(_criteres(["boulangerie", "patisserie"]))
    assert "boulangerie" in boulangeries and "garage" not in boulangeries


# --- Filtre de précision (page = bonne entreprise) --------------------------
def test_name_matches_domain():
    assert ea._name_matches_domain("Garagex Pro", "garagex.fr", GARAGES)
    # token significatif == segment du domaine
    assert ea._name_matches_domain("GARAGE DURAND", "garage-durand.fr", GARAGES)
    # nom concaténé == racine (domaine sans tiret)
    assert ea._name_matches_domain("GARAGE DURAND", "garagedurand.fr", GARAGES)
    assert not ea._name_matches_domain("INTEGRAL PARE BRISE", "carygroup.com", GARAGES)
    assert not ea._name_matches_domain("XAVIER SUZZONI", "essec.edu", GARAGES)
    # nom 100 % sectoriel → non confirmable → False (on préfère ne rien retenir)
    assert not ea._name_matches_domain("Garage Auto", "garage-auto-durand.fr", GARAGES)


@pytest.mark.parametrize("nom,domaine,quoi", [
    ("BAYARD AUTOMOBILE", "groupebayard.com", "Bayard Presse, éditeur"),
    ("AMIN BELFQUIH", "aminkader.com", "marque de mode"),
    ("AUTONOVA", "autonovamtl.com", "concessionnaire à Montréal"),
    ("THOMAS FISCHER", "galeriethomasfischer.de", "galerie d'art allemande"),
])
def test_rejects_measured_false_positives(nom, domaine, quoi):
    """Non-régression : faux positifs réels mesurés sur 15 garages parisiens.

    Tous passaient avec l'ancien match par sous-chaîne (`bayard` ⊂ `groupebayard`).
    Le pire d'entre eux livrait `dpo@groupebayard.com` — le délégué à la
    protection des données d'un éditeur, soit le pire destinataire possible
    pour de la prospection à froid.
    """
    assert not ea._name_matches_domain(nom, domaine, GARAGES), f"{domaine} = {quoi}"


def test_sigle_trop_court_ne_matche_pas():
    """Mesuré sur l'ICP agences : « APF » (3 lettres, aucun token identifiant)
    matchait `apf-francehandicap.org` — une association caritative — via la
    variante concaténée du nom, qui contournait le seuil de longueur."""
    agences = ea.generic_tokens(_criteres(["agence", "communication"]))
    assert not ea._name_matches_domain("APF", "apf-francehandicap.org", agences)
    assert not ea._name_matches_domain("AK", "akillis.com", agences)


def test_tld_etranger_rejete():
    """Un prospect Sirene est français : un ccTLD étranger = autre entité."""
    agences = ea.generic_tokens(_criteres(["agence", "communication"]))
    assert not ea._name_matches_domain("POWER UP", "powerup.at", agences)
    assert not ea._name_matches_domain("THOMAS FISCHER", "thomasfischer.de", GARAGES)
    # les TLD génériques restent acceptés
    assert ea._name_matches_domain("THEMIO", "themio.ai", GARAGES)
    assert ea._name_matches_domain("GARAGE DURAND", "garagedurand.fr", GARAGES)


def test_substring_alone_is_never_enough():
    """Un token inclus dans la racine sans en être un mot entier → rejet."""
    assert not ea._name_matches_domain("MARTIN", "martinelli-immobilier.fr", GARAGES)
    assert not ea._name_matches_domain("NOVA", "novatech-solutions.com", GARAGES)


def test_name_match_depends_on_the_campaign_icp():
    """Le même nom est discriminant ou non selon l'ICP de la campagne."""
    nom, domaine = "Garage Durand", "garage-martin.fr"
    # Campagne garages : « garage » ne discrimine pas → seul « durand » compte
    # → le domaine du garage Martin est bien rejeté.
    assert not ea._name_matches_domain(nom, domaine, GARAGES)
    # Campagne boulangeries : « garage » redevient un token identifiant → match.
    assert ea._name_matches_domain(nom, domaine, ea.generic_tokens(_criteres(["boulangerie"])))


@pytest.mark.asyncio
async def test_node_derives_generic_tokens_from_state_criteres(monkeypatch):
    """Le node passe bien le vocabulaire de l'ICP aux résolveurs."""
    seen: list[frozenset[str]] = []

    async def _resolver(prospect, client, settings, site_web, generic):
        seen.append(generic)
        return Contacts(source="spy")

    monkeypatch.setattr(ea, "RESOLVERS", [_resolver])
    await enrichissement_node({
        "prospects": [_p()],
        "criteres": _criteres(["garage", "atelier"]),
    })
    assert "garage" in seen[0] and "atelier" in seen[0]
    assert "paris" in seen[0]  # la ville du prospect n'identifie personne non plus


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
        contacts = await ea._resolve_tavily(prospect, client, settings, None, GARAGES)
    assert contacts.emails == ["pro@garagex.fr"]           # essec.edu écarté
    assert contacts.site_web == "http://garagex.fr"
    assert contacts.phones                                 # tél de la page confirmée
