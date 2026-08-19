"""Tests de la config LangSmith (#30) — purs, sans réseau, sans langsmith installé.

`configure_tracing` ne fait que propager `LANGCHAIN_*` de `settings` vers
l'environnement. On mocke `settings` et on isole `os.environ` par test.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

from utils import tracing


def _fake_settings(**o) -> SimpleNamespace:
    base = dict(
        langchain_tracing_v2=False,
        langchain_api_key="",
        langchain_project="prospection-b2b",
        langchain_endpoint="",
    )
    base.update(o)
    return SimpleNamespace(**base)


def test_desactive_par_defaut(monkeypatch):
    monkeypatch.setattr(tracing, "get_settings", lambda: _fake_settings())
    assert tracing.configure_tracing() is False


def test_active_avec_cle_pose_les_env(monkeypatch):
    # Isole os.environ (copie restaurée en fin de test).
    monkeypatch.setattr(os, "environ", dict(os.environ))
    monkeypatch.setattr(tracing, "get_settings", lambda: _fake_settings(
        langchain_tracing_v2=True,
        langchain_api_key="ls-secret",
        langchain_project="proj-x",
        langchain_endpoint="https://eu.smith.langchain.com",
    ))

    assert tracing.configure_tracing() is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "ls-secret"
    assert os.environ["LANGCHAIN_PROJECT"] == "proj-x"
    assert os.environ["LANGCHAIN_ENDPOINT"] == "https://eu.smith.langchain.com"


def test_active_sans_cle_ne_trace_pas(monkeypatch):
    """Traçage demandé mais clé absente → désactivé (pas de trace partielle)."""
    monkeypatch.setattr(os, "environ", dict(os.environ))
    monkeypatch.setattr(tracing, "get_settings", lambda: _fake_settings(
        langchain_tracing_v2=True, langchain_api_key="",
    ))
    assert tracing.configure_tracing() is False
    # Rien n'a été forcé dans l'environnement.
    assert os.environ.get("LANGCHAIN_API_KEY", "") == ""


def test_endpoint_optionnel_non_pose_si_vide(monkeypatch):
    monkeypatch.setattr(os, "environ", dict(os.environ))
    monkeypatch.delenv("LANGCHAIN_ENDPOINT", raising=False)
    monkeypatch.setattr(tracing, "get_settings", lambda: _fake_settings(
        langchain_tracing_v2=True, langchain_api_key="ls-secret", langchain_endpoint="",
    ))
    assert tracing.configure_tracing() is True
    assert "LANGCHAIN_ENDPOINT" not in os.environ


# --- #30 : câblage effectif du traçage (décorateur + orchestrateur) ----------

def test_score_llm_porte_traceable():
    """L'appel Claude `_score_llm` est décoré `@traceable` (observabilité #30).

    Import gardé : langsmith installé → le décorateur enrobe la fonction (attribut
    `__wrapped__` posé par functools.wraps) ; absent → no-op, la fonction reste
    appelable. Dans les deux cas `traceable` existe et `_score_llm` est callable."""
    import agents.scoring_agent as sa
    assert callable(sa.traceable)
    assert callable(sa._score_llm)
    try:
        import langsmith  # noqa: F401
    except ImportError:
        return  # décorateur no-op : rien de plus à asserter
    assert hasattr(sa._score_llm, "__wrapped__")


def test_run_configure_le_tracage(monkeypatch):
    """`graph.workflow.run` active le traçage au démarrage (#30) avant les nodes."""
    import asyncio

    from graph import workflow

    appels: list[int] = []
    monkeypatch.setattr(workflow, "configure_tracing", lambda: appels.append(1) or False)
    # État vide : init_campagne (prérequis) lève faute de campagne_id → run stoppe.
    # `configure_tracing` est appelé AVANT la boucle, donc bien enregistré.
    asyncio.run(workflow.run({}))
    assert appels, "run() doit appeler configure_tracing au démarrage"
