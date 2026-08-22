"""Tests unitaires du mapping Airtable (#36) — pur, sans réseau ni BDD."""
from scripts.sync_airtable import _build_records, _to_airtable_fields


def test_mapping_champs():
    row = {
        "nom_entreprise": "ACME", "siret": "12345678900011", "ville": "PARIS",
        "departement": "75", "code_naf": "55.10Z", "score_final": 85,
        "statut": "qualifie", "telephone": "+33123456789", "email": "x@acme.fr",
        "site_web": "https://acme.fr", "nom_dirigeant": "Jean Test", "campagne": "Camp A",
    }
    f = _to_airtable_fields(row)
    assert f["Entreprise"] == "ACME"
    assert f["SIRET"] == "12345678900011"
    assert f["Département"] == "75"
    assert f["Code NAF"] == "55.10Z"
    assert f["Score"] == 85
    assert f["Email"] == "x@acme.fr"
    assert f["Site web"] == "https://acme.fr"
    assert f["Dirigeant"] == "Jean Test"
    assert f["Campagne"] == "Camp A"


def test_mapping_ignore_none_et_vide():
    row = {"nom_entreprise": "", "siret": "999", "email": None,
           "site_web": "", "telephone": None, "campagne": None}
    f = _to_airtable_fields(row)
    assert f == {"SIRET": "999"}  # tout le reste None / vide -> ignoré


def test_dedup_par_siret():
    # Lignes triées par score décroissant (comme la requête SQL).
    rows = [
        {"nom_entreprise": "A", "siret": "111", "score_final": 90},
        {"nom_entreprise": "A bis", "siret": "111", "score_final": 80},  # doublon SIRET
        {"nom_entreprise": "B", "siret": "222", "score_final": 70},
        {"nom_entreprise": "C", "siret": None, "score_final": 60},        # sans SIRET
    ]
    records, doublons, sans_siret = _build_records(rows)
    assert len(records) == 2                              # 111 (1re occ) + 222
    assert doublons == 1
    assert sans_siret == 1
    assert records[0]["fields"]["Entreprise"] == "A"     # garde la meilleure (1re) occ
