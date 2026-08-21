"""Tests d'intégration des endpoints d'écriture (#116 A).

Chemins SÛRS uniquement (validation + 404) : ne mutent aucune donnée réelle.
Les chemins de succès (outcome/note/create) sont vérifiés en live avec cleanup.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.integration

_MISSING = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_outcome_statut_invalide_422(client):
    r = client.post(f"/api/prospects/{_MISSING}/outcome", json={"statut": "nope"})
    assert r.status_code == 422  # rejeté avant tout UPDATE


def test_outcome_prospect_introuvable_404(client):
    r = client.post(f"/api/prospects/{_MISSING}/outcome", json={"statut": "rdv"})
    assert r.status_code == 404  # statut valide mais aucune ligne


def test_note_prospect_introuvable_404(client):
    r = client.post(f"/api/prospects/{_MISSING}/note", json={"note": "x"})
    assert r.status_code == 404


def test_create_campagne_payload_invalide_422(client):
    # Payload vide : le normaliseur ICP doit rejeter (nom_entreprise/nom requis).
    r = client.post("/api/campagnes", json={})
    assert r.status_code == 422
