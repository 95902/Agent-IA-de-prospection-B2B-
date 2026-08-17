"""Tests de la jointure géographique OSM (#69) — utils/osm.py.

Fonctions pures testées en direct ; l'orchestrateur `enrichir_par_osm` est testé
avec `geocoder_ban` / `interroger_overpass` monkeypatchés — aucun appel réseau.
Vérifie les réglages mesurés : rayon, règle « nom OU < 30 m », une requête
Overpass par zone, non-écrasement des contacts existants.
"""
from __future__ import annotations

import uuid

import pytest

from utils import osm
from utils.osm import (
    POI,
    _construire_requete_overpass,
    _extraire_contacts_poi,
    _haversine_m,
    _meilleur_poi,
    _nom_similaire,
    _parser_pois,
    enrichir_par_osm,
)
from models.prospect import Prospect

CID = uuid.uuid4()
LAT, LON = 48.86, 2.35  # Paris, point de référence des tests


def _p(nom="Hotel Le Marais", adresse="1 rue de Test", code_postal="75004", **o) -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise=nom, adresse=adresse,
                    code_postal=code_postal, **o)


# --- Géométrie / nom --------------------------------------------------------
def test_haversine_environ_100m():
    d = _haversine_m(LAT, LON, LAT + 0.0009, LON)  # ~100 m en latitude
    assert 90 < d < 110


def test_nom_similaire_partage_token():
    assert _nom_similaire("HOTEL LE MARAIS SARL", "Hôtel Le Marais")
    assert not _nom_similaire("Hotel Le Marais", "Boulangerie Paul")
    # Formes juridiques seules ne suffisent pas.
    assert not _nom_similaire("SARL", "SAS")


def test_extraire_contacts_poi_precedence_et_variantes():
    tags = {"phone": "0142556677", "contact:website": "http://x.fr", "contact:email": "a@x.fr"}
    c = _extraire_contacts_poi(tags)
    assert c == {"phone": "0142556677", "website": "http://x.fr", "email": "a@x.fr"}
    # `phone` prime sur `contact:phone`.
    assert _extraire_contacts_poi({"phone": "1", "contact:phone": "2"})["phone"] == "1"


# --- Requête / parsing Overpass ---------------------------------------------
def test_construire_requete_contient_tag_et_bbox():
    q = _construire_requete_overpass(["shop=car_repair"], (48.8, 2.3, 48.9, 2.4))
    assert 'node["shop"="car_repair"]' in q
    assert 'way["shop"="car_repair"]' in q
    assert "(48.8,2.3,48.9,2.4)" in q
    assert "out center tags" in q


def test_parser_pois_node_et_way():
    data = {"elements": [
        {"type": "node", "lat": LAT, "lon": LON, "tags": {"name": "A", "phone": "0142556677"}},
        {"type": "way", "center": {"lat": LAT, "lon": LON}, "tags": {"name": "B"}},
        {"type": "node", "tags": {"name": "sans coord"}},  # ignoré (pas de lat/lon)
    ]}
    pois = _parser_pois(data)
    assert len(pois) == 2
    assert pois[0].nom == "A" and pois[0].phone == "0142556677"
    assert pois[1].nom == "B"


# --- Rapprochement (règle « nom OU < 30 m », rayon) -------------------------
def test_meilleur_poi_proche_sans_nom_accepte():
    p = _p(nom="Hotel Le Marais")
    poi = POI(lat=LAT + 0.0002, lon=LON, nom="Autre Chose")  # ~22 m
    res = _meilleur_poi(p, LAT, LON, [poi], rayon_m=150)
    assert res is not None and res[0] is poi


def test_meilleur_poi_loin_mais_nom_commun_accepte():
    p = _p(nom="Hotel Le Marais")
    poi = POI(lat=LAT + 0.0009, lon=LON, nom="Hôtel Le Marais")  # ~100 m + nom
    res = _meilleur_poi(p, LAT, LON, [poi], rayon_m=150)
    assert res is not None


def test_meilleur_poi_loin_sans_nom_rejete():
    p = _p(nom="Hotel Le Marais")
    poi = POI(lat=LAT + 0.0009, lon=LON, nom="Boulangerie Paul")  # ~100 m, nom différent
    assert _meilleur_poi(p, LAT, LON, [poi], rayon_m=150) is None


def test_meilleur_poi_hors_rayon_rejete():
    p = _p(nom="Hotel Le Marais")
    poi = POI(lat=LAT + 0.002, lon=LON, nom="Hôtel Le Marais")  # ~222 m > 150
    assert _meilleur_poi(p, LAT, LON, [poi], rayon_m=150) is None


# --- Orchestrateur (réseau mocké) -------------------------------------------
def _mock_reseau(monkeypatch, points, pois):
    """`points` : dict adresse->(lat,lon,score) ; `pois` : liste renvoyée par
    Overpass. Compte les appels Overpass dans le dict retourné."""
    compteur = {"overpass": 0}

    async def _ban(adresse, client, score_min=osm.BAN_SCORE_MIN):
        return points.get(adresse)

    async def _over(osm_tags, bbox, client):
        compteur["overpass"] += 1
        return list(pois)

    async def _no_sleep(_s):  # pas d'attente de politesse Overpass en test
        return None

    monkeypatch.setattr(osm, "geocoder_ban", _ban)
    monkeypatch.setattr(osm, "interroger_overpass", _over)
    monkeypatch.setattr(osm.asyncio, "sleep", _no_sleep)
    return compteur


@pytest.mark.asyncio
async def test_enrichir_remplit_contacts(monkeypatch):
    poi = POI(lat=LAT + 0.0002, lon=LON, nom="Hôtel Le Marais",
              phone="0142556677", website="http://hotel-x.fr", email="reservation@hotel-x.fr")
    _mock_reseau(monkeypatch, {"1 rue de Test": (LAT, LON, 0.9)}, [poi])
    p = _p()
    stats = await enrichir_par_osm([p], ["tourism=hotel"])
    assert p.telephone == "+33142556677"
    assert p.site_web == "http://hotel-x.fr"
    assert p.email == "reservation@hotel-x.fr"
    assert p.raw_data["osm"]["rapproche"] is True
    assert stats == {"geocodes": 1, "rapproches": 1, "emails": 1, "telephones": 1}


@pytest.mark.asyncio
async def test_une_requete_overpass_par_zone(monkeypatch):
    poi = POI(lat=LAT + 0.0002, lon=LON, nom="X", phone="0142556677")
    pts = {"a": (LAT, LON, 0.9), "b": (LAT, LON, 0.9), "c": (LAT, LON, 0.9)}
    compteur = _mock_reseau(monkeypatch, pts, [poi])
    # 2 prospects même code postal, 1 autre code postal -> 2 zones -> 2 requêtes.
    p1 = _p(adresse="a", code_postal="75004")
    p2 = _p(adresse="b", code_postal="75004")
    p3 = _p(adresse="c", code_postal="75011")
    await enrichir_par_osm([p1, p2, p3], ["tourism=hotel"])
    assert compteur["overpass"] == 2


@pytest.mark.asyncio
async def test_geocodage_echoue_prospect_ignore(monkeypatch):
    compteur = _mock_reseau(monkeypatch, {}, [])  # BAN ne renvoie rien
    p = _p()
    stats = await enrichir_par_osm([p], ["tourism=hotel"])
    assert stats["geocodes"] == 0
    assert compteur["overpass"] == 0  # aucune zone -> aucune requête
    assert "osm" not in (p.raw_data or {})


@pytest.mark.asyncio
async def test_tags_vides_noop(monkeypatch):
    compteur = _mock_reseau(monkeypatch, {"1 rue de Test": (LAT, LON, 0.9)}, [])
    p = _p()
    stats = await enrichir_par_osm([p], [])  # ICP sans osm_tags
    assert stats == {"geocodes": 0, "rapproches": 0, "emails": 0, "telephones": 0}
    assert compteur["overpass"] == 0


@pytest.mark.asyncio
async def test_ne_pas_ecraser_contact_existant(monkeypatch):
    poi = POI(lat=LAT + 0.0002, lon=LON, nom="X", phone="0142556677")
    _mock_reseau(monkeypatch, {"1 rue de Test": (LAT, LON, 0.9)}, [poi])
    p = _p(telephone="0600000000")  # déjà un tél
    await enrichir_par_osm([p], ["tourism=hotel"])
    assert p.telephone == "+33600000000"  # inchangé (normalisé)
