"""Tests d'intégration de l'API de lecture (#116).

@integration : le TestClient déclenche le lifespan → pool asyncpg → vraie BDD.
Exclus des runs unitaires par défaut (comme les autres tests @integration).
Assertions portables (shape, pas comptages) pour tourner sur une BDD vide ou peuplée.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # __enter__ exécute le lifespan (crée le pool)
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_campagnes_shape(client):
    r = client.get("/api/campagnes")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:  # BDD peuplée
        c = data[0]
        assert {"id", "nom", "statut", "prospects_collectes", "prospects_qualifies"} <= c.keys()


def test_prospects_pagination_shape(client):
    r = client.get("/api/prospects", params={"limit": 1})
    assert r.status_code == 200
    page = r.json()
    assert {"total", "limit", "offset", "items"} <= page.keys()
    assert page["limit"] == 1
    assert isinstance(page["items"], list)


def test_campagne_introuvable_404(client):
    r = client.get("/api/campagnes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_statut_invalide_422(client):
    r = client.get("/api/prospects", params={"statut": "pas_un_statut"})
    assert r.status_code == 422


def test_kpis_shape(client):
    r = client.get("/api/kpis", params={"since_days": 3})
    assert r.status_code == 200
    k = r.json()
    assert {"collectes", "qualifies", "taux_tel", "taux_email", "pct_qualifies"} <= k.keys()
