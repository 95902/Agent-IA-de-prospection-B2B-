"""Tests de la détection d'adresses de domiciliation (#68). HTTP mocké."""
from __future__ import annotations

import uuid

import httpx
import pytest

from config.settings import Settings
from models.prospect import Prospect
from utils import domiciliation as dom

CID = uuid.uuid4()


def _prospect(numero="47", libelle="VIVIENNE", commune="75102",
              type_voie="RUE", nom="GARAGE TEST") -> Prospect:
    adresse = {}
    if numero is not None:
        adresse["numeroVoieEtablissement"] = numero
    if type_voie is not None:
        adresse["typeVoieEtablissement"] = type_voie
    if libelle is not None:
        adresse["libelleVoieEtablissement"] = libelle
    if commune is not None:
        adresse["codeCommuneEtablissement"] = commune
    return Prospect(campagne_id=CID, nom_entreprise=nom,
                    raw_data={"adresseEtablissement": adresse})


def _settings(seuil=300) -> Settings:
    return Settings(insee_api_key="test-key", domiciliation_seuil=seuil)


def _client(total, compteur=None) -> httpx.AsyncClient:
    def handler(request):
        if compteur is not None:
            compteur.append(str(request.url))
        return httpx.Response(200, json={"header": {"total": total}})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- Extraction de l'adresse ------------------------------------------------
def test_cle_adresse_depuis_champs_bruts():
    cle = dom.cle_adresse(_prospect().raw_data)
    assert cle == dom.AdresseCle("47", "RUE", "VIVIENNE", "75102")


def test_cle_adresse_none_sans_numero():
    """Sans numéro on compterait toute la rue (mesuré : 44 589 vs 42 055)."""
    assert dom.cle_adresse(_prospect(numero=None).raw_data) is None


def test_cle_adresse_none_si_raw_data_vide():
    assert dom.cle_adresse(None) is None
    assert dom.cle_adresse({}) is None


def test_requete_enveloppe_le_champ_periode():
    """`etatAdministratifEtablissement` est un champ période → sinon HTTP 400 (#15)."""
    q = dom._requete(dom.AdresseCle("47", "RUE", "VIVIENNE", "75102"))
    assert "periode(etatAdministratifEtablissement:A)" in q
    assert 'numeroVoieEtablissement:"47"' in q
    assert 'libelleVoieEtablissement:"VIVIENNE"' in q


# --- Marquage ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_marque_adresse_de_domiciliation():
    p = _prospect()
    async with _client(8316) as client:
        await dom.marquer_domiciliation([p], client, _settings())
    assert dom.est_domicilie(p)
    assert p.raw_data["domiciliation"]["etablissements_a_cette_adresse"] == 8316


@pytest.mark.asyncio
async def test_ne_marque_pas_une_adresse_ordinaire():
    p = _prospect(numero="16", libelle="DE MAGDEBOURG", commune="75116")
    async with _client(18) as client:
        await dom.marquer_domiciliation([p], client, _settings())
    assert not dom.est_domicilie(p)
    assert p.raw_data["domiciliation"]["etablissements_a_cette_adresse"] == 18


@pytest.mark.asyncio
async def test_seuil_configurable():
    """Le même comptage change de verdict selon le seuil — pas de constante magique."""
    p_bas, p_haut = _prospect(), _prospect()
    async with _client(200) as client:
        await dom.marquer_domiciliation([p_bas], client, _settings(seuil=100))
        await dom.marquer_domiciliation([p_haut], client, _settings(seuil=1000))
    assert dom.est_domicilie(p_bas)
    assert not dom.est_domicilie(p_haut)


@pytest.mark.asyncio
async def test_adresse_partagee_interrogee_une_seule_fois(monkeypatch):
    """3 prospects à la même adresse → 1 seul appel API (quota Sirene 30/min)."""
    monkeypatch.setattr(dom, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    prospects = [_prospect(nom=f"GARAGE {i}") for i in range(3)]
    async with _client(8316, appels) as client:
        cache = await dom.marquer_domiciliation(prospects, client, _settings())
    assert len(appels) == 1
    assert len(cache) == 1
    assert all(dom.est_domicilie(p) for p in prospects)


@pytest.mark.asyncio
async def test_adresses_distinctes_interrogees_separement(monkeypatch):
    monkeypatch.setattr(dom, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    prospects = [_prospect(numero="47"), _prospect(numero="16", libelle="DE MAGDEBOURG")]
    async with _client(500, appels) as client:
        await dom.marquer_domiciliation(prospects, client, _settings())
    assert len(appels) == 2


@pytest.mark.asyncio
async def test_prospect_sans_numero_est_ignore(monkeypatch):
    monkeypatch.setattr(dom, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    p = _prospect(numero=None)
    async with _client(9999, appels) as client:
        await dom.marquer_domiciliation([p], client, _settings())
    assert appels == []                       # aucun appel inutile
    assert "domiciliation" not in (p.raw_data or {})
    assert not dom.est_domicilie(p)


# --- Dégradation ------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_en_erreur_ne_casse_pas_le_run():
    def handler(request):
        return httpx.Response(500, text="boom")
    p = _prospect()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await dom.marquer_domiciliation([p], client, _settings())
    assert "domiciliation" not in (p.raw_data or {})   # rien marqué à tort
    assert not dom.est_domicilie(p)


@pytest.mark.asyncio
async def test_sans_cle_api_aucun_marquage():
    p = _prospect()
    async with _client(8316) as client:
        await dom.marquer_domiciliation([p], client, Settings(insee_api_key=""))
    assert not dom.est_domicilie(p)


@pytest.mark.asyncio
async def test_raw_data_existant_preserve():
    p = _prospect()
    p.raw_data = {**p.raw_data, "enrichissement": {"emails": ["a@b.fr"]}}
    async with _client(8316) as client:
        await dom.marquer_domiciliation([p], client, _settings())
    assert p.raw_data["enrichissement"] == {"emails": ["a@b.fr"]}
    assert p.raw_data["adresseEtablissement"]["numeroVoieEtablissement"] == "47"
    assert p.raw_data["domiciliation"]["suspecte"] is True
