"""Graphe LangChain — nodes du pipeline de prospection.

Issue #11 — STUB pour `build_graph`/`run` (assemblage réel porté par #28).
Issue #16 — implémentation du premier node `init_campagne` : charge les
critères de ciblage d'une campagne depuis la BDD et peuple `EtatAgent`.

Règle #3 (CLAUDE.md) : AUCUNE valeur métier ICP codée en dur ici — tout
vient de la base (`criteres_ciblage`, `icp_profiles`). Ce node ne fait que
lire et peupler.

Règle #8 : async partout (asyncpg via `utils.db`).
"""
from __future__ import annotations

import uuid

from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from utils import db


# --- Exceptions (AC2 : erreurs explicites, fail fast) ----------------------

class CampagneIntrouvableError(Exception):
    """Levée quand `campagne_id` est absent de l'état ou introuvable en base."""


class CriteresIntrouvablesError(Exception):
    """Levée quand la campagne référence un `critere_id` absent de `criteres_ciblage`."""


# --- Node init_campagne (issue #16) ----------------------------------------

async def init_campagne(etat: EtatAgent) -> EtatAgent:
    """Charge les critères de ciblage d'une campagne depuis la BDD.

    Premier node du graphe LangChain (#28) : lit `campagnes.critere_id` puis
    charge la ligne `criteres_ciblage` correspondante (codes NAF, départements,
    effectif min/max, ancienneté min, mots-clés +/-) et le `qdrant_point_id` de
    l'ICP associé (`icp_profiles`). Peuple `EtatAgent` avec un objet
    `CriteresCiblage` complet, utilisé par tous les nodes suivants (collecte
    Sirene #15, nettoyage #19, scoring #24-26).

    AC1 : retourne un `EtatAgent` avec tous les critères correctement chargés.
    AC2 : lève `CampagneIntrouvableError` / `CriteresIntrouvablesError` si la
    campagne ou ses critères n'existent pas — fail fast, jamais de valeurs par
    défaut silencieuses (règle #3).

    Args:
        etat: état partagé du graphe. Doit contenir `campagne_id` (str UUID).

    Returns:
        `etat` enrichi avec `client_id`, `criteres` (CriteresCiblage),
        `icp_embedding` (**vecteur** `list[float]` de l'ICP, ou None), `config_scoring`.
    """
    campagne_id_raw = etat.get("campagne_id")
    if not campagne_id_raw:
        raise CampagneIntrouvableError(
            "init_campagne : `campagne_id` manquant dans l'état initial. "
            "Le graphe doit être lancé avec un campagne_id valide (UUID)."
        )

    try:
        campagne_uuid = uuid.UUID(str(campagne_id_raw))
    except (ValueError, TypeError) as exc:
        raise CampagneIntrouvableError(
            f"init_campagne : `campagne_id`='{campagne_id_raw}' n'est pas un UUID valide."
        ) from exc

    pool = await db.get_pg_pool()
    async with pool.acquire() as conn:
        # 1. Lecture de la campagne + qdrant_point_id de l'ICP associé
        #    (LEFT JOIN : une campagne peut ne pas avoir d'icp_profile_id).
        campagne_row = await conn.fetchrow(
            """
            SELECT
                c.id,
                c.client_id,
                c.critere_id,
                c.icp_profile_id,
                c.nom,
                c.config_scoring,
                icp.qdrant_point_id
            FROM campagnes c
            LEFT JOIN icp_profiles icp ON icp.id = c.icp_profile_id
            WHERE c.id = $1;
            """,
            campagne_uuid,
        )
        if campagne_row is None:
            raise CampagneIntrouvableError(
                f"init_campagne : campagne {campagne_uuid} introuvable en base."
            )

        critere_id = campagne_row["critere_id"]
        if critere_id is None:
            raise CriteresIntrouvablesError(
                f"init_campagne : la campagne {campagne_uuid} n'a pas de "
                f"`critere_id` renseigné (référence cassée)."
            )

        # 2. Lecture des critères de ciblage (ICP configurable par client).
        critere_row = await conn.fetchrow(
            """
            SELECT
                id, client_id, nom, description_icp,
                codes_naf, departements,
                effectif_min, effectif_max, anciennete_min_ans,
                exiger_site_web, exiger_email,
                mots_cles_positifs, mots_cles_negatifs,
                actif
            FROM criteres_ciblage
            WHERE id = $1;
            """,
            critere_id,
        )
        if critere_row is None:
            raise CriteresIntrouvablesError(
                f"init_campagne : critère {critere_id} référencé par la "
                f"campagne {campagne_uuid} mais absent de `criteres_ciblage`."
            )

        # 3. Construction de l'objet CriteresCiblage (Pydantic v2, règle #7).
        critere = CriteresCiblage(
            id=critere_row["id"],
            client_id=critere_row["client_id"],
            nom=critere_row["nom"],
            description_icp=critere_row["description_icp"],
            codes_naf=list(critere_row["codes_naf"] or []),
            departements=list(critere_row["departements"] or []),
            effectif_min=critere_row["effectif_min"],
            effectif_max=critere_row["effectif_max"],
            anciennete_min_ans=critere_row["anciennete_min_ans"],
            exiger_site_web=critere_row["exiger_site_web"],
            exiger_email=critere_row["exiger_email"],
            mots_cles_positifs=list(critere_row["mots_cles_positifs"] or []),
            mots_cles_negatifs=list(critere_row["mots_cles_negatifs"] or []),
            actif=critere_row["actif"],
        )

        # 4. qdrant_point_id de l'ICP (peut être None si #12 non exécuté).
        qdrant_point_id = campagne_row["qdrant_point_id"]

    # NOTE : on n'appelle PAS `db.close()` ici. Le pool PG et le client Qdrant
    # sont des singletons (utils.db) partagés par tous les nodes du graphe (#28)
    # et par les scripts. Fermer le pool dans un node casserait les nodes
    # suivants (sirene #15, nettoyage #19, scoring #24-26). La fermeture est du
    # ressort de l'orchestrateur (run/main.py) en fin de graphe — pas d'un node.
    # `scripts/init_icp.py` ferme son pool car il est standalone (hors graphe).

    # 4b. Résolution du VECTEUR ICP (Qdrant), hors connexion PG. `EtatAgent.
    # icp_embedding` est typé `list[float]` : le scoring embeddings (#26) attend le
    # VECTEUR, pas le point_id. On le résout via `get_icp_embedding(point_id)`.
    # None si l'ICP n'est pas encore embarqué (#12 non exécuté) ou si le point est
    # absent de Qdrant → la couche embeddings reste neutre (0.0), pas de plantage.
    icp_embedding: list[float] | None = None
    if qdrant_point_id is not None:
        icp_embedding = await db.get_icp_embedding(str(qdrant_point_id))

    # 5. Peuplement de l'état partagé (consommé par les nodes suivants).
    etat["campagne_id"] = str(campagne_uuid)
    etat["client_id"] = str(campagne_row["client_id"])
    etat["criteres"] = critere
    etat["icp_embedding"] = icp_embedding
    etat["config_scoring"] = dict(campagne_row["config_scoring"] or {})
    return etat


# --- Assemblage du graphe (issue #28 — STUB) -------------------------------

def build_graph():  # type: ignore[no-untyped-def]
    """STUB — construit le StateGraph LangChain. À implémenter (#28)."""
    raise NotImplementedError("graph/workflow.build_graph non implémenté — voir #28.")


async def run(state: EtatAgent) -> EtatAgent:
    """STUB — exécute le graphe complet pour une campagne. À implémenter (#28/#29)."""
    raise NotImplementedError("graph/workflow.run non implémenté — voir #28.")