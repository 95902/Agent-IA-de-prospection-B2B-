"""Tests du CLI (#29) — routing des modes + internals des commandes.

Purs : `graph.workflow.run` et `utils.db` sont monkeypatchés → aucun accès stack.
Le mode ad hoc DOIT forcer `dry_run` (pas de campagne en base pour persister).
"""
from __future__ import annotations

import asyncio

import pytest

import main

VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"


# --- Routing (main() → bonne commande / erreurs d'usage) --------------------

def _stub_cmd(store, key):
    async def _fn(*args, **kw):
        store[key] = args
        return 0
    return _fn


def test_route_list_campagnes(monkeypatch):
    appels = {}
    monkeypatch.setattr(main, "_lister_campagnes", _stub_cmd(appels, "list"))
    assert main.main(["--list-campagnes"]) == 0
    assert "list" in appels


def test_route_campagne(monkeypatch):
    appels = {}
    monkeypatch.setattr(main, "_run_campagne", _stub_cmd(appels, "camp"))
    assert main.main(["--campagne-id", VALID_UUID, "--limit", "10", "--dry-run"]) == 0
    assert appels["camp"] == (VALID_UUID, 10, True)


def test_route_adhoc(monkeypatch):
    appels = {}
    monkeypatch.setattr(main, "_run_adhoc", _stub_cmd(appels, "adhoc"))
    assert main.main(["--depts", "75,92", "--naf", "45.20A"]) == 0
    assert appels["adhoc"] == ("75,92", "45.20A", None)


def test_conflit_campagne_et_adhoc_exit_2():
    with pytest.raises(SystemExit) as exc:
        main.main(["--campagne-id", VALID_UUID, "--depts", "75"])
    assert exc.value.code == 2


def test_aucun_mode_exit_2():
    with pytest.raises(SystemExit) as exc:
        main.main([])
    assert exc.value.code == 2


# --- Internals des commandes (run / db monkeypatchés) -----------------------

def _patch_run(monkeypatch, retour):
    """Patch graph.workflow.run (capture le state) + utils.db.close (no-op)."""
    import graph.workflow as wf
    from utils import db
    capture = {}

    async def _fake_run(state):
        capture["state"] = state
        return retour

    async def _fake_close():
        capture["closed"] = True

    monkeypatch.setattr(wf, "run", _fake_run)
    monkeypatch.setattr(db, "close", _fake_close)
    return capture


def test_run_campagne_construit_le_state(monkeypatch):
    cap = _patch_run(monkeypatch, {"collectes": 3, "qualifies": 1, "erreurs": []})
    rc = asyncio.run(main._run_campagne(VALID_UUID, 10, dry_run=True))
    assert rc == 0
    assert cap["state"]["campagne_id"] == VALID_UUID
    assert cap["state"]["dry_run"] is True and cap["state"]["limit"] == 10
    assert cap["closed"] is True          # pool fermé même en succès


def test_run_campagne_uuid_invalide_ne_lance_rien(monkeypatch):
    cap = _patch_run(monkeypatch, {})
    rc = asyncio.run(main._run_campagne("pas-un-uuid", None, dry_run=False))
    assert rc == 2 and "state" not in cap  # run jamais appelé


def test_run_campagne_echec_prerequis_code_1(monkeypatch):
    cap = _patch_run(monkeypatch, {"erreurs": ["init_campagne: campagne introuvable"]})
    rc = asyncio.run(main._run_campagne(VALID_UUID, None, dry_run=False))
    assert rc == 1 and "state" in cap      # a bien tourné, mais prérequis KO


def test_run_adhoc_force_dry_run_et_synthetise_l_icp(monkeypatch):
    cap = _patch_run(monkeypatch, {"collectes": 0, "qualifies": 0, "erreurs": []})
    rc = asyncio.run(main._run_adhoc("75,92", "45.20A,45.20B", 50))
    assert rc == 0
    st = cap["state"]
    assert st["dry_run"] is True                        # ad hoc = dry-run forcé
    assert st["criteres"].departements == ["75", "92"]
    assert st["criteres"].codes_naf == ["45.20A", "45.20B"]
    assert st["limit"] == 50 and st["icp_embedding"] is None
    assert "campagne_id" in st                          # UUID jetable présent
