"""Tests des couches de scoring — purs / mockés, déterministes, hors ligne.

Couche règles (#24) : sous-scorers (`_score_effectif`, `_score_anciennete`,
`_score_mots_cles_positifs`) + barème intégré `_score_regles` (contact, effectif,
ancienneté, présence, géo, mots-clés, pénalités, exclusion #4, plafond 0-100).
Couche embeddings (#26) : `_cosinus` (Python pur) + `_score_embedding` (Ollama et
Qdrant mockés — aucun réseau ; cosinus borné 0-1, ICP absent → 0.0, upsert
conditionnel au `prospect_id`).
Couche LLM (#25) : rendu des prompts Jinja depuis l'ICP (`rendre_system`/`rendre_user`)
+ `_score_llm` (client Anthropic FAUX — aucun réseau) : sortie structurée, requête
agnostique du modèle (ni effort/temperature/thinking), bornage 0-100, repli sur le
score règles. Valeurs métier depuis `CriteresCiblage` (règle #3).
"""
from __future__ import annotations

import asyncio
import inspect
import json
import math
import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from agents import scoring_agent as sa   # pour monkeypatcher get_embedding / upsert
from agents.scoring_agent import (
    _cosinus,
    _score_anciennete,
    _score_effectif,
    _score_embedding,
    _score_llm,
    _score_mots_cles_positifs,
    _score_regles,
    rendre_system,
    rendre_user,
)
from config.settings import get_settings
from models.criteres import CriteresCiblage
from models.prospect import Prospect

CID = uuid.uuid4()

# Valeurs qui PASSENT les validators du Prospect (sinon mises à None à la construction).
TEL_OK = "0123456789"                      # ligne fixe FR -> +33123456789
EMAIL_OK = "contact@garage-durand.fr"      # générique commerciale -> conservée (#65)


def _p(nom="Garage Durand", **o) -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise=nom, **o)


def _criteres(**o) -> CriteresCiblage:
    base = dict(nom="ICP test")
    base.update(o)
    return CriteresCiblage(**base)


def _il_y_a(annees: float) -> date:
    """Date de création située `annees` en arrière (via 365.25 j/an, comme le barème)."""
    return date.today() - timedelta(days=round(annees * 365.25))


# --- _score_effectif (max 20) -----------------------------------------------
@pytest.mark.parametrize(
    "effectif, attendu",
    [
        (8, 20),     # dans la fourchette
        (2, 20),     # borne basse
        (15, 20),    # borne haute
        (16, 10),    # ecart 1 <= 3
        (18, 10),    # ecart 3 <= 3
        (19, 5),     # ecart 4 > 3
        (0, 10),     # ecart min(|0-2|,|0-15|)=2 <= 3
        (100, 5),    # loin au-dessus de la fourchette
    ],
)
def test_score_effectif(effectif, attendu):
    assert _score_effectif(effectif, 2, 15) == attendu


def test_score_effectif_inconnu_ne_devine_pas():
    assert _score_effectif(None, 2, 15) == 0


# --- _score_anciennete (max 15), seuil ICP = 3 ans --------------------------
@pytest.mark.parametrize(
    "annees_ago, attendu",
    [
        (11, 15),    # >= min+7 (10)
        (6, 10),     # >= min+2 (5), < 10
        (3.5, 5),    # >= min (3), < 5
        (2, 0),      # < min
    ],
)
def test_score_anciennete(annees_ago, attendu):
    assert _score_anciennete(_il_y_a(annees_ago), anciennete_min_ans=3) == attendu


# --- _score_mots_cles_positifs (max 10) -------------------------------------
def test_mots_cles_none_ou_vide():
    p = _p(libelle_naf="Carrosserie")
    assert _score_mots_cles_positifs(p, None) == 0
    assert _score_mots_cles_positifs(p, []) == 0


def test_mots_cles_un_hit():
    p = _p(libelle_naf="Entretien et réparation, carrosserie")
    assert _score_mots_cles_positifs(p, ["carrosserie"]) == 5


def test_mots_cles_deux_hits():
    p = _p(libelle_naf="Carrosserie et peinture automobile")
    assert _score_mots_cles_positifs(p, ["carrosserie", "peinture"]) == 10


def test_mots_cles_plafonne_a_10():
    p = _p(nom="Carrosserie Peinture Mécanique Durand", libelle_naf="carrosserie peinture")
    assert _score_mots_cles_positifs(p, ["carrosserie", "peinture", "mécanique"]) == 10


def test_mots_cles_insensible_casse():
    p = _p(libelle_naf="CARROSSERIE")
    assert _score_mots_cles_positifs(p, ["carrosserie"]) == 5


def test_mots_cles_cherche_dans_notes():
    p = _p(libelle_naf="Réparation", notes="Signalé comme spécialiste peinture")
    assert _score_mots_cles_positifs(p, ["peinture"]) == 5


# --- _score_regles : barème intégré -----------------------------------------
def test_regles_prospect_ideal():
    """Contact + effectif + ancienneté + site + avis + géo + mot-clé = 95, sans pénalité."""
    crit = _criteres(
        codes_naf=["4520Z"], departements=["75"], effectif_min=2, effectif_max=15,
        anciennete_min_ans=3, mots_cles_positifs=["carrosserie"],
    )
    p = _p(
        code_naf="4520Z", departement="75", effectif_estime=8,
        telephone=TEL_OK, email=EMAIL_OK, site_web="https://garage-durand.fr",
        date_creation=_il_y_a(20), libelle_naf="Réparation, carrosserie",
        notes="Bien noté sur avis google",
    )
    # 25 + 10 + 20 + 15 + 8 + 2 + 10 + 5 = 95
    assert _score_regles(p, crit) == 95


def test_regles_exclusion_force_a_zero():
    """Une exclusion ICP (mot entier) prime sur un prospect par ailleurs excellent."""
    crit = _criteres(
        departements=["75"], effectif_min=2, effectif_max=15,
        mots_cles_negatifs=["durand"],
    )
    p = _p(
        nom="Garage Durand", departement="75", effectif_estime=8,
        telephone=TEL_OK, email=EMAIL_OK, site_web="https://x.fr",
    )
    assert _score_regles(p, crit) == 0


def test_regles_exclusion_mot_entier_pas_sous_chaine():
    """« durand » n'exclut pas « Durandal » (mot entier, réutilise nettoyage #19)."""
    crit = _criteres(effectif_min=2, effectif_max=15, mots_cles_negatifs=["durand"])
    p = _p(nom="Garage Durandal", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(p, crit) == 45  # 25 (tel) + 20 (effectif), pas d'exclusion


def test_regles_penalite_sans_contact():
    """Sans téléphone NI email : -20. Le contact vaut 35 + évite la pénalité."""
    crit = _criteres(effectif_min=2, effectif_max=15, departements=["75"])
    avec = _p(departement="75", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    sans = _p(departement="75", effectif_estime=8)
    assert _score_regles(avec, crit) == 65   # 35 + 20 + 10
    assert _score_regles(sans, crit) == 10   # 20 + 10 - 20


def test_regles_credit_email_isole():
    """Téléphone présent dans les deux : l'email seul vaut +10 (pas de pénalité contact)."""
    crit = _criteres(effectif_min=2, effectif_max=15)
    avec = _p(effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    sans = _p(effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(avec, crit) == 55   # 25 + 10 + 20
    assert _score_regles(sans, crit) == 45   # 25 + 20


def test_regles_penalite_naf_hors_icp():
    """NAF hors des codes ICP : -30. NAF dans l'ICP : pas de pénalité."""
    crit = _criteres(codes_naf=["1234Z"], effectif_min=2, effectif_max=15)
    dedans = _p(code_naf="1234Z", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    dehors = _p(code_naf="9999Z", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    assert _score_regles(dedans, crit) == 55   # 35 + 20
    assert _score_regles(dehors, crit) == 25   # 35 + 20 - 30


def test_regles_codes_naf_vides_pas_de_penalite():
    """ICP sans codes_naf : aucune pénalité NAF, quel que soit le code du prospect."""
    crit = _criteres(codes_naf=[], effectif_min=2, effectif_max=15)
    p = _p(code_naf="9999Z", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(p, crit) == 45   # 25 + 20, pas de -30


def test_regles_plancher_a_zero():
    """Cumul de pénalités : jamais en dessous de 0 (clamp)."""
    crit = _criteres(codes_naf=["1234Z"], effectif_min=2, effectif_max=15)
    p = _p(code_naf="9999Z")  # ni contact, ni effectif connu, NAF hors ICP
    assert _score_regles(p, crit) == 0   # max(0, 0 - 20 - 30)


def test_regles_bonus_geo_uniquement_si_departement_prioritaire():
    """Le bonus géo (+10) ne s'applique que dans les départements de l'ICP."""
    crit = _criteres(effectif_min=2, effectif_max=15, departements=["75", "92"])
    dedans = _p(departement="92", effectif_estime=8, telephone=TEL_OK)
    dehors = _p(departement="13", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(dedans, crit) == 55   # 25 + 20 + 10
    assert _score_regles(dehors, crit) == 45   # 25 + 20


def test_regles_effectif_estime_pas_le_libelle():
    """Le barème lit effectif_estime (int), pas le libellé texte effectif."""
    crit = _criteres(effectif_min=2, effectif_max=15)
    # Libellé renseigné mais effectif_estime absent -> 0 pt d'effectif (on ne devine pas).
    p = _p(effectif="20 à 49 salariés", effectif_estime=None, telephone=TEL_OK)
    assert _score_regles(p, crit) == 25   # 25 (tel) + 0 (effectif inconnu)


# --- Node d'assemblage (#28) — reste un stub tant que le graphe n'est pas câblé ----
# Conservés depuis #11 : la couche règles est prête (#24) mais `scoring_node` (câblage
# des 3 couches + agrégation) n'est assemblé qu'en #28.
def test_scoring_node_is_async_coroutine() -> None:
    """`scoring_node` est bien une coroutine async (règle #8)."""
    from agents.scoring_agent import scoring_node

    assert inspect.iscoroutinefunction(scoring_node)


def test_scoring_node_stub_raises_not_implemented() -> None:
    """Le node lève NotImplementedError tant que #28 ne l'a pas assemblé."""
    from agents.scoring_agent import scoring_node

    with pytest.raises(NotImplementedError):
        asyncio.run(scoring_node({"prospects": []}))


# --- Couche 3 : cosinus pur (#26) -------------------------------------------
def test_cosinus_vecteurs_identiques():
    assert _cosinus([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosinus_orthogonaux():
    assert _cosinus([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosinus_opposes():
    assert _cosinus([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosinus_vecteur_nul_pas_de_division_par_zero():
    assert _cosinus([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0


def test_cosinus_valeur_connue():
    # angle 45° entre [1,1] et [1,0] -> cos = 1/sqrt(2)
    assert _cosinus([1.0, 1.0], [1.0, 0.0]) == pytest.approx(1 / math.sqrt(2))


# --- Couche 3 : _score_embedding (Ollama + Qdrant mockés) -------------------
def test_score_embedding_icp_absent_court_circuite(monkeypatch):
    """ICP non initialisé (None ou vide) → 0.0 sans appeler Ollama."""
    appels = []

    async def _fake_get(text):
        appels.append(text)
        return [1.0] * 4

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    assert asyncio.run(_score_embedding(_p(), None)) == 0.0
    assert asyncio.run(_score_embedding(_p(), [])) == 0.0
    assert appels == []   # aucun appel embedding (court-circuit)


def test_score_embedding_retourne_cosinus_borne(monkeypatch):
    """Cosinus 0-1 renvoyé (ici 1/sqrt(2) entre [1,1] et [1,0])."""
    async def _fake_get(text):
        return [1.0, 1.0]

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    assert asyncio.run(_score_embedding(_p(), [1.0, 0.0])) == pytest.approx(1 / math.sqrt(2))


def test_score_embedding_cosinus_negatif_clampe_a_zero(monkeypatch):
    """Un cosinus négatif est ramené à 0.0 (échelle [0, 1])."""
    async def _fake_get(text):
        return [-1.0, 0.0]

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    assert asyncio.run(_score_embedding(_p(), [1.0, 0.0])) == 0.0


def test_score_embedding_upsert_avec_id_et_payload(monkeypatch):
    """Avec un prospect_id : persistance Qdrant appelée avec le vecteur + payload indexable."""
    recu = {}

    async def _fake_get(text):
        return [0.5, 0.5, 0.5, 0.5]

    async def _fake_upsert(prospect_id, embedding, payload):
        recu.update(id=prospect_id, embedding=embedding, payload=payload)

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    monkeypatch.setattr(sa, "upsert_prospect_embedding", _fake_upsert)

    p = _p(nom="Garage Martin", code_naf="4520Z", departement="75")
    asyncio.run(_score_embedding(p, [0.5, 0.5, 0.5, 0.5], prospect_id="uuid-bdd-123"))

    assert recu["id"] == "uuid-bdd-123"
    assert recu["embedding"] == [0.5, 0.5, 0.5, 0.5]
    assert recu["payload"] == {
        "campagne_id": str(CID),
        "code_naf": "4520Z",
        "departement": "75",
        "nom_entreprise": "Garage Martin",
    }


def test_score_embedding_pas_d_upsert_sans_id(monkeypatch):
    """Sans prospect_id : on calcule le cosinus mais on n'écrit rien dans Qdrant."""
    a_ecrit = []

    async def _fake_get(text):
        return [1.0, 0.0]

    async def _fake_upsert(prospect_id, embedding, payload):
        a_ecrit.append(prospect_id)

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    monkeypatch.setattr(sa, "upsert_prospect_embedding", _fake_upsert)

    asyncio.run(_score_embedding(_p(), [1.0, 0.0]))   # prospect_id=None
    assert a_ecrit == []


def test_score_embedding_texte_reprend_les_champs(monkeypatch):
    """Le texte encodé reprend les champs discriminants du prospect."""
    vu = {}

    async def _fake_get(text):
        vu["text"] = text
        return [1.0, 0.0]

    monkeypatch.setattr(sa, "get_embedding", _fake_get)
    p = _p(nom="Garage Martin", libelle_naf="Réparation auto",
           effectif_estime=8, ville="Paris", departement="75")
    asyncio.run(_score_embedding(p, [1.0, 0.0]))

    for attendu in ("Garage Martin", "Réparation auto", "Paris", "75", "8"):
        assert attendu in vu["text"]


# --- Couche 2 : rendu des prompts Jinja depuis l'ICP (#25) ------------------
def test_rendre_system_reprend_l_icp():
    crit = _criteres(
        description_icp="Garages automobiles indépendants",
        codes_naf=["4520Z"], effectif_min=2, effectif_max=15,
        mots_cles_positifs=["carrosserie"], mots_cles_negatifs=["norauto"],
    )
    s = rendre_system(crit, client_nom="AssurPro")
    for attendu in ("AssurPro", "Garages automobiles indépendants", "4520Z",
                    "carrosserie", "norauto"):
        assert attendu in s
    assert "JSON" in s   # contrat de sortie présent


def test_rendre_system_defaut_sans_client_ni_valeurs():
    s = rendre_system(_criteres(), client_nom=None)
    assert "None" not in s              # default(..., true) évite le rendu littéral de None
    assert "(non renseigné)" in s


def test_rendre_user_reprend_le_prospect():
    p = _p(nom="Garage Martin", code_naf="4520Z", libelle_naf="Réparation auto",
           effectif_estime=8, ville="Paris", departement="75", site_web="https://x.fr")
    u = rendre_user(p, mots_cles_detectes=["diagnostic"])
    for attendu in ("Garage Martin", "4520Z", "Réparation auto", "8", "Paris",
                    "75", "diagnostic"):
        assert attendu in u


def test_rendre_user_champs_absents_pas_de_None():
    u = rendre_user(_p())               # la plupart des champs à None
    assert "None" not in u


# --- Couche 2 : _score_llm (client Anthropic FAUX — aucun réseau) -----------
class _FakeMessages:
    def __init__(self, resp=None, exc=None):
        self._resp, self._exc = resp, exc
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return self._resp


class _FakeClient:
    """Imite anthropic.AsyncAnthropic pour _score_llm — pas de réseau, pas de clé."""
    def __init__(self, resp=None, exc=None):
        self.messages = _FakeMessages(resp, exc)


def _resp_json(payload: dict) -> SimpleNamespace:
    bloc = SimpleNamespace(type="text", text=json.dumps(payload))
    return SimpleNamespace(content=[bloc])


_PAYLOAD_OK = {
    "score": 72,
    "justification": "Bonne adéquation avec l'ICP : activité et taille cohérentes.",
    "signaux_positifs": ["carrosserie", "avis google"],
    "signaux_negatifs": [],
    "priorite": "haute",
}


def test_score_llm_parse_sortie_structuree():
    client = _FakeClient(resp=_resp_json(_PAYLOAD_OK))
    r = asyncio.run(_score_llm(client, "sys", "usr", score_regles_fallback=50))
    assert r["score"] == 72
    assert r["priorite"] == "haute"
    assert r["signaux_positifs"] == ["carrosserie", "avis google"]
    assert "adéquation" in r["justification"]


def test_score_llm_requete_agnostique_du_modele():
    """La requête utilise le modèle configuré + sortie structurée + cache, et n'inclut
    NI temperature/top_p NI effort/thinking (contrat multi-modèle Haiku↔Sonnet)."""
    client = _FakeClient(resp=_resp_json(_PAYLOAD_OK))
    asyncio.run(_score_llm(client, "SYS", "USR", score_regles_fallback=50))
    kw = client.messages.calls[0]
    assert kw["model"] == get_settings().claude_scoring_model
    assert kw["output_config"]["format"]["type"] == "json_schema"
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kw["system"][0]["text"] == "SYS"
    assert "temperature" not in kw
    assert "top_p" not in kw
    assert "thinking" not in kw
    assert "effort" not in kw.get("output_config", {})


def test_score_llm_borne_le_score():
    haut = _FakeClient(resp=_resp_json({**_PAYLOAD_OK, "score": 150}))
    bas = _FakeClient(resp=_resp_json({**_PAYLOAD_OK, "score": -10}))
    assert asyncio.run(_score_llm(haut, "s", "u", 50))["score"] == 100
    assert asyncio.run(_score_llm(bas, "s", "u", 50))["score"] == 0


def test_score_llm_repli_sur_erreur_api():
    exc = anthropic.APIConnectionError(
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    client = _FakeClient(exc=exc)
    r = asyncio.run(_score_llm(client, "s", "u", score_regles_fallback=63))
    assert r["score"] == 63
    assert r["priorite"] == "moyenne"
    assert "Repli" in r["justification"]


def test_score_llm_repli_sur_json_invalide():
    resp = SimpleNamespace(content=[SimpleNamespace(type="text", text="pas du json")])
    client = _FakeClient(resp=resp)
    r = asyncio.run(_score_llm(client, "s", "u", score_regles_fallback=41))
    assert r["score"] == 41
    assert "Repli" in r["justification"]


def test_score_llm_repli_sans_bloc_texte():
    client = _FakeClient(resp=SimpleNamespace(content=[]))   # next(...) -> StopIteration
    r = asyncio.run(_score_llm(client, "s", "u", score_regles_fallback=55))
    assert r["score"] == 55
