"""Tests unitaires de « Affiner avec l'IA » (utils/icp_parse.py + POST /api/icp/parse).

Aucun appel réseau : `icp_parse.make_client` est remplacé par un faux client Claude.
Le TestClient est utilisé SANS `with` (pas de lifespan → pas de BDD).
"""
import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from config.settings import Settings
from utils import icp_parse

PHRASE = "Hôtels indépendants de 10 à 50 salariés à Paris"


class FakeMessages:
    def __init__(self, reponse=None, erreur=None):
        self.reponse = reponse
        self.erreur = erreur
        self.appels: list[dict] = []

    async def create(self, **kwargs):
        self.appels.append(kwargs)
        if self.erreur:
            raise self.erreur
        return self.reponse


class FakeClient:
    def __init__(self, messages: FakeMessages):
        self.messages = messages

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def reponse(data, stop_reason="end_turn"):
    texte = data if isinstance(data, str) else json.dumps(data)
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=texte)],
        usage=SimpleNamespace(input_tokens=1200, output_tokens=90),
    )


def sortie(**over):
    base = {
        "codes_naf": [], "departements": [], "effectif_min": None, "effectif_max": None,
        "anciennete_min_ans": None, "exiger_site_web": False, "exiger_email": False,
        "mots_cles_positifs": [], "mots_cles_negatifs": [], "non_traduits": [], "hypotheses": [],
    }
    base.update(over)
    return base


@pytest.fixture
def settings_actifs(monkeypatch):
    s = Settings(_env_file=None, icp_parse_llm_enabled=True, anthropic_api_key="sk-test")
    monkeypatch.setattr(api_main, "get_settings", lambda: s)
    monkeypatch.setattr(icp_parse, "get_settings", lambda: s)
    return s


@pytest.fixture
def faux_claude(monkeypatch):
    icp_parse._cache.clear()
    messages = FakeMessages(reponse(sortie()))
    monkeypatch.setattr(icp_parse, "make_client", lambda: FakeClient(messages))
    return messages


# --- schéma & validation ------------------------------------------------------
def test_schema_restreint_aux_codes_du_lexique():
    s = icp_parse.schema()
    lex = icp_parse.lexique()
    naf = s["properties"]["codes_naf"]["items"]["enum"]
    assert set(naf) == {n["code"] for sec in lex["secteurs"] for n in sec["naf"]}
    assert s["properties"]["departements"]["items"]["enum"] == [d["code"] for d in lex["departements"]]
    assert s["additionalProperties"] is False
    assert set(s["required"]) == set(s["properties"])


def test_valider_ecarte_codes_inconnus_et_incoherences():
    naf_ok = icp_parse.codes_naf_autorises()[0]
    out = icp_parse.valider(
        sortie(
            codes_naf=[naf_ok, naf_ok, "0000Z"],
            departements=["75", "20", "75"],
            effectif_min=50, effectif_max=10,
            anciennete_min_ans=-3,
            mots_cles_negatifs=["  Chaîne ", "chaîne", 7],
            non_traduits=["INDÉPENDANTS", "inventé"],
            exiger_email="oui",
        ),
        ["indépendants"],
    )
    assert out["codes_naf"] == [naf_ok]
    assert out["departements"] == ["75"]
    assert out["effectif_min"] is None and out["effectif_max"] is None
    assert out["anciennete_min_ans"] is None
    assert out["mots_cles_negatifs"] == ["chaîne"]
    assert out["non_traduits"] == ["indépendants"]
    assert out["exiger_email"] is False


def test_nettoyer_mots_et_cle_de_cache():
    assert icp_parse.nettoyer_mots([" indépendants ", "Indépendants", "", "x" * 80]) == ["indépendants", "x" * 60]
    assert icp_parse.cle_cache("Hôtels  à PARIS", ["Indépendants"]) == icp_parse.cle_cache(
        "hotels a paris", ["independants"]
    )


# --- appel Claude ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_affiner_appelle_claude_en_sortie_structuree_puis_cache(settings_actifs, faux_claude):
    faux_claude.reponse = reponse(sortie(mots_cles_negatifs=["chaîne"], hypotheses=["indépendants : exclusion"]))
    res, depuis_cache = await icp_parse.affiner(PHRASE, ["indépendants"])
    assert depuis_cache is False
    assert res["mots_cles_negatifs"] == ["chaîne"]

    appel = faux_claude.appels[0]
    assert appel["model"] == settings_actifs.claude_icp_parse_model
    assert appel["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in appel and "thinking" not in appel
    libelle = icp_parse.lexique()["secteurs"][0]["naf"][0]["libelle"]
    assert libelle in appel["system"][0]["text"]          # lexique injecté dans le prompt
    assert "indépendants" in appel["messages"][0]["content"]

    res2, depuis_cache2 = await icp_parse.affiner(PHRASE.upper(), ["Indépendants"])
    assert depuis_cache2 is True and res2 == res
    assert len(faux_claude.appels) == 1                   # aucun second appel payant


@pytest.mark.asyncio
@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
async def test_affiner_refus_ou_troncature(settings_actifs, faux_claude, stop_reason):
    faux_claude.reponse = reponse(sortie(), stop_reason=stop_reason)
    with pytest.raises(icp_parse.IcpParseError, match=stop_reason):
        await icp_parse.affiner(PHRASE, ["indépendants"])
    assert not icp_parse._cache                            # rien de mis en cache


@pytest.mark.asyncio
async def test_affiner_json_invalide(settings_actifs, faux_claude):
    faux_claude.reponse = reponse("{pas du json")
    with pytest.raises(icp_parse.IcpParseError, match="JSON"):
        await icp_parse.affiner(PHRASE, ["indépendants"])


# --- endpoints ------------------------------------------------------------------
def test_status_desactive_par_defaut(monkeypatch):
    s = Settings(_env_file=None, anthropic_api_key="sk-test")
    monkeypatch.setattr(api_main, "get_settings", lambda: s)
    r = TestClient(api_main.app).get("/api/icp/parse/status")
    assert r.json() == {"enabled": False, "modele": s.claude_icp_parse_model}
    r = TestClient(api_main.app).post("/api/icp/parse", json={"phrase": PHRASE, "non_traduits": ["x"]})
    assert r.status_code == 503


def test_endpoint_renvoie_les_criteres(settings_actifs, faux_claude):
    faux_claude.reponse = reponse(sortie(mots_cles_negatifs=["chaîne"], non_traduits=["fintech"]))
    client = TestClient(api_main.app)
    assert client.get("/api/icp/parse/status").json()["enabled"] is True
    r = client.post("/api/icp/parse", json={"phrase": PHRASE, "non_traduits": ["indépendants", "fintech"]})
    assert r.status_code == 200
    body = r.json()
    assert body["mots_cles_negatifs"] == ["chaîne"]
    assert body["non_traduits"] == ["fintech"]
    assert body["modele"] == settings_actifs.claude_icp_parse_model
    assert body["depuis_cache"] is False


def test_endpoint_erreurs(settings_actifs, faux_claude):
    client = TestClient(api_main.app)
    faux_claude.erreur = anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
    assert client.post("/api/icp/parse", json={"phrase": PHRASE, "non_traduits": ["a"]}).status_code == 503
    faux_claude.erreur = None
    faux_claude.reponse = reponse(sortie(), stop_reason="refusal")
    assert client.post("/api/icp/parse", json={"phrase": PHRASE, "non_traduits": ["b"]}).status_code == 502


@pytest.mark.parametrize(
    "payload",
    [
        {"phrase": "", "non_traduits": ["x"]},
        {"phrase": PHRASE, "non_traduits": []},
        {"phrase": PHRASE, "non_traduits": ["x"] * 21},
        {"phrase": PHRASE, "non_traduits": ["x" * 61]},
    ],
)
def test_endpoint_valide_l_entree(settings_actifs, faux_claude, payload):
    assert TestClient(api_main.app).post("/api/icp/parse", json=payload).status_code == 422
    assert faux_claude.appels == []
