"""Tests du node Sirene INSEE (agents/sirene_agent.py).

Issue #17 — Tests intégration Sirene (50 prospects réels).

Contient :
- Tests de structure (non-integration) : le node est une coroutine async,
  fail-fast si `state['criteres']` absent, et la clé API est vérifiée.
- Test unitaire du parsing INSEE → Prospect (non-integration) : valide la
  cohérence SIRET (14 chiffres) / SIREN (9 premiers) sans consommer de quota.
- Test unitaire du retry 429 (non-integration) : mocke httpx, n'a pas besoin
  de clé INSEE réelle.
- Tests d'intégration (`@pytest.mark.integration`) : tapent la vraie API INSEE,
  skippés automatiquement si `INSEE_API_KEY` n'est pas renseignée (voir
  `conftest.py` pour la gestion du marker).
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
    """Le node échoue vite si `state['criteres']` est absent (contrat d'entrée).

    Ancien STUB #11 attendait NotImplementedError ; le node est désormais
    implémenté (#15) et lève KeyError sur un état vide — on valide le contrat
    réel de fail-fast plutôt qu'un stub périmé.
    """
    from agents.sirene_agent import sirene_node

    with pytest.raises(KeyError):
        asyncio.run(sirene_node({}))


def test_sirene_node_fail_fast_si_api_key_absente() -> None:
    """Le node lève RuntimeError si INSEE_API_KEY est vide (sécurité quota).

    On patch get_settings pour forcer une clé vide : évite toute dépendance
    au .env réel et garantit le test en CI.
    """
    from agents.sirene_agent import sirene_node

    faux_settings = MagicMock()
    faux_settings.insee_api_key = ""
    with patch("agents.sirene_agent.get_settings", return_value=faux_settings):
        with pytest.raises(RuntimeError, match="INSEE_API_KEY manquante"):
            asyncio.run(sirene_node(_etat_test()))


# ===========================================================================
# Test unitaire du parsing — non-integration (AC1 SIRET valide sans quota)
# ===========================================================================

def test_parser_etablissement_siret_coherent_avec_siren() -> None:
    """AC1 (validation SIRET) sans consommer de quota INSEE.

    À partir d'un JSON établissement factice (format INSEE 3.11), on vérifie
    que `_parser_etablissement` produit un Prospect dont :
    - le SIRET fait 14 chiffres ;
    - le SIREN fait 9 chiffres ;
    - le SIREN == 9 premiers chiffres du SIRET (cohérence INSEE).
    """
    from agents.sirene_agent import _parser_etablissement

    etab = {
        "siret": _FIXTURE_SIRET,
        "siren": _FIXTURE_SIREN,
        "uniteLegale": {"denominationUniteLegale": "TEST SA"},
        "adresseEtablissement": {
            "codePostalEtablissement": "75001",
            "libelleCommuneEtablissement": "Paris",
        },
        "periodesEtablissement": [
            {"activitePrincipaleEtablissement": _NAF_CONSEIL_INFO}
        ],
    }

    prospect = _parser_etablissement(etab, _CAMPAGNE_ID)

    assert prospect is not None
    assert len(prospect.siret) == 14
    assert prospect.siret.isdigit()
    assert len(prospect.siren) == 9
    assert prospect.siren.isdigit()
    assert prospect.siret[:9] == prospect.siren, (
        "Le SIREN doit être les 9 premiers chiffres du SIRET."
    )


def test_parser_etablissement_siret_invalide_renvoie_none() -> None:
    """Un établissement au SIRET invalide est ignoré (renvoie None), pas crash."""
    from agents.sirene_agent import _parser_etablissement

    etab = {
        "siret": "123",  # invalide : trop court
        "siren": "123",
        "uniteLegale": {"denominationUniteLegale": "Bogus"},
        "adresseEtablissement": {},
        "periodesEtablissement": [{}],
    }
    assert _parser_etablissement(etab, _CAMPAGNE_ID) is None


# ===========================================================================
# Test unitaire du retry 429 — non-integration (mock httpx, pas de clé)
# ===========================================================================

@pytest.mark.asyncio
async def test_fetch_etablissements_retry_sur_429_puis_reussit() -> None:
    """AC #4 — `_fetch_etablissements` retry sur 429 puis réussit.

    Marqué non-integration : mocke le transport httpx, ne consomme aucun
    quota INSEE et n'a pas besoin de clé réelle. On patche `asyncio.sleep`
    pour éviter d'attendre 2 s réelles.

    Vérifie que :
    - le 1er appel reçoit 429 → log + sleep + retry ;
    - le 2e appel reçoit 200 → données retournées ;
    - exactement 2 appels HTTP effectués (1 retry) ;
    - `asyncio.sleep` a été appelé (throttle respecté).
    """
    import agents.sirene_agent as mod

    resp_429 = MagicMock(status_code=429)
    resp_429.raise_for_status = MagicMock(side_effect=AssertionError(
        "raise_for_status ne doit pas être appelé sur un 429"))
    resp_200 = MagicMock(status_code=200)
    resp_200.raise_for_status = MagicMock()
    resp_200.json = MagicMock(return_value={
        "etablissements": [{"siret": _FIXTURE_SIRET, "siren": _FIXTURE_SIREN}],
        "header": {"total": 1},
    })

    appels = {"n": 0}

    async def fake_get(url, params=None, headers=None):
        appels["n"] += 1
        if appels["n"] == 1:
            return resp_429
        return resp_200

    client = MagicMock()
    client.get = fake_get

    sleep_mock = AsyncMock()
    with patch.object(mod.asyncio, "sleep", sleep_mock):
        result = await mod._fetch_etablissements(
            client, {}, _DEPT_PARIS, _NAF_CONSEIL_INFO, limit=10,
        )

    assert result == [{"siret": _FIXTURE_SIRET, "siren": _FIXTURE_SIREN}]
    assert appels["n"] == 2, "devrait faire exactement 1 retry (2 appels total)"
    assert sleep_mock.await_count >= 1, "devrait respecter le throttle (sleep)"


@pytest.mark.asyncio
async def test_fetch_etablissements_429_persistent_lance_runtime_error() -> None:
    """Si le 429 persiste au-delà de MAX_RETRIES, on lève RuntimeError."""
    import agents.sirene_agent as mod

    resp_429 = MagicMock(status_code=429)
    client = MagicMock()

    async def fake_get(*a, **k):
        return resp_429

    client.get = fake_get

    sleep_mock = AsyncMock()
    with patch.object(mod.asyncio, "sleep", sleep_mock):
        with pytest.raises(RuntimeError, match="429 persistant"):
            await mod._fetch_etablissements(
                client, {}, _DEPT_PARIS, _NAF_CONSEIL_INFO, limit=10,
            )

    # MAX_RETRIES = 3 dans le module ; on doit avoir 3 tentatives + 3 sleeps.
    assert sleep_mock.await_count == mod.MAX_RETRIES


# ===========================================================================
# Tests d'intégration — vraie API INSEE (skippés sans INSEE_API_KEY)
# ===========================================================================

def _insee_key_disponible() -> str | None:
    """Retourne la clé INSEE si elle est renseignée, sinon None."""
    from config.settings import get_settings
    return get_settings().insee_api_key or None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_50_prospects_reels_siret_valides() -> None:
    """AC1 — Récupère 50 prospects réels via l'API INSEE, 100% SIRET valides.

    ICP de test générique (non sectoriel) : 6202Z (conseil informatique) en
    département 75. Skip si `INSEE_API_KEY` n'est pas renseignée.
    """
    key = _insee_key_disponible()
    if not key:
        pytest.skip(
            "INSEE_API_KEY manquante dans .env — tests 1-3 de l'issue #17 "
            "nécessitent une clé API INSEE valide (api-sirene/3.11)."
        )

    from agents.sirene_agent import sirene_node

    etat = _etat_test(
        criteres=_criteres_test(
            codes_naf=[_NAF_CONSEIL_INFO],
            departements=[_DEPT_PARIS],
        ),
    )
    etat = await sirene_node(etat, limit=50)

    prospects = etat.get("prospects", [])
    assert len(prospects) >= 50, (
        f"devrait récupérer ≥ 50 prospects réels (obtenu : {len(prospects)}). "
        "Si le volume est insuffisant, élargir le couple NAF/dept."
    )

    # AC1 : 100% des SIRET valides (14 chiffres, cohérents avec SIREN).
    invalides = []
    for p in prospects:
        if not (p.siret and len(p.siret) == 14 and p.siret.isdigit()):
            invalides.append(f"SIRET non 14 chiffres : {p.siret!r}")
            continue
        if not (p.siren and len(p.siren) == 9 and p.siren.isdigit()):
            invalides.append(f"SIREN non 9 chiffres : {p.siren!r}")
            continue
        if p.siret[:9] != p.siren:
            invalides.append(
                f"SIRET {p.siret} / SIREN {p.siren} incohérents"
            )
    assert not invalides, (
        f"{len(invalides)} SIRET/SIREN invalides sur {len(prospects)} :\n"
        + "\n".join(invalides[:10])
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_pagination_volume_superieur_100() -> None:
    """AC #3 — `_fetch_etablissements` pagine correctement sur > 100 résultats.

    On demande un volume > 100 (limite 150) sur un couple NAF/dept à fort
    volume (6202Z en 92 — Hauts-de-Seine). Vérifie que la pagination ramène
    bien les établissements au-delà de la 1re page. Skip sans clé INSEE.
    """
    key = _insee_key_disponible()
    if not key:
        pytest.skip(
            "INSEE_API_KEY manquante dans .env — tests 1-3 de l'issue #17 "
            "nécessitent une clé API INSEE valide (api-sirene/3.11)."
        )

    import agents.sirene_agent as mod

    # On appelle `_fetch_etablissements` directement pour valider la
    # pagination indépendamment du reste du node.
    headers = {"X-INSEE-Api-Key-Integration": key, "Accept": "application/json"}
    async with mod.httpx.AsyncClient(timeout=30.0) as client:
        etabs = await mod._fetch_etablissements(
            client, headers, _DEPT_HAUTS_DE_SEINE, _NAF_CONSEIL_INFO, limit=150,
        )

    assert len(etabs) > 100, (
        f"la pagination devrait ramener > 100 établissements "
        f"(obtenu : {len(etabs)}). Le couple {_NAF_CONSEIL_INFO}/"
        f"{_DEPT_HAUTS_DE_SEINE} devrait être à fort volume."
    )
    # Tous les SIRET renvoyés par l'API font 14 chiffres (format INSEE).
    for e in etabs:
        siret = e.get("siret", "")
        assert len(siret) == 14 and siret.isdigit(), (
            f"SIRET INSEE mal formé : {siret!r}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_50_prospects_multi_naf_multi_depts() -> None:
    """AC1 (variante) — 50 prospects sur 2 NAF × 2 départements.

    Vérifie que l'itération sur tous les couples (dept, NAF) de l'ICP
    fonctionne et agrège bien les résultats. Skip sans clé INSEE.
    """
    key = _insee_key_disponible()
    if not key:
        pytest.skip(
            "INSEE_API_KEY manquante dans .env — tests 1-3 de l'issue #17 "
            "nécessitent une clé API INSEE valide (api-sirene/3.11)."
        )

    from agents.sirene_agent import sirene_node

    etat = _etat_test(
        criteres=_criteres_test(
            codes_naf=[_NAF_PROGRAMMATION, _NAF_CONSEIL_INFO],
            departements=[_DEPT_PARIS, _DEPT_HAUTS_DE_SEINE],
        ),
    )
    etat = await sirene_node(etat, limit=50)

    prospects = etat.get("prospects", [])
    assert len(prospects) >= 50, (
        f"devrait récupérer ≥ 50 prospects sur 2 NAF × 2 depts "
        f"(obtenu : {len(prospects)})."
    )
    # Cohérence SIRET/SIREN sur l'ensemble.
    for p in prospects:
        assert p.siret and len(p.siret) == 14 and p.siret.isdigit()
        assert p.siren and len(p.siren) == 9 and p.siren.isdigit()
        assert p.siret[:9] == p.siren