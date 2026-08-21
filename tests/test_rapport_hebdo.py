"""Tests unitaires du rapport hebdo (#38) — fonctions pures, sans BDD.

La collecte SQL (`collecter`) est couverte en intégration ; ici on verrouille le
calcul des KPIs dérivés, les gardes (division par zéro, valeurs manquantes) et le
rendu texte/HTML.
"""
from scripts import rapport_hebdo as rh


def _sample(**kw) -> rh.Rapport:
    base = dict(
        portee="7 derniers jours", collectes=150, qualifies=30, avec_tel=60,
        avec_email=30, score_moy_qualifies=70.0, appels=0, rdv=0,
        cout_estime_eur=0.30, campagnes=[], top_file=[],
    )
    base.update(kw)
    return rh.Rapport(**base)


def test_pct_garde_division_zero():
    assert rh._pct(5, 0) == 0.0
    assert rh._pct(3, 8) == 37.5


def test_flag_min_max_none():
    assert rh._flag(50, 40) == "  ✅"
    assert rh._flag(30, 40) == "  ⚠️"
    assert rh._flag(0.10, 0.15, sens="max") == "  ✅"
    assert rh._flag(0.20, 0.15, sens="max") == "  ⚠️"
    assert rh._flag(None, 40) == "  n/a"


def test_kpis_derives():
    r = _sample()
    assert r.taux_tel == 40.0
    assert r.taux_email == 20.0
    assert r.pct_qualifies == 20.0
    assert r.cout_par_qualifie == round(0.30 / 30, 4)
    assert r.taux_rdv is None  # aucun appel journalisé


def test_taux_rdv_calcule():
    r = _sample(appels=50, rdv=1)
    assert r.taux_rdv == 2.0


def test_gardes_zero():
    r = _sample(qualifies=0, collectes=0)
    assert r.cout_par_qualifie is None
    assert r.pct_qualifies == 0.0
    assert r.taux_tel == 0.0


def test_rendre_texte_contient_kpis():
    out = rh.rendre_texte(_sample())
    assert "RAPPORT DE PROSPECTION" in out
    assert "Taux téléphone" in out
    assert "150" in out


def test_rendre_html_valide():
    r = _sample(top_file=[rh.Prospect(
        nom_entreprise="ACME COM", code_naf="73.11Z", score_final=80,
        telephone="0102030405", email=None,
    )])
    html = rh.rendre_html(r)
    assert html.strip().startswith("<div")
    assert "ACME COM" in html
    assert "qualifiés" in html
