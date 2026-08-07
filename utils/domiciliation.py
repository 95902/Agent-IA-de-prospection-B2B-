"""Détection des adresses de domiciliation (#68) — qualité des prospects.

Beaucoup d'établissements Sirene sont enregistrés chez un **domiciliataire**
(société qui fournit une adresse de siège social et fait suivre le courrier), pas
dans un local d'exploitation. Mesuré sur 40 garages parisiens réels : 3 prospects
partagent le 47 rue Vivienne, où **8 316 établissements actifs** sont enregistrés ;
5 autres se partagent deux adresses hébergeant 42 055 et 4 219 établissements.

Deux conséquences, d'où cette détection :

1. **Qualité** — un « garage » domicilié dans le 2ᵉ arrondissement n'a pas
   d'atelier : c'est un mauvais prospect pour un logiciel de gestion d'atelier.
2. **Mesure** — c'est la cause racine de l'échec de l'enrichissement (#18/PR #66,
   0 % d'email et de téléphone) : ces établissements n'ont aucune existence
   physique localisable, donc ni site, ni fiche annuaire, ni point sur une carte.
   Tant qu'on ne les écarte pas, tout taux d'enrichissement est faussé.

On **marque**, on ne supprime pas : un immeuble de bureaux légitime peut héberger
des dizaines d'entreprises, et la décision d'exclure appartient au scoring / à
l'ICP du client. Aucune liste de domiciliataires n'est codée en dur — c'est le
**comptage** qui décide (règle #3).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable, NamedTuple

import httpx

from config.settings import Settings, get_settings
from models.prospect import Prospect

logger = logging.getLogger(__name__)

# Même API que la collecte (#15). Constante locale : `utils/` ne dépend pas de
# `agents/` (sens des dépendances).
INSEE_BASE = "https://api.insee.fr/api-sirene/3.11"
MIN_INTERVAL_S = 2.0  # Sirene : 30 req/min


class AdresseCle(NamedTuple):
    """Adresse normalisée, telle que Sirene la stocke."""
    numero: str
    type_voie: str | None
    libelle_voie: str
    code_commune: str


def cle_adresse(raw_data: dict | None) -> AdresseCle | None:
    """Extrait l'adresse exacte depuis le JSON Sirene conservé dans `raw_data`.

    On repart des **champs bruts** et non de `Prospect.adresse` (chaîne
    concaténée) : re-parser une chaîne donne des faux positifs sur les noms de
    voie. Vérifié en direct — « 60 RUE FRANCOIS IER » (chiffre romain, tel que
    Sirene le stocke) et « 60 rue François 1er » ne renvoient pas le même nombre.

    Retourne None si l'adresse est inexploitable, notamment **sans numéro de
    voie** : on compterait alors toute la rue (mesuré : 44 589 établissements
    pour « RUE FRANCOIS IER » sans numéro, contre 42 055 au n° 60).
    """
    adresse = (raw_data or {}).get("adresseEtablissement") or {}
    numero = adresse.get("numeroVoieEtablissement")
    libelle = adresse.get("libelleVoieEtablissement")
    commune = adresse.get("codeCommuneEtablissement")
    if not (numero and libelle and commune):
        return None
    return AdresseCle(str(numero), adresse.get("typeVoieEtablissement"),
                      str(libelle), str(commune))


def _requete(cle: AdresseCle) -> str:
    parties = [
        f'numeroVoieEtablissement:"{cle.numero}"',
        f'libelleVoieEtablissement:"{cle.libelle_voie}"',
        f"codeCommuneEtablissement:{cle.code_commune}",
    ]
    if cle.type_voie:
        parties.append(f'typeVoieEtablissement:"{cle.type_voie}"')
    # Champ « période » → doit être enveloppé, sinon HTTP 400 (cf. #15).
    parties.append("periode(etatAdministratifEtablissement:A)")
    return " AND ".join(parties)


async def compter_a_adresse(
    cle: AdresseCle, client: httpx.AsyncClient, settings: Settings
) -> int | None:
    """Nombre d'établissements ACTIFS à cette adresse exacte. None si l'API échoue."""
    if not settings.insee_api_key:
        logger.warning("insee_api_key absente — détection de domiciliation ignorée")
        return None
    try:
        resp = await client.get(
            f"{INSEE_BASE}/siret",
            params={"q": _requete(cle), "nombre": 1},
            headers={"X-INSEE-Api-Key-Integration": settings.insee_api_key,
                     "Accept": "application/json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json().get("header", {}).get("total")
    except Exception as exc:  # une adresse non vérifiable ne casse pas le run
        logger.warning("comptage domiciliation KO (%s) : %s", cle.libelle_voie, exc)
        return None


async def marquer_domiciliation(
    prospects: Iterable[Prospect],
    client: httpx.AsyncClient | None = None,
    settings: Settings | None = None,
) -> dict[AdresseCle, int]:
    """Marque les prospects situés à une adresse de domiciliation.

    Écrit dans `raw_data['domiciliation']` : le comptage, le seuil appliqué et le
    verdict — on garde la traçabilité plutôt que de supprimer la fiche.

    Les adresses sont **dédupliquées** : plusieurs prospects partagent souvent la
    même (c'est précisément le signal), et l'API Sirene est limitée à 30 req/min.
    Retourne le cache {adresse: comptage} pour inspection/tests.
    """
    settings = settings or get_settings()
    prospects = list(prospects)
    cache: dict[AdresseCle, int] = {}

    ferme_client = client is None
    client = client or httpx.AsyncClient()
    try:
        premier = True
        for prospect in prospects:
            cle = cle_adresse(prospect.raw_data)
            if cle is None:
                continue
            if cle not in cache:
                if not premier:
                    await asyncio.sleep(MIN_INTERVAL_S)
                premier = False
                total = await compter_a_adresse(cle, client, settings)
                if total is None:
                    continue
                cache[cle] = total
            total = cache[cle]
            prospect.raw_data = {
                **(prospect.raw_data or {}),
                "domiciliation": {
                    "etablissements_a_cette_adresse": total,
                    "seuil": settings.domiciliation_seuil,
                    "suspecte": total >= settings.domiciliation_seuil,
                },
            }
    finally:
        if ferme_client:
            await client.aclose()

    marques = sum(
        1 for p in prospects
        if (p.raw_data or {}).get("domiciliation", {}).get("suspecte")
    )
    logger.info(
        "domiciliation : %d/%d prospects marqués (%d adresses distinctes vérifiées)",
        marques, len(prospects), len(cache),
    )
    return cache


def est_domicilie(prospect: Prospect) -> bool:
    """Verdict porté par `marquer_domiciliation`. False si non vérifié."""
    return bool((prospect.raw_data or {}).get("domiciliation", {}).get("suspecte"))
