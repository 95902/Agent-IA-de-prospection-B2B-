"""Enrichissement email B2B via Dropcontact (#21) — fallback PAYANT.

Dernier recours de la chaîne email, **après** la chaîne gratuite (OSM #69 +
cascade #18). Dropcontact devine l'email professionnel (prénom.nom@entreprise) à
partir du nom du dirigeant (#67) + la raison sociale + le SIREN — **sans besoin de
site web** (contrairement à la spec d'origine de #21, corrigée ici).

## Facturation « pay on success »

Un crédit n'est débité que si un email vérifié est renvoyé ; les recherches
infructueuses sont gratuites. Mesuré : **0 email sur 15 micro-entreprises**
locales (garages/hôtels), **1/4 sur des PME B2B établies**. Donc à réserver aux
ICP « PME établies » — inutile sur des micro-entreprises (cf. issue #21).

## Garde légale AVANT dépense (non négociable)

On n'interroge Dropcontact que pour les prospects **vérifiés non opposés**
(`peut_etre_contacte()`, art. R123-232). Le nettoyage (#19) doit donc avoir tourné
avant : envoyer un prospect opposé chez un enrichisseur tiers est exactement ce que
le droit d'opposition interdit. Condition d'appel complète :

    email IS None  ET  nom_dirigeant IS NOT None  ET  peut_etre_contacte(p)

## API réelle (la spec #21 et ARCHITECTURE.md étaient fausses)

- `POST https://api.dropcontact.com/v1/enrich/all` — corps `{"data": [...], "siren": true}`
- Auth : header **`X-Access-Token`** (pas Bearer)
- Polling : `GET /v1/enrich/all/{request_id}` jusqu'à `success: true`
- La réponse conserve l'ORDRE des entrées.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Iterable

import httpx

from config.settings import Settings, get_settings
from models.prospect import Prospect, _clean_email
from utils.opposition_commerciale import peut_etre_contacte

logger = logging.getLogger(__name__)

DROPCONTACT_URL = "https://api.dropcontact.com/v1/enrich/all"
POLL_INTERVAL_S = 5.0
MAX_ATTEMPTS = 24  # ~2 min à 5 s


def _eligibles(prospects: Iterable[Prospect]) -> list[Prospect]:
    """Prospects éligibles à l'appel Dropcontact : sans email, avec dirigeant, et
    **vérifiés non opposés** (garde légale). Website non requis."""
    return [
        p for p in prospects
        if p.email is None and p.nom_dirigeant and peut_etre_contacte(p)
    ]


def _payload(prospects: list[Prospect]) -> list[dict]:
    """Entrées Dropcontact. `full_name` + `company` est le combo minimal viable ;
    on ajoute SIREN/SIRET (toujours dispo via Sirene) pour fiabiliser le matching."""
    items: list[dict] = []
    for p in prospects:
        item: dict = {"full_name": p.nom_dirigeant, "company": p.nom_entreprise}
        if p.siren:
            item["num_siren"] = p.siren
        if p.siret:
            item["siret"] = p.siret
        if p.site_web:
            item["website"] = p.site_web
        items.append(item)
    return items


def _email_de(item: dict) -> str | None:
    """Extrait l'email d'une entrée de réponse Dropcontact (`email` = liste
    d'objets `{email, qualification}`)."""
    emails = item.get("email") or []
    if isinstance(emails, list) and emails:
        return emails[0].get("email")
    if isinstance(emails, str):  # tolérance si l'API renvoie une chaîne
        return emails or None
    return None


async def soumettre(
    data: list[dict], client: httpx.AsyncClient, settings: Settings
) -> str | None:
    """Soumet le lot, retourne le `request_id`. None si l'API échoue."""
    try:
        resp = await client.post(
            DROPCONTACT_URL,
            json={"data": data, "siren": True},
            headers={"X-Access-Token": settings.dropcontact_api_key,
                     "Content-Type": "application/json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json().get("request_id")
    except Exception as exc:
        logger.warning("Dropcontact soumission KO : %s", exc)
        return None


async def resultat(
    request_id: str, client: httpx.AsyncClient, settings: Settings,
    poll_interval: float = POLL_INTERVAL_S, max_attempts: int = MAX_ATTEMPTS,
) -> list[dict]:
    """Poll jusqu'à `success: true`. [] si timeout ou erreur (jamais bloquant)."""
    url = f"{DROPCONTACT_URL}/{request_id}"
    headers = {"X-Access-Token": settings.dropcontact_api_key}
    for tentative in range(max_attempts):
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:
            logger.warning("Dropcontact polling KO : %s", exc)
            return []
        if body.get("success"):
            return body.get("data", []) or []
        if tentative < max_attempts - 1:
            await asyncio.sleep(poll_interval)
    logger.warning("Dropcontact : résultat non prêt après %d tentatives", max_attempts)
    return []


async def enrichir_emails(
    prospects: Iterable[Prospect],
    client: httpx.AsyncClient | None = None,
    settings: Settings | None = None,
    budget: int | None = None,
    poll_interval: float = POLL_INTERVAL_S,
    max_attempts: int = MAX_ATTEMPTS,
) -> dict[str, int]:
    """Complète l'email des prospects éligibles via Dropcontact (fallback payant).

    `budget` plafonne le nombre de prospects soumis (pay on success : les échecs ne
    coûtent rien, mais on borne quand même la dépense potentielle). Retourne des
    compteurs {eligibles, soumis, emails} pour le log / les métriques (#23).
    """
    settings = settings or get_settings()
    prospects = list(prospects)
    stats = {"eligibles": 0, "soumis": 0, "emails": 0}

    elig = _eligibles(prospects)
    stats["eligibles"] = len(elig)
    if not elig:
        return stats
    if not settings.dropcontact_api_key:
        logger.warning("dropcontact_api_key absente — enrichissement email ignoré")
        return stats
    if budget is not None:
        elig = elig[:budget]
    stats["soumis"] = len(elig)

    ferme_client = client is None
    client = client or httpx.AsyncClient()
    try:
        request_id = await soumettre(_payload(elig), client, settings)
        if not request_id:
            return stats
        data = await resultat(request_id, client, settings, poll_interval, max_attempts)
        # La réponse conserve l'ordre des entrées -> appariement par position.
        for prospect, item in zip(elig, data):
            brut = _email_de(item)
            email = _clean_email(brut) if brut else None
            if prospect.email is None and email:
                prospect.email = email
                stats["emails"] += 1
            prospect.raw_data = {
                **(prospect.raw_data or {}),
                "dropcontact": {
                    "email": brut,
                    "retenu": bool(email) and prospect.email == email,
                    "at": datetime.now(timezone.utc).isoformat(),
                },
            }
    finally:
        if ferme_client:
            await client.aclose()

    logger.info(
        "dropcontact : %d éligible(s), %d soumis, %d email(s) trouvé(s)",
        stats["eligibles"], stats["soumis"], stats["emails"],
    )
    return stats
