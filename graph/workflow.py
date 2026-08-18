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

import logging
import uuid

from agents.enrichissement_agent import enrichissement_node
from agents.nettoyage_agent import nettoyage_node
from agents.scoring_agent import scoring_node
from agents.sirene_agent import sirene_node
from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from utils import db

logger = logging.getLogger(__name__)


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
    # Mode ad hoc (#29) : si l'état est déjà peuplé (criteres synthétisés depuis les
    # flags CLI --depts/--naf, sans campagne en base), init_campagne est un no-op —
    # on ne relit pas la BDD. Idempotent aussi si le node est ré-exécuté.
    if etat.get("criteres") is not None:
        return etat

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
                osm_tags,
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
            osm_tags=list(critere_row["osm_tags"] or []),
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


# --- Assemblage du pipeline (issue #28) ------------------------------------

# Les 6 nodes dans l'ordre. Chaîne manuelle (pas de dépendance LangGraph — cf. #28
# et la note de prep) : chaque node reste un `async (state) -> state`, contrat
# compatible avec un futur `StateGraph` si on décide d'ajouter LangGraph.
# `prerequis=True` : un échec rend la suite vide de sens (pas de contexte / pas de
# prospects) → on stoppe proprement. Sinon on logge et on continue (pipeline partiel).
_PIPELINE: tuple[tuple[str, object, bool], ...] = (
    ("init_campagne", init_campagne, True),
    ("fetch_sirene", sirene_node, True),
    ("enrichir", enrichissement_node, False),
    ("nettoyer", nettoyage_node, False),
    ("scorer", scoring_node, False),
)


def build_graph() -> tuple[tuple[str, object, bool], ...]:
    """Retourne la description ordonnée du pipeline (nodes async `(state) -> state`).

    Chaîne manuelle, sans dépendance graphe. Point d'extension unique si l'équipe
    ajoute LangGraph plus tard : mapper `_PIPELINE` sur un `StateGraph`. `run`
    exécute cette description."""
    return _PIPELINE


async def run(state: EtatAgent) -> EtatAgent:
    """Exécute le pipeline complet pour une campagne, nodes en séquence (#28).

    Gestion d'erreurs par node : chaque échec est loggé et poussé dans
    `state["erreurs"]`. Un node **prérequis** en échec (`init_campagne`,
    `fetch_sirene`) arrête le pipeline — inutile de continuer sans contexte ni
    prospects. Les autres nodes n'arrêtent pas la campagne (résultat partiel > rien).
    La panne Claude est absorbée dans `scoring_node` (repli règles), pas ici.

    `state` doit contenir `campagne_id`. Retourne l'état final (avec `qualifies`,
    `erreurs`). La fermeture du pool PG / client Qdrant est du ressort de
    l'orchestrateur appelant (`main.py`, #29), pas de `run`."""
    state.setdefault("erreurs", [])
    state.setdefault("collectes", 0)
    state.setdefault("qualifies", 0)
    for nom, node, prerequis in _PIPELINE:
        try:
            state = await node(state)  # type: ignore[operator]
        except Exception as exc:
            logger.exception("Node '%s' en échec : %s", nom, exc)
            state["erreurs"].append(f"{nom}:{exc}")
            if prerequis:
                logger.error("Node prérequis '%s' échoué — arrêt du pipeline.", nom)
                break
    return state