"""Tests du nettoyage (#19) — dédup + exclusions ICP + garde opposition + domicil.

Couvre : déduplication par SIRET (marque, ne supprime pas), exclusions client par
**mot entier** (règle #4, jamais sous-chaîne), filtre effectif hors cible, et le
fait que les filtres payants (opposition) / throttlés (domiciliation) ne tournent
que sur les survivants des filtres locaux. Réseau mocké — aucune vraie API.
"""
from __future__ import annotations

import inspect
import uuid

import pytest

from agents import nettoyage_agent as na
from agents.nettoyage_agent import (
    _matche_exclusion,
    _normalize,
    nettoyage_node,
)
from models.criteres import CriteresCiblage
from models.prospect import Prospect

CID = uuid.uuid4()

# SIRET Luhn-valides distincts (base 732829320000xx recalculée n'est pas triviale ;
# on réutilise des SIRET connus valides).
SIRET_A = "73282932000074"   # exemple python-stdnum
SIRET_B = "55208131766522"   # Danone (siège) — Luhn-valide


def _p(nom="Garage Durand", siret=None, siren=None, effectif_estime=None, **o) -> Prospect:
    return Prospect(
        campagne_id=CID, nom_entreprise=nom, siret=siret, siren=siren,
        effectif_estime=effectif_estime, **o,
    )


def _criteres(negatifs=None, effectif_min=1, effectif_max=500) -> CriteresCiblage:
    return CriteresCiblage(
        nom="ICP test", mots_cles_negatifs=negatifs or [],
        effectif_min=effectif_min, effectif_max=effectif_max,
    )


# --- Normalisation / exclusion par mot entier -------------------------------
def test_normalize_enleve_accents_et_ponctuation():
    assert _normalize("Éts. Durand-Groupe") == "ets durand groupe"


def test_exclusion_mot_entier_matche():
    p = _p(nom="Garage du Groupe Martin")
    assert _matche_exclusion(p, ["groupe"]) == "groupe"


def test_exclusion_pas_de_faux_positif_sous_chaine():
    # « groupe » ne doit PAS matcher « regroupement » (mot entier, pas sous-chaîne).
    p = _p(nom="Regroupement des Garages")
    assert _matche_exclusion(p, ["groupe"]) is None


def test_exclusion_multi_mots():
    p = _p(nom="Supermarché Groupe Casino Sud")
    assert _matche_exclusion(p, ["groupe casino"]) == "groupe casino"
    assert _matche_exclusion(_p(nom="Groupe Leclerc"), ["groupe casino"]) is None


# --- Node : async + noop ----------------------------------------------------
def test_nettoyage_node_is_async_coroutine():
    assert inspect.iscoroutinefunction(nettoyage_node)


@pytest.mark.asyncio
async def test_node_empty_prospects_noop():
    assert (await nettoyage_node({"prospects": []}))["prospects"] == []


# --- Helpers de mock : marquer_opposition / marquer_domiciliation -----------
def _mock_marqueurs(monkeypatch, oppose_siren=None):
    """Remplace les deux marqueurs réseau. `marquer_opposition` écrit le verdict
    dans raw_data (comme le vrai) selon `oppose_siren` ; enregistre les prospects
    reçus dans `vus['opp']` / `vus['dom']`."""
    oppose_siren = oppose_siren or set()
    vus: dict[str, list] = {"opp": [], "dom": []}

    async def _opp(prospects, client=None, settings=None, budget_credits=None, strict=False):
        prospects = list(prospects)
        vus["opp"] = prospects
        for p in prospects:
            oppose = p.siren in oppose_siren if p.siren else None
            p.raw_data = {**(p.raw_data or {}),
                          "opposition_commerciale": {"oppose": oppose}}
        return {}

    async def _dom(prospects, client=None, settings=None):
        vus["dom"] = list(prospects)
        return {}

    monkeypatch.setattr(na, "marquer_opposition", _opp)
    monkeypatch.setattr(na, "marquer_domiciliation", _dom)
    return vus


# --- Dédup ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_dedup_marque_doublon_sur_siret_repete(monkeypatch):
    vus = _mock_marqueurs(monkeypatch)
    p1, p2, p3 = _p(siret=SIRET_A), _p(siret=SIRET_A), _p(siret=SIRET_B)
    out = await nettoyage_node({"prospects": [p1, p2, p3], "criteres": _criteres()})
    ps = out["prospects"]
    assert ps[0].doublon is False   # 1re occurrence gardée
    assert ps[1].doublon is True    # 2e occurrence marquée
    assert ps[2].doublon is False
    # Le doublon n'est pas envoyé aux marqueurs payants.
    assert p2 not in vus["opp"]
    assert p1 in vus["opp"] and p3 in vus["opp"]


# --- Exclusions + effectif : pas de dépense sur les rejetés -----------------
@pytest.mark.asyncio
async def test_exclu_et_hors_cible_pas_envoyes_a_opposition(monkeypatch):
    vus = _mock_marqueurs(monkeypatch)
    ok = _p(nom="Garage Martin", siret=SIRET_A, effectif_estime=10)
    exclu = _p(nom="Groupe Renault", siret=SIRET_B, effectif_estime=10)
    trop_gros = _p(nom="Garage Grand", siren="552081317", effectif_estime=9000)
    state = {"prospects": [ok, exclu, trop_gros],
             "criteres": _criteres(negatifs=["groupe"], effectif_max=500)}
    await nettoyage_node(state)

    assert exclu.raw_data["nettoyage"]["exclusion"] == "groupe"
    assert trop_gros.raw_data["nettoyage"]["effectif_hors_cible"] is True
    # Seul le prospect propre atteint les marqueurs payants/throttlés.
    assert vus["opp"] == [ok]
    assert vus["dom"] == [ok]


# --- Garde d'opposition transmise au budget ---------------------------------
@pytest.mark.asyncio
async def test_budget_opposition_par_defaut_depuis_settings(monkeypatch):
    recu = {}

    async def _opp(prospects, client=None, settings=None, budget_credits=None, strict=False):
        recu["budget"] = budget_credits
        return {}

    async def _dom(prospects, client=None, settings=None):
        return {}

    monkeypatch.setattr(na, "marquer_opposition", _opp)
    monkeypatch.setattr(na, "marquer_domiciliation", _dom)
    # settings.opposition_budget_credits par défaut = None ; on force via param.
    await nettoyage_node({"prospects": [_p(siren="552081317")], "criteres": _criteres()},
                         budget_opposition=5)
    assert recu["budget"] == 5


@pytest.mark.asyncio
async def test_sans_criteres_ne_plante_pas(monkeypatch):
    _mock_marqueurs(monkeypatch)
    out = await nettoyage_node({"prospects": [_p(siret=SIRET_A)]})  # pas de criteres
    assert out["prospects"][0].doublon is False
