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


def test_regles_naf_normalise_point_insee():
    """Régression : le NAF INSEE réel arrive AVEC point (`45.20A`) alors que
    `criteres_ciblage.codes_naf` est stocké SANS point (`4520A`, cf.
    `sirene._naf_avec_point`). La comparaison doit normaliser les deux, sinon la
    pénalité -30 frappait à tort TOUT prospect réel (dotted ≠ dotless)."""
    crit = _criteres(codes_naf=["4520A", "4520B"], effectif_min=2, effectif_max=15)
    # Prospect réel : code_naf avec point → matche l'ICP dot-less après normalisation.
    dedans = _p(code_naf="45.20A", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    assert _score_regles(dedans, crit) == 55   # 35 + 20, PAS de -30
    # Contrôle : un NAF réellement hors ICP reste pénalisé.
    dehors = _p(code_naf="68.20B", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
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
def test_scoring_node_is_async_coroutine() -> None:
    """`scoring_node` est bien une coroutine async (règle #8)."""
    from agents.scoring_agent import scoring_node

    assert inspect.iscoroutinefunction(scoring_node)


# --- Node de scoring (#28) : I/O + couches monkeypatchées -------------------


class _FakeAsyncClient:
    """AsyncAnthropic factice — le node l'ouvre en context manager mais _score_llm
    est monkeypatché, donc le client n'est jamais réellement utilisé."""

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _patch_scoring_node(monkeypatch, scores_finaux):
    """Monkeypatch upsert/couches/agrégation + le client Claude. `scores_finaux` =
    liste des score_final renvoyés (1 par prospect scoré). Retourne les ids upsertés."""
    ids = []
    it = iter(scores_finaux)

    async def _fake_upsert(data):
        pid = f"id-{len(ids)}"
        ids.append(pid)
        return pid

    async def _fake_llm(client, sys, usr, score_regles_fallback):
        return {"score": 50, "justification": "x", "signaux_positifs": [],
                "signaux_negatifs": [], "priorite": "moyenne"}

    async def _fake_embedding(prospect, icp, prospect_id=None):
        return 0.5

    async def _fake_agreger(prospect_id, score_regles, llm, score_embedding,
                            config_scoring=None, **kw):
        return sa.ScoreResult(
            score_regles=score_regles, score_llm=llm["score"],
            score_embedding=score_embedding, score_final=next(it), priorite="moyenne",
        )

    monkeypatch.setattr(sa.anthropic, "AsyncAnthropic", _FakeAsyncClient)
    monkeypatch.setattr(sa, "upsert_prospect", _fake_upsert)
    monkeypatch.setattr(sa, "_score_llm", _fake_llm)
    monkeypatch.setattr(sa, "_score_embedding", _fake_embedding)
    monkeypatch.setattr(sa, "agreger_et_sauvegarder", _fake_agreger)
    return ids


def _state_scoring(prospects):
    return {"prospects": prospects, "criteres": _criteres(),
            "icp_embedding": None, "config_scoring": {}}


def test_scoring_node_compte_les_qualifies(monkeypatch):
    ids = _patch_scoring_node(monkeypatch, scores_finaux=[75, 20])  # 1 qualifie, 1 invalide
    state = _state_scoring([_p("A"), _p("B")])
    out = asyncio.run(sa.scoring_node(state))
    assert len(ids) == 2                # un upsert par prospect
    assert out["qualifies"] == 1        # seuls les >= 60 comptent
    assert out["erreurs"] == []


def test_scoring_node_isole_les_erreurs(monkeypatch):
    _patch_scoring_node(monkeypatch, scores_finaux=[80])  # 1 seul score consommé (le bon)

    async def _upsert_ko_puis_ok(data):
        if data["nom_entreprise"] == "KO":
            raise RuntimeError("upsert boom")
        return "id-ok"

    monkeypatch.setattr(sa, "upsert_prospect", _upsert_ko_puis_ok)
    state = _state_scoring([_p("KO"), _p("OK")])
    out = asyncio.run(sa.scoring_node(state))
    assert len(out["erreurs"]) == 1 and "KO" in out["erreurs"][0]
    assert out["qualifies"] == 1        # le prospect OK est bien scoré malgré l'échec du KO


def test_scoring_node_sans_prospects_ne_fait_rien(monkeypatch):
    ids = _patch_scoring_node(monkeypatch, scores_finaux=[])
    out = asyncio.run(sa.scoring_node({"prospects": [], "criteres": _criteres()}))
    assert ids == [] and out["qualifies"] == 0


def test_scoring_node_dry_run_n_ecrit_rien(monkeypatch):
    """dry-run (#29) : pas d'upsert, pas d'`agreger_et_sauvegarder` ; score via `_agreger`
    (réel), embedding sans persistance Qdrant (id=None), qualifiés quand même comptés."""
    appels = {"upsert": 0, "agreger": 0, "emb_id": "?"}

    async def _no_upsert(data):
        appels["upsert"] += 1
        return "id"

    async def _no_agreger(*a, **k):
        appels["agreger"] += 1

    async def _fake_llm(client, s, u, score_regles_fallback):
        return {"score": 100, "justification": "", "signaux_positifs": [],
                "signaux_negatifs": [], "priorite": "haute"}

    async def _fake_emb(prospect, icp, prospect_id=None):
        appels["emb_id"] = prospect_id
        return 1.0

    monkeypatch.setattr(sa.anthropic, "AsyncAnthropic", _FakeAsyncClient)
    monkeypatch.setattr(sa, "upsert_prospect", _no_upsert)
    monkeypatch.setattr(sa, "agreger_et_sauvegarder", _no_agreger)
    monkeypatch.setattr(sa, "_score_llm", _fake_llm)
    monkeypatch.setattr(sa, "_score_embedding", _fake_emb)

    state = {"prospects": [_p("A")], "criteres": _criteres(),
             "icp_embedding": None, "config_scoring": {}, "dry_run": True}
    out = asyncio.run(sa.scoring_node(state))
    assert appels["upsert"] == 0 and appels["agreger"] == 0   # AUCUNE écriture
    assert appels["emb_id"] is None                            # embedding non persisté
    # _agreger(0 règles, 100 llm, 1.0 emb, défaut) = 45 + 20 = 65 -> qualifie
    assert out["qualifies"] == 1


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


# --- Agrégation (#27) : _statut_pour_score / _agreger (purs) -----------------

@pytest.mark.parametrize(
    "score_final, attendu",
    [
        (100, "qualifie"),
        (60, "qualifie"),   # borne exacte ≥ 60
        (59, "nouveau"),
        (30, "nouveau"),    # borne exacte : 30 n'est PAS invalide
        (29, "invalide"),   # < 30
        (0, "invalide"),
    ],
)
def test_statut_pour_score_seuils_exacts(score_final, attendu):
    assert sa._statut_pour_score(score_final) == attendu


def test_agreger_poids_defaut_combinaison_connue():
    # 0.35*60 + 0.45*80 + 0.20*(0.5*100) = 21 + 36 + 10 = 67
    assert sa._agreger(60, 80, 0.5) == (67, "qualifie")


def test_agreger_embedding_x100_pas_x1():
    # score_embedding est un cosinus 0-1 ; il DOIT compter ×100 dans la somme.
    # emb=1.0 seul (poids défaut 0.20) => contribue 20 pts, pas 0.2.
    assert sa._agreger(0, 0, 1.0) == (20, "invalide")
    assert sa._agreger(0, 0, 0.0) == (0, "invalide")


def test_agreger_borne_haute_a_100():
    # Poids volontairement > 1 au total => brut dépasse 100 => clampé à 100.
    poids = {"poids_regles": 1.0, "poids_llm": 1.0, "poids_embedding": 1.0}
    assert sa._agreger(100, 100, 1.0, poids) == (100, "qualifie")


def test_agreger_poids_campagne_priment():
    # Config campagne 100% règles : seul score_regles compte.
    poids = {"poids_regles": 1.0, "poids_llm": 0.0, "poids_embedding": 0.0}
    assert sa._agreger(90, 10, 0.1, poids) == (90, "qualifie")


def test_agreger_poids_partiel_repli_par_cle():
    # Config incomplète (llm seul) : regles/embedding retombent sur le défaut.
    # 0.35*40 + 1.0*0 + 0.20*(1.0*100) = 14 + 0 + 20 = 34 -> nouveau
    assert sa._agreger(40, 0, 1.0, {"poids_llm": 1.0}) == (34, "nouveau")


def test_agreger_dict_vide_equivaut_au_defaut():
    assert sa._agreger(60, 80, 0.5, {}) == sa._agreger(60, 80, 0.5, None)


# --- Agrégation (#27) : agreger_et_sauvegarder (I/O monkeypatchées) ----------

def _fake_llm(score=88):
    return {
        "score": score,
        "justification": "match ICP",
        "signaux_positifs": ["site web"],
        "signaux_negatifs": [],
        "priorite": "haute",
    }


def _patch_save(monkeypatch):
    """Monkeypatch save_score (capture le score_data). `config_scoring` est un
    paramètre (issu de `state`), plus une lecture BDD — rien d'autre à patcher."""
    capture = {}

    async def _fake_save(prospect_id, score_data):
        capture["prospect_id"] = prospect_id
        capture["score_data"] = score_data

    monkeypatch.setattr(sa, "save_score", _fake_save)
    return capture


def test_agreger_et_sauvegarder_persiste_et_mappe(monkeypatch):
    cap = _patch_save(monkeypatch)
    res = asyncio.run(
        sa.agreger_et_sauvegarder(
            "pid-1", score_regles=90, llm=_fake_llm(10), score_embedding=0.9,
            config_scoring={"poids_regles": 1.0, "poids_llm": 0.0, "poids_embedding": 0.0},
            prompt_version="v1", modele_llm="claude-haiku-4-5",
        )
    )
    # 100% règles -> score_final = 90 -> qualifie ; sortie LLM mappée dans ScoreResult.
    assert (res.score_final, res.score_regles, res.score_llm) == (90, 90, 10)
    assert res.priorite == "haute" and res.signaux_positifs == ["site web"]

    sd = cap["score_data"]
    assert cap["prospect_id"] == "pid-1"
    assert sd["statut"] == "qualifie"
    assert sd["score_final"] == 90
    assert sd["modele_llm"] == "claude-haiku-4-5" and sd["prompt_version"] == "v1"
    # signaux + priorité + poids historisés dans details (audit #32).
    assert sd["details"]["priorite"] == "haute"
    assert sd["details"]["poids"] == {"poids_regles": 1.0, "poids_llm": 0.0, "poids_embedding": 0.0}


def test_agreger_et_sauvegarder_embedding_reste_cosinus(monkeypatch):
    # Le ×100 ne doit vivre QUE dans score_final, jamais dans la colonne score_embedding.
    cap = _patch_save(monkeypatch)
    res = asyncio.run(
        sa.agreger_et_sauvegarder(  # config_scoring omis -> None -> poids par défaut
            "pid-2", score_regles=0, llm=_fake_llm(0), score_embedding=0.5
        )
    )
    sd = cap["score_data"]
    assert sd["score_embedding"] == 0.5          # cosinus brut 0-1 persisté
    assert res.score_embedding == 0.5
    # 0.20 * (0.5*100) = 10 -> score_final 10, statut invalide (poids défaut, repli None).
    assert sd["score_final"] == 10 and sd["statut"] == "invalide"
