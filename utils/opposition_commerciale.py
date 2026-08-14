"""Opposition à l'utilisation commerciale des données (#74) — filtre LÉGAL.

Une entreprise peut **s'opposer formellement à l'utilisation commerciale de ses
données** (art. R123-232 du code de commerce), choix exprimé au Guichet Unique lors
de l'immatriculation ou via le RNE. C'est un opt-out enregistré, pas une zone
grise : démarcher ces entreprises est précisément ce que ce droit interdit.

Mesuré sur 35 entreprises réelles (Paris, août 2026) : **17 opposées, soit 49 %**.
Et le taux grimpe à **87 % pour les SIREN récents** (immatriculés via le Guichet
Unique depuis 2023) contre 20 % pour les anciens — il augmentera donc mécaniquement
à mesure que le stock d'entreprises se renouvelle.

Source : **aucune source gratuite n'expose ce champ.** Vérifié : `statut_diffusion`
(Sirene et annuaire-entreprises) vaut `O` pour les opposées comme pour les autres —
ce n'est pas le même concept. Seul Pappers le renvoie, sur `/entreprise`, **par
défaut** : coût = l'appel de base, soit **1 crédit par entreprise**.

## Le principe : fermé par défaut

Ne pas savoir n'est pas une autorisation. Si l'API est indisponible, si la clé
manque ou si le budget de crédits est épuisé, le prospect reste **non vérifié** —
et un prospect non vérifié n'est **pas** contactable. D'où deux fonctions
distinctes, volontairement dissymétriques :

    est_oppose(p)         -> True seulement si on a VÉRIFIÉ qu'il est opposé
    peut_etre_contacte(p) -> True seulement si on a VÉRIFIÉ qu'il ne l'est pas

Utiliser `peut_etre_contacte()` comme garde avant tout envoi vers un enrichisseur
tiers ou toute file de contact. `not est_oppose()` n'est PAS équivalent : cette
expression laisserait passer les prospects non vérifiés.

Traçabilité : la valeur et la date de vérification sont conservées dans
`raw_data['opposition_commerciale']`, pour pouvoir justifier une exclusion — ou une
non-exclusion — en cas de contrôle.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Iterable

import httpx

from config.settings import Settings, get_settings
from models.prospect import Prospect

logger = logging.getLogger(__name__)

PAPPERS_BASE = "https://api.pappers.fr/v2"
MIN_INTERVAL_S = 0.3     # API payante, mais restons polis
COUT_CREDITS_PAR_SIREN = 1


class BudgetCreditsEpuise(RuntimeError):
    """Levée uniquement si `strict=True` — sinon on s'arrête proprement."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def solde_credits(client: httpx.AsyncClient, settings: Settings) -> int | None:
    """Crédits Pappers restants. None si indisponible."""
    try:
        resp = await client.get(
            f"{PAPPERS_BASE}/suivi-jetons",
            params={"api_token": settings.pappers_api_key},
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json().get("jetons_pay_as_you_go_restants")
    except Exception as exc:
        logger.warning("solde Pappers indisponible : %s", exc)
        return None


async def verifier_opposition(
    siren: str, client: httpx.AsyncClient, settings: Settings
) -> bool | None:
    """`True` = opposée, `False` = non opposée, `None` = **non vérifiable**.

    Le `None` est significatif : il ne veut pas dire « autorisée », il veut dire
    qu'on ne sait pas — et dans ce cas on ne contacte pas.
    """
    if not settings.pappers_api_key:
        logger.warning("pappers_api_key absente — opposition non vérifiable")
        return None
    try:
        resp = await client.get(
            f"{PAPPERS_BASE}/entreprise",
            params={"api_token": settings.pappers_api_key, "siren": siren},
            timeout=30.0,
        )
        resp.raise_for_status()
        valeur = resp.json().get("opposition_utilisation_commerciale")
    except Exception as exc:
        logger.warning("opposition non vérifiable (%s) : %s", siren, exc)
        return None
    # Champ absent de la réponse -> on ne conclut pas.
    return bool(valeur) if valeur is not None else None


async def marquer_opposition(
    prospects: Iterable[Prospect],
    client: httpx.AsyncClient | None = None,
    settings: Settings | None = None,
    budget_credits: int | None = None,
    strict: bool = False,
) -> dict[str, bool | None]:
    """Vérifie l'opposition commerciale de chaque prospect et l'inscrit dans
    `raw_data['opposition_commerciale']`.

    `budget_credits` borne le nombre de SIREN interrogés (1 crédit chacun). Une
    fois le budget atteint, on **s'arrête** : les prospects restants ne sont pas
    vérifiés, donc pas contactables — jamais l'inverse. Sans budget explicite, tous
    les SIREN distincts sont interrogés, ce qui peut coûter cher sur une grosse
    campagne : à câbler avec le suivi de coûts (#23).

    `strict=True` lève `BudgetCreditsEpuise` au lieu de s'arrêter silencieusement.

    Retourne le cache {siren: opposé} pour inspection et tests.
    """
    settings = settings or get_settings()
    prospects = list(prospects)
    cache: dict[str, bool | None] = {}
    interroges = 0

    ferme_client = client is None
    client = client or httpx.AsyncClient()
    try:
        for prospect in prospects:
            siren = prospect.siren
            if not siren:
                continue
            if siren not in cache:
                if budget_credits is not None and interroges >= budget_credits:
                    message = (
                        f"budget de {budget_credits} crédit(s) atteint — "
                        f"{len(prospects) - len(cache)} prospect(s) non vérifiés, "
                        "donc non contactables"
                    )
                    if strict:
                        raise BudgetCreditsEpuise(message)
                    logger.warning(message)
                    break
                if interroges:
                    await asyncio.sleep(MIN_INTERVAL_S)
                cache[siren] = await verifier_opposition(siren, client, settings)
                interroges += 1
            prospect.raw_data = {
                **(prospect.raw_data or {}),
                "opposition_commerciale": {
                    "oppose": cache[siren],
                    "verifie_le": _now(),
                    "source": "pappers/entreprise",
                    "base_legale": "art. R123-232 code de commerce",
                },
            }
    finally:
        if ferme_client:
            await client.aclose()

    opposes = sum(1 for v in cache.values() if v is True)
    inconnus = sum(1 for v in cache.values() if v is None)
    contactables = sum(1 for p in prospects if peut_etre_contacte(p))
    logger.info(
        "opposition commerciale : %d opposé(s), %d non vérifiable(s), "
        "%d/%d prospect(s) contactables — %d crédit(s) consommés",
        opposes, inconnus, contactables, len(prospects),
        interroges * COUT_CREDITS_PAR_SIREN,
    )
    return cache


def _verdict(prospect: Prospect) -> bool | None:
    bloc = (prospect.raw_data or {}).get("opposition_commerciale")
    return bloc.get("oppose") if isinstance(bloc, dict) else None


def est_oppose(prospect: Prospect) -> bool:
    """True **seulement** si la vérification a conclu à une opposition.

    ⚠️ Ne pas utiliser `not est_oppose(p)` comme autorisation de contact : un
    prospect non vérifié renverrait False ici. Utiliser `peut_etre_contacte()`.
    """
    return _verdict(prospect) is True


def peut_etre_contacte(prospect: Prospect) -> bool:
    """True **seulement** si on a vérifié que le prospect n'est pas opposé.

    C'est la garde à utiliser avant tout envoi vers un enrichisseur tiers ou toute
    file de contact. Non vérifié -> False (fermé par défaut).
    """
    return _verdict(prospect) is False


def filtrer_contactables(prospects: Iterable[Prospect]) -> list[Prospect]:
    """Ne garde que les prospects dont la non-opposition est **vérifiée**."""
    return [p for p in prospects if peut_etre_contacte(p)]
