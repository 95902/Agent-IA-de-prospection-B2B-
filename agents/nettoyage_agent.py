"""Node de nettoyage (#19) — dédup + exclusions ICP + garde légale + qualité.

Entre l'enrichissement (#18) et le scoring (#24). Prépare et filtre les prospects
en appliquant, dans un ordre choisi pour **dépenser le moins possible** :

    1. Dédup SIRET          (local, gratuit)  -> marque `doublon = True`
    2. Exclusions client    (local, gratuit)  -> `raw_data['nettoyage']`
    3. Effectif hors cible  (local, gratuit)  -> `raw_data['nettoyage']`
    4. Opposition commerciale (Pappers, PAYANT, budgété)  -> seulement sur les
       survivants des filtres locaux : on ne brûle pas un crédit sur un prospect
       déjà écarté. C'est aussi la **garde légale** (art. R123-232) — voir #74.
    5. Domiciliation        (Sirene, gratuit mais throttlé)  -> qualité (#68)

On **marque, on ne supprime pas** (cohérent avec #68/#74) : la décision finale
d'exclure appartient au scoring (#24) et à l'ICP du client. Seul `doublon` est un
booléen de première classe (colonne `prospects`) ; le reste vit dans
`raw_data['nettoyage']` pour la traçabilité.

⚠️ **Ordre légal.** L'opposition commerciale doit être connue **avant** tout envoi
vers un enrichisseur tiers payant (Dropcontact, #21). Deux garanties, pas une :
ce node marque l'opposition, ET l'enrichisseur Dropcontact ne doit s'exécuter que
sur `peut_etre_contacte(prospect)`. Si l'assemblage du graphe (#28) place le
nettoyage après un enrichisseur tiers, ce dernier reste donc bloqué par sa propre
garde — on ne dépend pas de l'ordre des nodes pour la conformité.

Règles : aucune liste de marques codée en dur — les exclusions viennent de
`criteres_ciblage.mots_cles_negatifs` du client (règle #4) ; matching par **mot
entier**, jamais par sous-chaîne (« groupe » n'exclut pas « regroupement »).
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime, timezone

from config.settings import get_settings
from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from models.prospect import Prospect
from utils.domiciliation import marquer_domiciliation
from utils.opposition_commerciale import marquer_opposition, peut_etre_contacte

logger = logging.getLogger(__name__)


# --- Normalisation / matching par mot entier --------------------------------
def _normalize(texte: str) -> str:
    """Minuscule, sans accents, ponctuation -> espaces, espaces compactés.

    Permet un matching par mot entier robuste : « Éts. Durand-Groupe » devient
    « ets durand groupe », où chaque mot est isolable par ses bornes d'espace.
    """
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    sans_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", sans_accent)).strip()


def _matche_exclusion(prospect: Prospect, negatifs: list[str]) -> str | None:
    """Retourne le 1er mot-clé négatif présent en **mot entier** dans le nom de
    l'entreprise, ou None. Le mot-clé peut être multi-mots (« groupe casino ») :
    on exige alors la séquence exacte, toujours bornée par des espaces.
    """
    nom = f" {_normalize(prospect.nom_entreprise or '')} "
    for brut in negatifs:
        motif = _normalize(brut)
        if motif and f" {motif} " in nom:
            return brut
    return None


def _hors_cible_effectif(prospect: Prospect, criteres: CriteresCiblage) -> bool:
    """True si l'effectif estimé est **connu** et hors [effectif_min, effectif_max].

    Effectif inconnu (`None`) -> on ne conclut pas : ne pas écarter sur une donnée
    absente (on préfère laisser le scoring décider plutôt que perdre un prospect).
    """
    n = prospect.effectif_estime
    if n is None:
        return False
    return n < criteres.effectif_min or n > criteres.effectif_max


# --- Dédup ------------------------------------------------------------------
def _dedupliquer(prospects: list[Prospect]) -> int:
    """Marque `doublon = True` sur les occurrences suivantes d'un même SIRET.

    Garde la première vue, ne supprime rien. Les prospects sans SIRET ne sont
    pas dédupliqués (aucune clé fiable — on ne devine pas).
    """
    vus: set[str] = set()
    marques = 0
    for p in prospects:
        if not p.siret:
            continue
        if p.siret in vus:
            if not p.doublon:
                p.doublon = True
                marques += 1
        else:
            vus.add(p.siret)
    return marques


# --- Marquage local (exclusions + effectif) ---------------------------------
def _marquer_local(prospects: list[Prospect], criteres: CriteresCiblage) -> None:
    for p in prospects:
        if p.doublon:
            continue
        exclusion = _matche_exclusion(p, criteres.mots_cles_negatifs)
        hors_cible = _hors_cible_effectif(p, criteres)
        if exclusion is None and not hors_cible:
            continue
        p.raw_data = {
            **(p.raw_data or {}),
            "nettoyage": {
                "exclusion": exclusion,               # mot-clé négatif matché
                "effectif_hors_cible": hors_cible,
                "at": datetime.now(timezone.utc).isoformat(),
            },
        }


def _est_ecarte(prospect: Prospect) -> bool:
    """Écarté par un filtre LOCAL (dédup / exclusion / effectif) — sert à ne pas
    dépenser de crédit d'opposition sur un prospect déjà rejeté. N'inclut PAS
    l'opposition elle-même (qui n'est pas encore connue à ce stade)."""
    if prospect.doublon:
        return True
    net = (prospect.raw_data or {}).get("nettoyage", {})
    return bool(net.get("exclusion") or net.get("effectif_hors_cible"))


# --- Node -------------------------------------------------------------------
async def nettoyage_node(
    state: EtatAgent, budget_opposition: int | None = None
) -> EtatAgent:
    """Nettoie `state['prospects']` : dédup, exclusions ICP, garde d'opposition
    commerciale (budgétée), marquage domiciliation. Mute et renvoie le state.

    `budget_opposition` plafonne les crédits Pappers ; par défaut, prend
    `settings.opposition_budget_credits`.
    """
    prospects: list[Prospect] = state.get("prospects", [])
    if not prospects:
        return state
    settings = get_settings()
    criteres = state.get("criteres")

    # 1. Dédup SIRET (gratuit)
    doublons = _dedupliquer(prospects)

    # 2-3. Exclusions client + effectif hors cible (gratuit). Sans ICP en state,
    # on ne peut pas appliquer les exclusions — on log et on continue.
    if criteres is not None:
        _marquer_local(prospects, criteres)
    else:
        logger.warning("nettoyage : pas de critères ICP dans le state — "
                       "exclusions et filtre effectif ignorés")

    # 4-5. On ne dépense (opposition) et ne throttle (domiciliation) que sur les
    # survivants des filtres locaux.
    candidats = [p for p in prospects if not _est_ecarte(p)]

    # 4. Opposition commerciale — garde légale (art. R123-232), fermée par défaut.
    budget = (
        budget_opposition if budget_opposition is not None
        else settings.opposition_budget_credits
    )
    await marquer_opposition(candidats, budget_credits=budget, settings=settings)

    # 5. Domiciliation — qualité (#68).
    await marquer_domiciliation(candidats, settings=settings)

    contactables = sum(1 for p in candidats if peut_etre_contacte(p))
    logger.info(
        "nettoyage : %d prospects, %d doublon(s), %d écarté(s) localement, "
        "%d contactable(s) vérifié(s)",
        len(prospects), doublons, len(prospects) - len(candidats), contactables,
    )
    state["prospects"] = prospects
    return state
