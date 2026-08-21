"""Test d'intégration (#41) — purge RGPD contre un vrai PostgreSQL.

Vérifie les 4 durées de rétention (docs/LEGAL.md), le journal d'audit
`purge_rgpd_log`, l'exclusion de `oppositions_rgpd` (jamais purgée), et le `--dry-run`
(lecture seule). Seed daté finement (INSERT avec `created_at` explicite) + teardown.

    pytest tests/test_purge_rgpd.py -m integration -v
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from scripts.purge_rgpd import purger
from utils import db

pytestmark = pytest.mark.integration

SIRET_OPPOSE = "11111111111111"


@pytest_asyncio.fixture
async def donnees_datees():
    """Seed client + campagne + prospects/appels/opposition/log à des âges contrôlés.
    Retourne les ids utiles. Teardown : DELETE client (CASCADE) + opposition + logs du test."""
    client_id, critere_id, camp_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        depart = await c.fetchval("SELECT now();")  # borne pour nettoyer les logs du run
        await c.execute(
            "INSERT INTO clients (id, nom_entreprise, secteur, produit_vendu, "
            "zone_intervention, statut) VALUES ($1,'Purge SARL','conseil','x','France','essai');",
            client_id,
        )
        await c.execute(
            "INSERT INTO criteres_ciblage (id, client_id, nom, codes_naf, departements) "
            "VALUES ($1,$2,'crit purge',ARRAY['6201Z'],ARRAY['75']);",
            critere_id, client_id,
        )
        await c.execute(
            "INSERT INTO campagnes (id, client_id, critere_id, nom, statut) "
            "VALUES ($1,$2,$3,'camp purge','brouillon');",
            camp_id, client_id, critere_id,
        )

        async def _prospect(nom: str, statut: str, age: str, siret: str | None = None) -> uuid.UUID:
            return await c.fetchval(
                "INSERT INTO prospects (campagne_id, nom_entreprise, siret, statut, created_at) "
                f"VALUES ($1,$2,$3,$4, now() - INTERVAL '{age}') RETURNING id;",
                camp_id, nom, siret, statut,
            )

        ids = {
            "inv_vieux": await _prospect("Invalide vieux", "invalide", "7 months", SIRET_OPPOSE),
            "inv_recent": await _prospect("Invalide recent", "invalide", "5 months"),
            "qual_vieux": await _prospect("Qualifie vieux", "qualifie", "4 years"),
            "qual_recent": await _prospect("Qualifie recent", "qualifie", "2 years"),
            "rdv_vieux": await _prospect("Converti vieux", "rdv", "4 years"),
        }
        # Appels rattachés au survivant (qual_recent) : un vieux (>1 an) purgé, un récent gardé.
        await c.execute(
            "INSERT INTO appels (prospect_id, date_appel) VALUES ($1, now() - INTERVAL '2 years');",
            ids["qual_recent"],
        )
        await c.execute(
            "INSERT INTO appels (prospect_id, date_appel) VALUES ($1, now() - INTERVAL '1 month');",
            ids["qual_recent"],
        )
        # Opposition (siret identique à inv_vieux) — doit survivre à la purge du prospect.
        await c.execute(
            "INSERT INTO oppositions_rgpd (siret, motif) VALUES ($1, 'test') "
            "ON CONFLICT (siret) DO NOTHING;",
            SIRET_OPPOSE,
        )
        # Vieux log système (> 3 mois) → purgé.
        await c.execute(
            "INSERT INTO purge_rgpd_log (table_cible, nb_lignes, motif, purge_le) "
            "VALUES ('prospects', 1, 'vieux log test', now() - INTERVAL '4 months');",
        )
    try:
        yield {"ids": ids, "camp_id": camp_id, "depart": depart}
    finally:
        async with pool.acquire() as c:
            await c.execute("DELETE FROM clients WHERE id=$1;", client_id)  # CASCADE
            await c.execute("DELETE FROM oppositions_rgpd WHERE siret=$1;", SIRET_OPPOSE)
            await c.execute("DELETE FROM purge_rgpd_log WHERE purge_le >= $1;", depart)
        await db.close()


async def _existe(prospect_id: uuid.UUID) -> bool:
    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        return await c.fetchval("SELECT EXISTS(SELECT 1 FROM prospects WHERE id=$1);", prospect_id)


@pytest.mark.asyncio
async def test_dry_run_ne_supprime_rien(donnees_datees) -> None:
    """--dry-run compte les cibles mais ne supprime rien (lecture seule)."""
    ids = donnees_datees["ids"]
    res = dict(((t, m), n) for t, m, n in await purger(dry_run=True))
    # Au moins les 2 prospects vieux + 1 appel vieux + 1 vieux log sont comptés.
    assert res[("prospects", "prospects invalides > 6 mois")] >= 1
    assert res[("prospects", "prospects qualifies non convertis > 3 ans")] >= 1
    assert res[("appels", "historique appels > 1 an")] >= 1
    # Rien n'a bougé.
    assert await _existe(ids["inv_vieux"]) and await _existe(ids["qual_vieux"])


@pytest.mark.asyncio
async def test_purge_applique_les_4_regles(donnees_datees) -> None:
    ids = donnees_datees["ids"]
    depart = donnees_datees["depart"]

    await purger(dry_run=False)

    # Invalides > 6 mois supprimés ; < 6 mois gardés.
    assert not await _existe(ids["inv_vieux"])
    assert await _existe(ids["inv_recent"])
    # Qualifiés non convertis > 3 ans supprimés ; < 3 ans gardés ; convertis (rdv) gardés.
    assert not await _existe(ids["qual_vieux"])
    assert await _existe(ids["qual_recent"])
    assert await _existe(ids["rdv_vieux"]), "un prospect converti (rdv) ne doit PAS être purgé"

    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        # Appels : le vieux (>1 an) est parti, le récent reste.
        appels_restants = await c.fetchval(
            "SELECT count(*) FROM appels WHERE prospect_id=$1;", ids["qual_recent"]
        )
        assert appels_restants == 1
        # Vieux log système purgé.
        vieux_log = await c.fetchval(
            "SELECT count(*) FROM purge_rgpd_log WHERE motif='vieux log test';"
        )
        assert vieux_log == 0
        # oppositions_rgpd INTOUCHÉE (le SIRET opposé reste opposable même si son prospect a été purgé).
        assert await c.fetchval("SELECT EXISTS(SELECT 1 FROM oppositions_rgpd WHERE siret=$1);", SIRET_OPPOSE)
        # Journal d'audit écrit pour les suppressions de ce run.
        logs = await c.fetch(
            "SELECT table_cible, motif, nb_lignes FROM purge_rgpd_log WHERE purge_le >= $1;", depart
        )
        motifs = {r["motif"]: r["nb_lignes"] for r in logs}
        assert motifs.get("prospects invalides > 6 mois", 0) >= 1
        assert motifs.get("historique appels > 1 an", 0) >= 1
        assert all(r["nb_lignes"] > 0 for r in logs), "aucune ligne de log à 0 (pas de bruit)"


@pytest.mark.asyncio
async def test_run_idempotent(donnees_datees) -> None:
    """Un 2e run immédiat ne trouve plus rien à purger (0 nouvelle ligne de log)."""
    depart = donnees_datees["depart"]
    await purger(dry_run=False)
    res2 = await purger(dry_run=False)
    assert all(n == 0 for _, _, n in res2), "le 2e run ne doit plus rien supprimer"
    pool = await db.get_pg_pool()
    async with pool.acquire() as c:
        # Aucune ligne de log ajoutée au 2e run (on ne journalise pas les purges vides)…
        # on vérifie juste qu'aucune n'a nb_lignes = 0.
        zero = await c.fetchval(
            "SELECT count(*) FROM purge_rgpd_log WHERE purge_le >= $1 AND nb_lignes = 0;", depart
        )
        assert zero == 0
