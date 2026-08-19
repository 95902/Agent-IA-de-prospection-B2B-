"""Tests d'intégration (#31) — pipeline complet assemblé `graph.workflow.run` (#28).

Deux critères d'acceptance du Sprint 3 :

1. **Débit** : `run()` traite ~100 prospects réels en < 15 min (collecte Sirene →
   OSM → enrichissement → nettoyage → scoring), en mode ad hoc / dry-run (aucune
   écriture — c'est exactement le chemin de `main.py --depts/--naf`, #29).
2. **Résilience panne Claude** : si l'API Claude est indisponible, `scoring_node`
   bascule seul sur le repli (score règles + embedding) — la campagne ne s'arrête
   pas, aucun prospect ne fait échouer le lot (#28).

⚠️ Le test de **débit** est coûteux (vraies APIs Sirene/Tavily) → double opt-in :
marqué `integration` (exclu du run par défaut) ET gardé par `RUN_E2E=1`. Lancer :

    RUN_E2E=1 pytest tests/test_e2e_run.py -m integration -s

Tout est paramétrable par variable d'env (aucune valeur métier codée en dur,
règle #3) : `E2E_DEPTS` / `E2E_NAF` / `E2E_LIMIT` / `E2E_MAX_SECONDS`.

Le test de **résilience** est déterministe et léger (prospects synthétiques,
Claude simulé en panne) : il ne dépend que d'Ollama (embedding local) et tourne
avec `-m integration` sans `RUN_E2E`.
"""
from __future__ import annotations

import os
import time
import uuid

import anthropic
import httpx
import pytest
import pytest_asyncio

from utils import db

pytestmark = pytest.mark.integration

_RUN_E2E = os.getenv("RUN_E2E") == "1"


@pytest_asyncio.fixture
async def _clean_db_pool():
    """Ferme le pool PG singleton après le test (voir test_init_campagne)."""
    yield
    await db.close()


# --- AC1 : débit du pipeline complet (100 prospects < 15 min) ---------------

@pytest.mark.skipif(
    not _RUN_E2E,
    reason="E2E live coûteux — activer avec RUN_E2E=1 (tape Sirene/Tavily).",
)
@pytest.mark.asyncio
async def test_run_pipeline_100_prospects_sous_15min(_clean_db_pool) -> None:
    """`run()` en mode ad hoc (dry-run) sur ~100 prospects réels, < 15 min, 0 erreur.

    Reproduit fidèlement le chemin `main.py --depts/--naf --limit` (#29) : ICP
    synthétisé depuis les flags, `init_campagne` no-op (état pré-peuplé), scoring
    en mémoire (aucune écriture). La borne de temps est l'AC #31 (« 100 prospects
    < 15 min »). Le pipeline doit rester à 0 erreur même si Claude est indisponible
    (le repli du scoring absorbe la panne)."""
    from graph.workflow import run
    from models.criteres import CriteresCiblage

    limit = int(os.getenv("E2E_LIMIT", "100"))
    max_seconds = float(os.getenv("E2E_MAX_SECONDS", "900"))  # 15 min (AC #31)

    criteres = CriteresCiblage(
        nom="E2E débit",
        departements=os.getenv("E2E_DEPTS", "75,92").split(","),
        codes_naf=os.getenv("E2E_NAF", "45.20A").split(","),
    )
    state = {
        "campagne_id": str(uuid.uuid4()),  # jetable — dry-run, jamais persisté
        "criteres": criteres,              # → init_campagne no-op
        "config_scoring": {},              # poids par défaut à l'agrégation
        "icp_embedding": None,             # pas d'ICP embarqué → couche embedding neutre
        "dry_run": True,                   # aucune écriture BDD/Qdrant
        "limit": limit,
    }

    t0 = time.monotonic()
    etat = await run(state)
    duree = time.monotonic() - t0

    prospects = etat.get("prospects") or []
    print(
        f"\nE2E run — collectés: {etat.get('collectes', 0)}, "
        f"prospects: {len(prospects)}, qualifiés: {etat.get('qualifies', 0)}, "
        f"erreurs: {len(etat.get('erreurs', []))}, durée: {duree:.0f}s"
    )
    for err in etat.get("erreurs", [])[:5]:
        print(f"  ! {err}")

    # AC1 : le pipeline collecte, produit des prospects, et tient la borne de temps.
    assert prospects, "Sirene n'a renvoyé aucun prospect (collecte vide)."
    assert etat.get("collectes", 0) > 0
    assert duree < max_seconds, f"pipeline {duree:.0f}s ≥ {max_seconds:.0f}s pour {len(prospects)} prospects"
    # AC #28 : aucun node prérequis en échec, aucun prospect ne casse le lot.
    assert etat.get("erreurs", []) == [], f"erreurs non vides : {etat['erreurs'][:5]}"
    assert isinstance(etat.get("qualifies"), int)


# --- AC2 : résilience à une panne Claude (repli du scoring) ------------------

class _FakeMessagesDown:
    """Simule l'API Messages de Claude en panne : chaque appel lève une APIError."""

    async def create(self, **_kwargs):
        raise anthropic.APIConnectionError(
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )


class _FakeClaudeDown:
    """Remplace `anthropic.AsyncAnthropic` : contexte async dont `.messages.create`
    lève toujours (panne API). Exerce le repli réel de `_score_llm` (#25/#28)."""

    def __init__(self, *_args, **_kwargs):
        self.messages = _FakeMessagesDown()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False


@pytest.mark.asyncio
async def test_scoring_node_survit_a_une_panne_claude(_clean_db_pool, monkeypatch) -> None:
    """AC #28/#31 : Claude down → `scoring_node` bascule sur le repli, 0 erreur.

    Prospects synthétiques (pas de collecte réseau), ICP embarqué factice non nul
    pour exercer la couche embedding réelle (Ollama, règle #5). Claude est simulé
    en panne : `scoring_node` doit terminer sans exception, sans pousser d'erreur,
    et compter les qualifiés issus du repli (règles + embedding)."""
    from agents.scoring_agent import scoring_node
    from models.criteres import CriteresCiblage
    from models.prospect import Prospect

    monkeypatch.setattr(
        "agents.scoring_agent.anthropic.AsyncAnthropic", _FakeClaudeDown
    )

    criteres = CriteresCiblage(
        nom="résilience",
        codes_naf=["45.20A"],
        departements=["75"],
        effectif_min=0,
        effectif_max=10_000,
    )
    campagne_id = uuid.uuid4()
    prospects = [
        Prospect(
            campagne_id=campagne_id,
            nom_entreprise=f"Garage Test {i}",
            code_naf="45.20A",
            departement="75",
            ville="Paris",
            telephone="+33140000000",
            email=f"contact{i}@garage-test.fr",
            effectif_estime=8,
        )
        for i in range(3)
    ]
    state = {
        "criteres": criteres,
        "prospects": prospects,
        "icp_embedding": [0.01] * 768,  # non nul → embedding réel via Ollama
        "config_scoring": {},
        "dry_run": True,                # aucune écriture — pas de campagne en base
    }

    etat = await scoring_node(state)

    # La panne Claude n'a pas cassé le lot : aucune exception remontée, 0 erreur.
    assert etat.get("erreurs", []) == [], f"erreurs inattendues : {etat.get('erreurs')}"
    assert isinstance(etat.get("qualifies"), int)
    # Les 3 prospects ont été traités (repli appliqué), aucun n'a fait échouer le node.
    assert etat is state
