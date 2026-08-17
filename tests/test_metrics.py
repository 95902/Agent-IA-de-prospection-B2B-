"""Tests des métriques par source (#23) — utils/metrics.py. Pur, sans I/O."""
from __future__ import annotations

import uuid

from utils.metrics import (
    MetriquesSource,
    couverture_globale,
    depuis_dropcontact,
    depuis_osm,
    rapport,
)
from models.prospect import Prospect

CID = uuid.uuid4()


def _p(email=None, telephone=None, site_web=None, doublon=False, oppose=None, **o) -> Prospect:
    p = Prospect(campagne_id=CID, nom_entreprise="ACME", email=email,
                 telephone=telephone, site_web=site_web, doublon=doublon, **o)
    if oppose is not None:
        p.raw_data = {"opposition_commerciale": {"oppose": oppose}}
    return p


def test_taux_source():
    assert MetriquesSource("x", True, tentes=4, reussis=1).taux == 0.25
    assert MetriquesSource("x", True, tentes=0, reussis=0).taux == 0.0


def test_couverture_globale_pourcentages():
    ps = [
        _p(email="a@b.fr", telephone="0612345678", oppose=False),
        _p(telephone="0612345678"),
        _p(doublon=True),
        _p(),
    ]
    cov = couverture_globale(ps)
    assert cov["n"] == 4
    assert cov["email"] == 1 and cov["email_pct"] == 25.0
    assert cov["telephone"] == 2 and cov["telephone_pct"] == 50.0
    assert cov["doublons"] == 1
    assert cov["contactables"] == 1  # seul le 1er a un verdict non-opposé vérifié


def test_depuis_osm_gratuit():
    m = depuis_osm({"geocodes": 30, "rapproches": 22, "emails": 12, "telephones": 13})
    assert m.source == "osm" and m.gratuite is True
    assert m.tentes == 30 and m.reussis == 22 and m.cout_credits == 0


def test_depuis_dropcontact_cout_pay_on_success():
    m = depuis_dropcontact({"eligibles": 10, "soumis": 8, "emails": 2})
    assert m.source == "dropcontact" and m.gratuite is False
    assert m.tentes == 8 and m.reussis == 2
    assert m.cout_credits == 2  # pay on success : 1 crédit par email trouvé


def test_rapport_contient_cibles_et_sources():
    cov = couverture_globale([_p(email="a@b.fr")])
    txt = rapport(cov, [depuis_osm({"geocodes": 1, "rapproches": 1}),
                        depuis_dropcontact({"soumis": 1, "emails": 0})])
    assert "cible PRD" in txt
    assert "osm" in txt and "dropcontact" in txt
    assert "gratuit" in txt
