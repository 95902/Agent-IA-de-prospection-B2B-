"""Test d'intégration (#31/#32) — régression du MODE CAMPAGNE.

Garde les 3 bugs trouvés pendant l'audit #32 qu'AUCUN test n'attrapait : tous les
tests existants tournent en mode **ad hoc** (init_campagne court-circuité), or les
3 bugs vivent dans le chemin **campagne** (`--campagne-id`) :

  #1 NAF non normalisé dans `_score_regles` (INSEE dotté `55.10Z` vs ICP dot-less
     `5510Z`) → pénalité -30 à tort. Couvert unitairement (#102) ; re-vérifié ici
     via l'invariant de normalisation.
  #2 colonne `criteres_ciblage.osm_tags` absente du schéma → `init_campagne` plantait
     (`UndefinedColumnError`).
  #3 `init_icp` UPDATE `icp_profiles.updated_at` (colonne inexistante) → `qdrant_point_id`
     jamais persisté → couche embedding (#26) muette en mode campagne.

Exerce le VRAI chemin campagne (script `init_icp` réel + node `init_campagne`) contre
Postgres + Qdrant + Ollama. Données isolées (UUID aléatoires), supprimées en teardown.

    pytest tests/test_campagne_mode_regression.py -m integration -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid

import pytest
import pytest_asyncio

from agents.scoring_agent import _score_regles
from graph.workflow import init_campagne
from models.criteres import CriteresCiblage
from models.prospect import Prospect
from utils import db

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def campagne_seedee():
    """Seed client + critère (avec osm_tags + NAF dot-less) + icp_profile + campagne,
    UUID aléatoires. Teardown : DELETE client (CASCADE) + point Qdrant + close pool."""
    client_id, critere_id, icp_id, camp_id = (uuid.uuid4() for _ in range(4))
    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        await c.execute(
            "INSERT INTO clients (id, nom_entreprise, secteur, produit_vendu, "
            "zone_intervention, statut) VALUES ($1,$2,'conseil','x','France','essai');",
            client_id, "Regress SARL",
        )
        await c.execute(
            "INSERT INTO criteres_ciblage (id, client_id, nom, description_icp, codes_naf, "
            "departements, effectif_min, effectif_max, anciennete_min_ans, "
            "mots_cles_positifs, osm_tags) "
            "VALUES ($1,$2,'crit regress','Hotels independants Paris',ARRAY['5510Z'],"
            "ARRAY['75'],2,50,2,ARRAY['hotel'],ARRAY['tourism=hotel']);",
            critere_id, client_id,
        )
        await c.execute(
            "INSERT INTO icp_profiles (id, client_id, critere_id, nom, description, actif) "
            "VALUES ($1,$2,$3,'icp regress','Hotels independants Paris',TRUE);",
            icp_id, client_id, critere_id,
        )
        await c.execute(
            "INSERT INTO campagnes (id, client_id, critere_id, icp_profile_id, nom, statut) "
            "VALUES ($1,$2,$3,$4,'camp regress','brouillon');",
            camp_id, client_id, critere_id, icp_id,
        )
    try:
        yield {"client_id": client_id, "icp_id": icp_id, "camp_id": camp_id}
    finally:
        async with pool.acquire() as c:
            await c.execute("DELETE FROM clients WHERE id=$1;", client_id)  # CASCADE
        try:
            await db.get_qdrant().delete(
                collection_name=db.COLLECTION_ICP, points_selector=[str(icp_id)]
            )
        except Exception:
            pass
        await db.close()


@pytest.mark.asyncio
async def test_mode_campagne_bout_en_bout(campagne_seedee):
    ids = campagne_seedee

    # --- #3 : le SCRIPT init_icp réel doit persister qdrant_point_id -----------
    # (si l'UPDATE touchait `updated_at` inexistant, exit 2 + qdrant_point_id NULL).
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": "."}
    r = subprocess.run(
        [sys.executable, "scripts/init_icp.py", "--client-id", str(ids["client_id"])],
        capture_output=True, text=True, timeout=180, env=env,
    )
    assert r.returncode == 0, f"init_icp a échoué (régression #3) : {r.stdout}\n{r.stderr}"
    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        qpid = await c.fetchval(
            "SELECT qdrant_point_id FROM icp_profiles WHERE id=$1;", ids["icp_id"]
        )
    assert qpid is not None, "init_icp n'a pas persisté qdrant_point_id (régression #3)"

    # --- #2 + #3 : init_campagne lit osm_tags ET résout l'embedding ICP --------
    etat = await init_campagne({"campagne_id": str(ids["camp_id"])})
    crit: CriteresCiblage = etat["criteres"]
    assert list(crit.osm_tags) == ["tourism=hotel"], "osm_tags non chargé (régression #2)"
    emb = etat["icp_embedding"]
    assert emb is not None and len(emb) == 768, \
        "embedding ICP non résolu en mode campagne (régression #3)"

    # --- #1 : NAF INSEE dotté doit scorer comme le dot-less (invariant) --------
    def _p(naf: str) -> Prospect:
        return Prospect(
            campagne_id=ids["camp_id"], nom_entreprise="HOTEL TEST", code_naf=naf,
            departement="75", telephone="+33140000000", email="c@hotel-test.fr",
            effectif_estime=8,
        )
    dotte = _score_regles(_p("55.10Z"), crit)   # forme INSEE réelle
    dot_less = _score_regles(_p("5510Z"), crit)  # forme ICP stockée
    assert dotte == dot_less, f"NAF dotté pénalisé à tort ({dotte} != {dot_less}, régression #1)"
    assert dotte >= 60, f"score règles inattendu ({dotte}) — NAF matché devrait qualifier"
