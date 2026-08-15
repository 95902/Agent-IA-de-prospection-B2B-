"""Tests du filtre d'opposition à l'utilisation commerciale (#74). HTTP mocké.

L'enjeu de ces tests n'est pas seulement « le champ est bien lu » : c'est que le
module soit **fermé par défaut**. Un prospect non vérifié ne doit jamais devenir
contactable, quelle que soit la panne (API KO, clé absente, budget épuisé).
"""
from __future__ import annotations

import uuid

import httpx
import pytest

from config.settings import Settings
from models.prospect import Prospect
from utils import opposition_commerciale as oc

CID = uuid.uuid4()

# SIREN réels issus de nos mesures (août 2026). Le modèle Prospect (#10) valide
# le checksum Luhn : des numéros inventés seraient rejetés à la construction.
SIRENS = [
    "322521774",  # BAYARD AUTOMOBILE   — opposée en réel
    "107159691",  # INTEGRAL PARE BRISE — opposée en réel
    "331816140",  # DM MOTORS           — non opposée
    "340505346",  # HUGUES MIHEL        — non opposée
    "313215444",  # GILBERT SERVANS     — non opposée
]


def _prospect(siren=SIRENS[0], nom="BAYARD AUTOMOBILE") -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise=nom, siren=siren)


def _settings(cle="test-key") -> Settings:
    return Settings(pappers_api_key=cle)


def _client(oppose, appels=None) -> httpx.AsyncClient:
    """`oppose` : True / False / None (champ absent de la réponse)."""
    def handler(request):
        if appels is not None:
            appels.append(str(request.url))
        corps = {"siren": "322521774"}
        if oppose is not None:
            corps["opposition_utilisation_commerciale"] = oppose
        return httpx.Response(200, json=corps)
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- Lecture du champ --------------------------------------------------------
@pytest.mark.asyncio
async def test_entreprise_opposee():
    p = _prospect()
    async with _client(True) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert oc.est_oppose(p) is True
    assert oc.peut_etre_contacte(p) is False


@pytest.mark.asyncio
async def test_entreprise_non_opposee():
    p = _prospect()
    async with _client(False) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert oc.est_oppose(p) is False
    assert oc.peut_etre_contacte(p) is True


@pytest.mark.asyncio
async def test_tracabilite_conservee():
    """Une exclusion doit pouvoir être justifiée : valeur, date, source, base légale."""
    p = _prospect()
    async with _client(True) as client:
        await oc.marquer_opposition([p], client, _settings())
    bloc = p.raw_data["opposition_commerciale"]
    assert bloc["oppose"] is True
    assert bloc["source"] == "pappers/entreprise"
    assert "R123-232" in bloc["base_legale"]
    assert bloc["verifie_le"]


# --- Fermé par défaut : le coeur du module -----------------------------------
@pytest.mark.asyncio
async def test_api_en_erreur_rend_le_prospect_non_contactable():
    def handler(request):
        return httpx.Response(500, text="boom")
    p = _prospect()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert oc.est_oppose(p) is False          # on n'a pas prouvé l'opposition
    assert oc.peut_etre_contacte(p) is False  # …mais on ne contacte pas pour autant


@pytest.mark.asyncio
async def test_cle_absente_rend_le_prospect_non_contactable():
    p = _prospect()
    async with _client(False) as client:
        await oc.marquer_opposition([p], client, _settings(cle=""))
    assert oc.peut_etre_contacte(p) is False


@pytest.mark.asyncio
async def test_champ_absent_de_la_reponse_ne_conclut_pas():
    """Pappers pourrait ne pas renvoyer le champ : ce n'est pas une autorisation."""
    p = _prospect()
    async with _client(None) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert p.raw_data["opposition_commerciale"]["oppose"] is None
    assert oc.peut_etre_contacte(p) is False


@pytest.mark.asyncio
async def test_prospect_jamais_verifie_non_contactable():
    """Sans passage par le filtre, aucun prospect n'est contactable."""
    assert oc.peut_etre_contacte(_prospect()) is False
    assert oc.est_oppose(_prospect()) is False


def test_negation_de_est_oppose_nest_pas_une_autorisation():
    """Garde-fou explicite contre le contresens `not est_oppose(p)`."""
    p = _prospect()  # jamais vérifié
    assert not oc.est_oppose(p)            # tentant…
    assert not oc.peut_etre_contacte(p)    # …mais c'est bien celui-ci qui décide


# --- Budget de crédits -------------------------------------------------------
@pytest.mark.asyncio
async def test_budget_epuise_sarrete_sans_rien_autoriser(monkeypatch):
    monkeypatch.setattr(oc, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    prospects = [_prospect(siren=s) for s in SIRENS]
    async with _client(False, appels) as client:
        await oc.marquer_opposition(prospects, client, _settings(), budget_credits=2)
    assert len(appels) == 2                                   # budget respecté
    assert sum(oc.peut_etre_contacte(p) for p in prospects) == 2
    # les 3 restants ne sont ni vérifiés ni contactables
    assert all(not oc.peut_etre_contacte(p) for p in prospects[2:])


@pytest.mark.asyncio
async def test_budget_strict_leve_une_exception(monkeypatch):
    monkeypatch.setattr(oc, "MIN_INTERVAL_S", 0)
    prospects = [_prospect(siren=s) for s in SIRENS[:3]]
    async with _client(False) as client:
        with pytest.raises(oc.BudgetCreditsEpuise):
            await oc.marquer_opposition(prospects, client, _settings(),
                                        budget_credits=1, strict=True)


# --- Cache et volumétrie -----------------------------------------------------
@pytest.mark.asyncio
async def test_un_siren_une_seule_requete(monkeypatch):
    """Plusieurs établissements partagent le SIREN : 1 crédit, pas 3."""
    monkeypatch.setattr(oc, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    prospects = [_prospect(), _prospect(), _prospect()]
    async with _client(True, appels) as client:
        cache = await oc.marquer_opposition(prospects, client, _settings())
    assert len(appels) == 1
    assert len(cache) == 1
    assert all(oc.est_oppose(p) for p in prospects)


@pytest.mark.asyncio
async def test_prospect_sans_siren_ignore(monkeypatch):
    monkeypatch.setattr(oc, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    p = Prospect(campagne_id=CID, nom_entreprise="SANS SIREN")
    async with _client(False, appels) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert appels == []
    assert oc.peut_etre_contacte(p) is False


@pytest.mark.asyncio
async def test_filtrer_contactables(monkeypatch):
    monkeypatch.setattr(oc, "MIN_INTERVAL_S", 0)
    autorise, refuse = _prospect(siren=SIRENS[2]), _prospect(siren=SIRENS[0])

    def handler(request):
        oppose = "322521774" in str(request.url)
        return httpx.Response(200, json={"opposition_utilisation_commerciale": oppose})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await oc.marquer_opposition([autorise, refuse], client, _settings())
    assert oc.filtrer_contactables([autorise, refuse]) == [autorise]


@pytest.mark.asyncio
async def test_raw_data_existant_preserve():
    p = _prospect()
    p.raw_data = {"domiciliation": {"etablissements_a_cette_adresse": 8}}
    async with _client(False) as client:
        await oc.marquer_opposition([p], client, _settings())
    assert p.raw_data["domiciliation"]["etablissements_a_cette_adresse"] == 8
    assert p.raw_data["opposition_commerciale"]["oppose"] is False
