"""Tests du node Sirene INSEE (agents/sirene_agent.py).

Issue #11 — structure. L'implémentation réelle a été portée par l'issue #15
(PR #62) : `sirene_node` interroge l'API Sirene 3.11 à partir des critères de
l'état. Les tests qui tapent l'API INSEE réelle sont marqués
`@pytest.mark.integration` (exclu des runs par défaut, voir conftest.py).

Ici on ne vérifie que la structure (pas d'API touchée) :
- le node est une coroutine async (règle #8) ;
- il fail-fast si l'état est incomplet (clé `criteres` ou `campagne_id`
  absente) — cohérent avec la règle #3 (aucune valeur ICP par défaut).
"""
from __future__ import annotations

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

# ---------------------------------------------------------------------------
# Constantes de test — codes NAF et départements RÉELS mais NON sectoriels
# (choisis pour leur fort volume en Île-de-France : 6201Z = programmation
# informatique, 6202Z = conseil en informatique). Aucun ICP codé en dur dans
# la logique de production — ces valeurs ne vivent que dans les fixtures de
# test (exclues du garde-fou test_no_hardcoded_icp.py).
# ---------------------------------------------------------------------------
_NAF_PROGRAMMATION = "6201Z"
_NAF_CONSEIL_INFO = "6202Z"
_DEPT_PARIS = "75"
_DEPT_HAUTS_DE_SEINE = "92"

_CAMPAGNE_ID = UUID("00000000-0000-0000-0000-000000000001")
_CLIENT_ID = UUID("00000000-0000-0000-0000-000000000002")

# SIRET/SIREN valides (checksum Luhn OK) pour fixtures sans appel API.
# SIREN 734000003 (8 chiffres + clé Luhn) ; SIRET = SIREN + NIC 0000 + clé.
_FIXTURE_SIREN = "734000003"
_FIXTURE_SIRET = "73400000300008"


def _criteres_test(*, codes_naf: list[str] | None = None,
                   departements: list[str] | None = None):
    """Construit un CriteresCiblage générique (non sectoriel) pour les tests."""
    from models.criteres import CriteresCiblage

    return CriteresCiblage(
        nom="ICP de test générique (non sectoriel)",
        codes_naf=codes_naf or [_NAF_CONSEIL_INFO],
        departements=departements or [_DEPT_PARIS],
        effectif_min=1,
        effectif_max=500,
    )


def _etat_test(**overrides) -> dict:
    """Construit un EtatAgent minimal pour appeler sirene_node."""
    etat = {
        "campagne_id": str(_CAMPAGNE_ID),
        "client_id": str(_CLIENT_ID),
        "criteres": _criteres_test(),
        "prospects": [],
    }
    etat.update(overrides)
    return etat


# ===========================================================================
# Tests de structure (non-integration) — conservés / mis à jour depuis #11
# ===========================================================================

def test_sirene_node_is_async_coroutine() -> None:
    """sirene_node est bien une coroutine async (règle #8)."""
    from agents.sirene_agent import sirene_node

    assert inspect.iscoroutinefunction(sirene_node)


def test_sirene_node_fail_fast_si_criteres_absents() -> None:
    """Issue #15 — le node fail-fast si l'état n'est pas peuplé (règle #3).

    `sirene_node` lit `state["criteres"]` : un état vide doit lever une erreur
    explicite (KeyError), jamais fallback sur des valeurs par défaut. On
    n'attend plus NotImplementedError depuis que #15 a implémenté le node.
    """
    from agents.sirene_agent import sirene_node

    # État vide : ni `criteres` ni `campagne_id` → KeyError, pas NotImplementedError.
    with pytest.raises(KeyError):
        asyncio.run(sirene_node({}))
