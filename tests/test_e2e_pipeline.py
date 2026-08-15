"""Test E2E collecte + enrichissement + nettoyage (#22) — vraies APIs.

Valide bout-en-bout la moitié « avant scoring » du pipeline en chaînant les nodes
existants (le graphe #28 n'est pas encore assemblé) :

    sirene_node (#15)  →  OSM pré-passe (#69)  →  enrichissement_node (#18)
      →  nettoyage_node (#19 : dédup + exclusions + opposition + domiciliation)
      →  dropcontact.enrichir_emails (#21, fallback payant borné)

⚠️ **Dépend de #19, #21, #23, #69** (les fonctions appelées). Les imports sont
faits DANS le test pour que ce fichier se **collecte** même sur une `main` où ces
PR ne sont pas encore fusionnées (le test étant skippé par défaut, ils ne
s'exécutent pas). L'E2E ne tourne réellement qu'une fois ces PR sur `main`.

⚠️ **Coûteux, opt-in double.** Marqué `integration` (exclu du run par défaut) ET
gardé par `RUN_E2E=1` : `pytest -m integration` seul ne le lance PAS. L'opposition
consomme 1 crédit Pappers par SIREN (solde rare) → volume borné par `E2E_LIMIT`
(défaut 20, pas 100) pour ne pas l'épuiser.

Lancer, quand on décide sciemment de dépenser :

    RUN_E2E=1 E2E_LIMIT=20 pytest tests/test_e2e_pipeline.py -m integration -s

Tout est surchargeable par variable d'env (ICP, seuils) — aucune valeur métier
codée en dur (règle #3).
"""
from __future__ import annotations

import os
import time
import uuid

import pytest

pytestmark = pytest.mark.integration

_RUN = os.getenv("RUN_E2E") == "1"


@pytest.mark.skipif(
    not _RUN,
    reason="E2E live — activer avec RUN_E2E=1 (consomme des crédits Pappers/Dropcontact).",
)
@pytest.mark.asyncio
async def test_pipeline_collecte_enrichissement_nettoyage():
    # Imports tardifs : dépendances #19/#21/#23/#69 — voir docstring.
    from agents.enrichissement_agent import enrichissement_node
    from agents.nettoyage_agent import nettoyage_node
    from agents.sirene_agent import sirene_node
    from config.settings import get_settings
    from models.criteres import CriteresCiblage
    from utils import dropcontact
    from utils.metrics import couverture_globale, depuis_dropcontact, depuis_osm, rapport
    from utils.opposition_commerciale import peut_etre_contacte
    from utils.osm import enrichir_par_osm

    settings = get_settings()
    assert settings.insee_api_key, "INSEE_API_KEY requise pour l'E2E."

    limit = int(os.getenv("E2E_LIMIT", "20"))
    criteres = CriteresCiblage(
        nom="E2E pilote",
        departements=os.getenv("E2E_DEPTS", "75").split(","),
        codes_naf=os.getenv("E2E_NAF", "5510Z").split(","),      # hôtels par défaut
        osm_tags=os.getenv("E2E_OSM", "tourism=hotel").split(","),
        mots_cles_negatifs=os.getenv("E2E_EXCLUS", "groupe").split(","),
        effectif_min=0, effectif_max=10_000,
    )
    state = {"campagne_id": uuid.uuid4(), "criteres": criteres, "prospects": []}

    t0 = time.monotonic()
    await sirene_node(state, limit=limit)
    assert state["prospects"], "Sirene n'a renvoyé aucun prospect."

    osm_stats = await enrichir_par_osm(state["prospects"], criteres.osm_tags)
    await enrichissement_node(state)
    await nettoyage_node(state, budget_opposition=limit)
    dc_stats = await dropcontact.enrichir_emails(
        state["prospects"], budget=int(os.getenv("E2E_DROPCONTACT_BUDGET", "5"))
    )
    duree = time.monotonic() - t0

    prospects = state["prospects"]
    couverture = couverture_globale(prospects)
    rapport_txt = rapport(couverture, [depuis_osm(osm_stats), depuis_dropcontact(dc_stats)])
    print("\n" + rapport_txt + f"\n  durée : {duree:.0f}s")

    # --- Invariants durs (toujours vrais, quelle que soit la donnée) ---------
    sirets_actifs = [p.siret for p in prospects if p.siret and not p.doublon]
    assert len(sirets_actifs) == len(set(sirets_actifs)), "doublon SIRET non marqué"

    for p in prospects:
        # Un prospect contactable (opposition vérifiée non-opposée) ne peut pas
        # être un prospect exclu par l'ICP : le nettoyage ne l'aurait pas envoyé
        # à la vérification d'opposition.
        if peut_etre_contacte(p):
            exclusion = (p.raw_data or {}).get("nettoyage", {}).get("exclusion")
            assert exclusion is None, f"prospect exclu ({exclusion}) marqué contactable"

    assert duree < 600, f"pipeline > 10 min ({duree:.0f}s) pour {len(prospects)} prospects"

    # --- Cibles PRD (assertions tunables via env selon l'ICP choisi) ---------
    assert couverture["telephone_pct"] >= float(os.getenv("E2E_MIN_TEL", "40")), rapport_txt
    assert couverture["email_pct"] >= float(os.getenv("E2E_MIN_EMAIL", "20")), rapport_txt
