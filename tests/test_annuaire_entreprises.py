"""Tests du lookup dirigeant via l'Annuaire des Entreprises (#67). HTTP mocké."""
from __future__ import annotations

import uuid

import httpx
import pytest

from models.prospect import Prospect
from utils import annuaire_entreprises as ann

CID = uuid.uuid4()


def _prospect(siren="428836332", nom="SARL GARAGE DES OEILLETS") -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise=nom, siren=siren)


def _fiche(siren="428836332", dirigeants=None, **extra) -> dict:
    fiche = {"siren": siren, "nom_complet": "SARL GARAGE DES OEILLETS",
             "dirigeants": dirigeants if dirigeants is not None else []}
    fiche.update(extra)
    return fiche


def _client(fiche, appels=None) -> httpx.AsyncClient:
    def handler(request):
        if appels is not None:
            appels.append(str(request.url))
        results = [fiche] if fiche is not None else []
        return httpx.Response(200, json={"results": results, "total_results": len(results)})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# Données réelles observées le 2026-08-08 sur l'API.
PERSONNE_PHYSIQUE = {
    "nom": "LUZINDALALU", "prenoms": "STÉPHANE DOMA YOANNE",
    "annee_de_naissance": "1993", "date_de_naissance": "1993-10",
    "qualite": "Président de SAS", "type_dirigeant": "personne physique",
}
PERSONNE_MORALE = {
    "siren": "812334225", "denomination": "GROUPE OPTIMUM HOLDING",
    "qualite": "Président de SAS", "type_dirigeant": "personne morale",
}
NOM_AVEC_PARENTHESES = {
    "nom": "PEDRO TEIXEIRA (PEDRO TEIXEIRA)", "prenoms": "JOA MANUEL",
    "qualite": "Gérant", "type_dirigeant": "personne physique",
}


# --- Normalisation ----------------------------------------------------------
def test_premier_prenom_seulement():
    """Les enrichisseurs attendent UN prénom, pas l'état civil complet."""
    assert ann._premier_prenom("STÉPHANE DOMA YOANNE") == "STÉPHANE"
    assert ann._premier_prenom("") == ""


def test_nettoie_les_parentheses():
    assert ann._nettoyer("PEDRO TEIXEIRA (PEDRO TEIXEIRA)") == "PEDRO TEIXEIRA"


# --- Extraction -------------------------------------------------------------
def test_extrait_personne_physique():
    d = ann.extraire_dirigeant(_fiche(dirigeants=[PERSONNE_PHYSIQUE]))
    assert d == ann.Dirigeant("STÉPHANE", "LUZINDALALU", "Président de SAS")
    assert d.nom_complet == "STÉPHANE LUZINDALALU"


def test_ignore_personne_morale():
    """Une holding dirigeante ne donne pas d'email nominatif."""
    assert ann.extraire_dirigeant(_fiche(dirigeants=[PERSONNE_MORALE])) is None


def test_prend_la_personne_physique_parmi_plusieurs():
    fiche = _fiche(dirigeants=[PERSONNE_MORALE, PERSONNE_PHYSIQUE])
    assert ann.extraire_dirigeant(fiche).nom == "LUZINDALALU"


def test_aucun_dirigeant():
    assert ann.extraire_dirigeant(_fiche(dirigeants=[])) is None


# --- Enrichissement ---------------------------------------------------------
@pytest.mark.asyncio
async def test_renseigne_nom_dirigeant():
    p = _prospect()
    async with _client(_fiche(dirigeants=[PERSONNE_PHYSIQUE])) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.nom_dirigeant == "STÉPHANE LUZINDALALU"
    d = ann.dirigeant_de(p)
    assert (d.prenom, d.nom) == ("STÉPHANE", "LUZINDALALU")


@pytest.mark.asyncio
async def test_ne_conserve_pas_la_date_de_naissance():
    """Minimisation RGPD : la source expose la naissance, on ne la stocke pas."""
    p = _prospect()
    async with _client(_fiche(dirigeants=[PERSONNE_PHYSIQUE])) as client:
        await ann.enrichir_dirigeants([p], client)
    stocke = p.raw_data["annuaire"]["dirigeant"]
    assert set(stocke) == {"prenom", "nom", "qualite"}
    assert "1993" not in str(stocke)


@pytest.mark.asyncio
async def test_conserve_finances_et_nom_commercial():
    fiche = _fiche(dirigeants=[PERSONNE_PHYSIQUE],
                   finances={"2024": {"ca": 0, "resultat_net": 79731}},
                   siege={"nom_commercial": "GARAGE DU 14E", "liste_enseignes": []})
    p = _prospect()
    async with _client(fiche) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.raw_data["annuaire"]["finances"]["2024"]["resultat_net"] == 79731
    assert p.raw_data["annuaire"]["nom_commercial"] == "GARAGE DU 14E"


@pytest.mark.asyncio
async def test_un_siren_une_seule_requete(monkeypatch):
    monkeypatch.setattr(ann, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    prospects = [_prospect(), _prospect(), _prospect()]
    async with _client(_fiche(dirigeants=[PERSONNE_PHYSIQUE]), appels) as client:
        await ann.enrichir_dirigeants(prospects, client)
    assert len(appels) == 1
    assert all(p.nom_dirigeant == "STÉPHANE LUZINDALALU" for p in prospects)


@pytest.mark.asyncio
async def test_prospect_sans_siren_ignore(monkeypatch):
    monkeypatch.setattr(ann, "MIN_INTERVAL_S", 0)
    appels: list[str] = []
    p = Prospect(campagne_id=CID, nom_entreprise="SANS SIREN")
    async with _client(_fiche(), appels) as client:
        await ann.enrichir_dirigeants([p], client)
    assert appels == []
    assert p.nom_dirigeant is None


@pytest.mark.asyncio
async def test_siren_different_rejete():
    """La recherche plein texte peut renvoyer autre chose : on vérifie le SIREN."""
    p = _prospect(siren="428836332")
    async with _client(_fiche(siren="999999999", dirigeants=[PERSONNE_PHYSIQUE])) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.nom_dirigeant is None


# --- Dégradation ------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_en_erreur_ne_casse_pas_le_run():
    def handler(request):
        return httpx.Response(503, text="indisponible")
    p = _prospect()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.nom_dirigeant is None
    assert "annuaire" not in (p.raw_data or {})


@pytest.mark.asyncio
async def test_raw_data_existant_preserve():
    p = _prospect()
    p.raw_data = {"adresseEtablissement": {"numeroVoieEtablissement": "47"}}
    async with _client(_fiche(dirigeants=[PERSONNE_PHYSIQUE])) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.raw_data["adresseEtablissement"]["numeroVoieEtablissement"] == "47"
    assert p.raw_data["annuaire"]["dirigeant"]["nom"] == "LUZINDALALU"


@pytest.mark.asyncio
async def test_nom_dirigeant_existant_non_ecrase():
    p = _prospect()
    p.nom_dirigeant = "SAISI A LA MAIN"
    async with _client(_fiche(dirigeants=[PERSONNE_PHYSIQUE])) as client:
        await ann.enrichir_dirigeants([p], client)
    assert p.nom_dirigeant == "SAISI A LA MAIN"
