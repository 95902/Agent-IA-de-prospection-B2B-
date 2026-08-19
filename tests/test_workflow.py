"""Tests de l'orchestration du pipeline (#28) — `graph.workflow.run` / `build_graph`.

Purs : on monkeypatche `_PIPELINE` avec des nodes factices (les vrais nodes ont
leurs propres tests). On vérifie l'ordre d'exécution, l'arrêt sur node prérequis
et la poursuite sur node non-prérequis, et l'enregistrement des erreurs.
"""
from __future__ import annotations

import asyncio

from graph import workflow as wf


def _recorder(nom):
    """Node factice : note son passage dans state['ordre'] et renvoie l'état."""
    async def _node(state):
        state.setdefault("ordre", []).append(nom)
        return state
    return _node


def _boom(nom):
    async def _node(state):
        raise RuntimeError(f"{nom} explose")
    return _node


def test_build_graph_expose_les_5_nodes_dans_l_ordre():
    noms = [nom for nom, _node, _prereq in wf.build_graph()]
    assert noms == ["init_campagne", "fetch_sirene", "enrichir", "nettoyer", "scorer"]


def test_run_execute_les_nodes_en_sequence(monkeypatch):
    monkeypatch.setattr(wf, "_PIPELINE", (
        ("a", _recorder("a"), True),
        ("b", _recorder("b"), True),
        ("c", _recorder("c"), False),
    ))
    out = asyncio.run(wf.run({"campagne_id": "x"}))
    assert out["ordre"] == ["a", "b", "c"]
    assert out["erreurs"] == []
    # run() initialise les compteurs de suivi.
    assert out["qualifies"] == 0 and out["collectes"] == 0


def test_run_arrete_sur_node_prerequis_en_echec(monkeypatch):
    monkeypatch.setattr(wf, "_PIPELINE", (
        ("a", _recorder("a"), True),
        ("b", _boom("b"), True),          # prérequis KO -> stop
        ("c", _recorder("c"), False),
    ))
    out = asyncio.run(wf.run({"campagne_id": "x"}))
    assert out["ordre"] == ["a"]          # c n'a jamais tourné
    assert len(out["erreurs"]) == 1 and out["erreurs"][0].startswith("b:")


def test_run_continue_apres_node_non_prerequis_en_echec(monkeypatch):
    monkeypatch.setattr(wf, "_PIPELINE", (
        ("a", _recorder("a"), True),
        ("b", _boom("b"), False),         # non prérequis -> on logge et on continue
        ("c", _recorder("c"), False),
    ))
    out = asyncio.run(wf.run({"campagne_id": "x"}))
    assert out["ordre"] == ["a", "c"]     # c a bien tourné malgré l'échec de b
    assert len(out["erreurs"]) == 1 and out["erreurs"][0].startswith("b:")
