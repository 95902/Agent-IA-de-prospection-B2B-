"""Tests unitaires (sans BDD) des compteurs « actionnables » de l'API de lecture.

Un pool factice remplace `utils.db.get_pg_pool` ; le TestClient est utilisé SANS
`with` pour ne pas déclencher le lifespan (qui ouvrirait un vrai pool asyncpg).
Les invariants sur une vraie BDD sont dans tests/test_api.py (@integration).
"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import api.main as api_main


class FakePool:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.calls: list[tuple[str, tuple]] = []

    async def fetchrow(self, sql, *args):
        self.calls.append((sql, args))
        return self.row

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
        return self.rows


@pytest.fixture
def fake(monkeypatch):
    pool = FakePool()

    async def get_pool():
        return pool

    monkeypatch.setattr(api_main.db, "get_pg_pool", get_pool)
    return pool, TestClient(api_main.app)


def _kpi_row(**over):
    row = {
        "collectes": 1200, "qualifies": 152, "avec_tel": 175, "avec_email": 171,
        "smq": 70.44, "qualifies_score": 158, "joignables": 248, "actionnables": 122,
    }
    row.update(over)
    return row


def test_kpis_expose_actionnables_et_garde_les_champs_existants(fake):
    pool, client = fake
    pool.row = _kpi_row()
    k = client.get("/api/kpis", params={"since_days": 36500}).json()
    # nouveaux champs
    assert k["qualifies_score"] == 158
    assert k["joignables"] == 248
    assert k["actionnables"] == 122
    assert k["pct_actionnables"] == 10.2
    # champs historiques inchangés
    assert k["qualifies"] == 152
    assert k["taux_tel"] == 14.6
    assert k["taux_email"] == 14.2
    assert k["pct_qualifies"] == 12.7
    assert k["score_moy_qualifies"] == 70.4


def test_kpis_sql_seuil_et_joignabilite(fake):
    pool, client = fake
    pool.row = _kpi_row()
    client.get("/api/kpis")
    sql = pool.calls[-1][0]
    assert "score_final >= 60" in sql
    assert "btrim(email)" in sql and "btrim(telephone)" in sql
    assert "AS actionnables" in sql


def test_kpis_bdd_vide(fake):
    pool, client = fake
    pool.row = _kpi_row(collectes=0, qualifies=0, avec_tel=0, avec_email=0, smq=None,
                        qualifies_score=None, joignables=None, actionnables=None)
    k = client.get("/api/kpis").json()
    assert k["collectes"] == 0
    assert k["actionnables"] == 0
    assert k["pct_actionnables"] == 0.0
    assert k["score_moy_qualifies"] is None


def test_campagnes_collectes_et_actionnables_calcules(fake):
    pool, client = fake
    cid = uuid4()
    pool.rows = [{
        "id": cid, "nom": "Pilote", "statut": "brouillon",
        "prospects_collectes": 500, "prospects_qualifies": 72, "actionnables": 55,
    }]
    data = client.get("/api/campagnes").json()
    assert data == [{
        "id": str(cid), "nom": "Pilote", "statut": "brouillon",
        "prospects_collectes": 500, "prospects_qualifies": 72, "actionnables": 55,
    }]
    sql = pool.calls[-1][0]
    assert "LEFT JOIN LATERAL" in sql and "FROM prospects WHERE campagne_id = c.id" in sql
    assert sql.rstrip().endswith("ORDER BY c.nom")


def test_campagne_detail_et_404(fake):
    pool, client = fake
    cid = uuid4()
    pool.row = {
        "id": cid, "nom": "Test", "statut": "brouillon",
        "prospects_collectes": 150, "prospects_qualifies": 37, "actionnables": 29,
    }
    assert client.get(f"/api/campagnes/{cid}").json()["actionnables"] == 29
    sql, args = pool.calls[-1]
    assert "WHERE c.id = $1" in sql and args == (cid,)

    pool.row = None
    assert client.get(f"/api/campagnes/{uuid4()}").status_code == 404


def test_seuil_aligne_sur_le_scoring():
    from agents.scoring_agent import _SEUIL_QUALIFIE

    assert api_main._SEUIL_QUALIFIE == _SEUIL_QUALIFIE
