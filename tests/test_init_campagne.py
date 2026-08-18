"""Tests du node `init_campagne` — issue #16.

Couvre les 2 critères d'acceptance :
- AC1 : `init_campagne` retourne un `EtatAgent` avec tous les critères de la
  campagne correctement chargés (codes NAF, départements, effectif min/max,
  ancienneté min, mots-clés +/-, ICP embedding **vecteur** résolu, config_scoring).
- AC2 : Erreur claire et explicite si la campagne ou ses critères n'existent pas
  (fail fast, pas de valeurs par défaut silencieuses).

Stratégie de test (CLAUDE.md) :
- Tests unitaires avec mock de la couche DB (AC2 + logique de mapping AC1) :
  ils tournent sans Postgres/Qdrant, sans marquage `integration`.
- Tests d'intégration (AC1 bout-en-bout avec vraie BDD) marqués
  `@pytest.mark.integration` — exclus du run par défaut (voir conftest.py).
  Ils requièrent la fixture SQL `tests/fixtures/init_campagne_test_data.sql`.

Aucune valeur métier ICP codée en dur dans la logique de production testée :
`init_campagne` ne fait que lire la BDD et peupler `EtatAgent`. Les UUIDs et
valeurs ci-dessous sont des données de test (le garde-fou
`test_no_hardcoded_icp.py` exclut le répertoire `tests/`).
"""
from __future__ import annotations

import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from utils import db

# UUIDs stables alignés sur tests/fixtures/init_campagne_test_data.sql.
CLIENT_ID = "11111111-1111-4111-8111-111111111111"
CRITERE_ID = "22222222-2222-4222-8222-222222222222"
ICP_PROFILE_ID = "33333333-3333-4333-8333-333333333333"
CAMPAGNE_ID = "44444444-4444-4444-8444-444444444444"


# --- Helpers ---------------------------------------------------------------

def _fake_campagne_row(
    *,
    campagne_id: str = CAMPAGNE_ID,
    client_id: str = CLIENT_ID,
    critere_id: str = CRITERE_ID,
    icp_profile_id: str | None = ICP_PROFILE_ID,
    config_scoring: dict | None = None,
) -> dict:
    """Row simulée renvoyée par la lecture PG de `campagnes`."""
    return {
        "id": uuid.UUID(campagne_id),
        "client_id": uuid.UUID(client_id),
        "critere_id": uuid.UUID(critere_id),
        "icp_profile_id": uuid.UUID(icp_profile_id) if icp_profile_id else None,
        "nom": "Campagne test pilote",
        "config_scoring": config_scoring
        or {"poids_regles": 0.35, "poids_llm": 0.45, "poids_embedding": 0.20},
    }


def _fake_critere_row(*, critere_id: str = CRITERE_ID) -> dict:
    """Row simulée renvoyée par la lecture PG de `criteres_ciblage`."""
    return {
        "id": uuid.UUID(critere_id),
        "client_id": uuid.UUID(CLIENT_ID),
        "nom": "Cible test pilote",
        "description_icp": "Profil cible de test pour validation du pipeline",
        "codes_naf": ["6201Z", "6202Z"],
        "departements": ["75", "92"],
        "effectif_min": 3,
        "effectif_max": 50,
        "anciennete_min_ans": 2,
        "exiger_site_web": True,
        "exiger_email": False,
        "mots_cles_positifs": ["qualite", "service"],
        "mots_cles_negatifs": ["exclusion1", "exclusion2"],
        "actif": True,
    }


def _fake_icp_point_id(*, icp_id: str = ICP_PROFILE_ID) -> str:
    """qdrant_point_id simulé (str UUID)."""
    return icp_id


def _make_pool_mock(campagne_row, critere_row, icp_point_id):
    """Construit un mock du pool asyncpg avec les rows attendues.

    `init_campagne` fait 2 requêtes PG :
    1. SELECT campagnes + icp_profiles.qdrant_point_id (1 fetchrow)
    2. SELECT criteres_ciblage (1 fetchrow)
    On sérialise via `side_effect`.
    """
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(side_effect=[campagne_row, critere_row])
    pool = AsyncMock()
    pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=conn),
        __aexit__=AsyncMock(return_value=None),
    ))
    return pool, conn


# --- Structure : signature async + TypedDict -------------------------------

def test_init_campagne_is_async_coroutine() -> None:
    """Le node est une coroutine async (règle #8 async partout)."""
    from graph.workflow import init_campagne

    assert inspect.iscoroutinefunction(init_campagne)


# --- AC2 : erreurs explicites (tests unitaires, mock DB) -------------------

@pytest.mark.asyncio
async def test_ac2_campagne_inconnue_leve_erreur_claire() -> None:
    """AC2 : campagne_id inconnu → erreur explicite, pas de valeur par défaut."""
    from graph.workflow import init_campagne, CampagneIntrouvableError

    inconnu = str(uuid.uuid4())
    # campagnes.fetchrow retourne None → init_campagne doit fail fast.
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    pool = AsyncMock()
    pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=conn),
        __aexit__=AsyncMock(return_value=None),
    ))

    with patch("graph.workflow.db.get_pg_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(CampagneIntrouvableError) as exc_info:
            await init_campagne({"campagne_id": inconnu})

    assert inconnu in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac2_criteres_manquants_leve_erreur_claire() -> None:
    """AC2 : campagne existe mais criteres_ciblage supprimé → erreur explicite.

    Simule un critere_id orphelin (référence cassée) — doit échouer plutôt que
    de remplir silencieusement des valeurs par défaut.
    """
    from graph.workflow import init_campagne, CriteresIntrouvablesError

    campagne = _fake_campagne_row()
    # 2e fetchrow (criteres_ciblage) retourne None.
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(side_effect=[campagne, None])
    pool = AsyncMock()
    pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=conn),
        __aexit__=AsyncMock(return_value=None),
    ))

    with patch("graph.workflow.db.get_pg_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(CriteresIntrouvablesError) as exc_info:
            await init_campagne({"campagne_id": CAMPAGNE_ID})

    assert CRITERE_ID in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac2_champ_campagne_id_manquant_leve_erreur() -> None:
    """AC2 : `campagne_id` absent de l'état initial → erreur explicite (fail fast)."""
    from graph.workflow import init_campagne, CampagneIntrouvableError

    with patch("graph.workflow.db.get_pg_pool", new_callable=AsyncMock):
        with pytest.raises((CampagneIntrouvableError, ValueError, KeyError)):
            await init_campagne({})  # pas de campagne_id


# --- AC1 : mapping DB → EtatAgent (tests unitaires, mock DB) ---------------

@pytest.mark.asyncio
async def test_ac1_unit_charge_tous_les_criteres() -> None:
    """AC1 (mock DB) : tous les champs criteres_ciblage mappés dans EtatAgent."""
    from graph.workflow import init_campagne

    campagne = _fake_campagne_row()
    critere = _fake_critere_row()
    icp_point_id = _fake_icp_point_id()
    # La 1re requête (campagnes JOIN icp_profiles) renvoie une row combinée
    # avec qdrant_point_id. On fusionne dans le mock.
    campagne_row = {**campagne, "qdrant_point_id": uuid.UUID(icp_point_id)}

    pool, conn = _make_pool_mock(campagne_row, critere, icp_point_id)

    fake_vecteur = [0.1, 0.2, 0.3]  # vecteur ICP résolu depuis Qdrant (mocké)
    with patch("graph.workflow.db.get_pg_pool", new_callable=AsyncMock, return_value=pool), \
         patch("graph.workflow.db.get_icp_embedding", new_callable=AsyncMock,
               return_value=fake_vecteur) as mock_get_icp:
        etat = await init_campagne({"campagne_id": CAMPAGNE_ID})

    # EtatAgent peuplé correctement.
    assert etat["campagne_id"] == CAMPAGNE_ID
    assert etat["client_id"] == CLIENT_ID
    assert isinstance(etat["criteres"], CriteresCiblage)
    crit: CriteresCiblage = etat["criteres"]
    assert crit.id == uuid.UUID(CRITERE_ID)
    assert crit.codes_naf == ["6201Z", "6202Z"]
    assert crit.departements == ["75", "92"]
    assert crit.effectif_min == 3
    assert crit.effectif_max == 50
    assert crit.anciennete_min_ans == 2
    assert crit.exiger_site_web is True
    assert crit.exiger_email is False
    assert crit.mots_cles_positifs == ["qualite", "service"]
    assert crit.mots_cles_negatifs == ["exclusion1", "exclusion2"]
    # ICP embedding : le VECTEUR est résolu depuis Qdrant via le qdrant_point_id.
    mock_get_icp.assert_awaited_once_with(icp_point_id)
    assert etat["icp_embedding"] == fake_vecteur
    assert etat["config_scoring"]["poids_llm"] == 0.45


@pytest.mark.asyncio
async def test_ac1_unit_embedding_optionnel_si_pas_icp_profile() -> None:
    """AC1 : campagne sans icp_profile_id (NULL) → icp_embedding=None, pas d'erreur.

    Un ICP non encore embarqué (#12 non exécuté) ne doit pas faire planter le
    node de chargement des critères — les critères sont indépendants de
    l'embedding.
    """
    from graph.workflow import init_campagne

    campagne = _fake_campagne_row(icp_profile_id=None)
    critere = _fake_critere_row()
    campagne_row = {**campagne, "qdrant_point_id": None}

    pool, _ = _make_pool_mock(campagne_row, critere, None)

    with patch("graph.workflow.db.get_pg_pool", new_callable=AsyncMock, return_value=pool), \
         patch("graph.workflow.db.get_icp_embedding", new_callable=AsyncMock) as mock_get_icp:
        etat = await init_campagne({"campagne_id": CAMPAGNE_ID})

    assert etat["icp_embedding"] is None
    mock_get_icp.assert_not_awaited()   # court-circuit : pas de point_id → pas d'appel Qdrant
    assert isinstance(etat["criteres"], CriteresCiblage)


# --- AC1 : bout-en-bout avec vraie BDD (integration) -----------------------

@pytest_asyncio.fixture
async def _clean_db_pool() -> None:
    """Ferme le pool PG singleton (utils.db) après chaque test d'intégration.

    `db.get_pg_pool()` crée un pool global (min_size=1) réutilisé d'un test à
    l'autre. Sans nettoyage, la connexion remise au pool par le test N est
    réutilisée par le test N+1 alors qu'asyncpg est en train de la `reset` →
    InterfaceError « another operation is in progress ». On ferme donc le pool
    après chaque test d'intégration pour repartir d'un état propre.
    """
    yield
    await db.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ac1_integration_charge_campagne_de_test(_clean_db_pool) -> None:
    """AC1 (intégration) : charge la campagne de la fixture SQL réelle.

    Prérequis : la stack Docker est up (postgres sur localhost:5432) ET la
    fixture `tests/fixtures/init_campagne_test_data.sql` a été chargée :
        docker exec -i prospection_b2b_postgres psql -U scraper -d \\
            prospection_b2b < tests/fixtures/init_campagne_test_data.sql
    """
    from graph.workflow import init_campagne

    etat = await init_campagne({"campagne_id": CAMPAGNE_ID})

    assert etat["campagne_id"] == CAMPAGNE_ID
    assert etat["client_id"] == CLIENT_ID
    crit: CriteresCiblage = etat["criteres"]
    assert crit.id == uuid.UUID(CRITERE_ID)
    assert crit.codes_naf == ["6201Z", "6202Z"]
    assert crit.departements == ["75", "92"]
    assert crit.effectif_min == 3 and crit.effectif_max == 50
    assert crit.anciennete_min_ans == 2
    assert crit.mots_cles_positifs == ["qualite", "service"]
    assert crit.mots_cles_negatifs == ["exclusion1", "exclusion2"]
    assert etat["config_scoring"]["poids_regles"] == 0.35


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ac2_integration_campagne_inexistante_leve(_clean_db_pool) -> None:
    """AC2 (intégration) : UUID aléatoire → CampagneIntrouvableError."""
    from graph.workflow import init_campagne, CampagneIntrouvableError

    inconnu = str(uuid.uuid4())
    with pytest.raises(CampagneIntrouvableError):
        await init_campagne({"campagne_id": inconnu})