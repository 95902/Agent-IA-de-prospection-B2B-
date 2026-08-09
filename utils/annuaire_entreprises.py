"""Récupération du dirigeant via l'Annuaire des Entreprises (#67).

`Prospect.nom_dirigeant` existe (#10) mais n'était jamais renseigné : **l'API
Sirene ne renvoie pas les dirigeants**. Or c'est un prérequis dur pour
Dropcontact (#21), qui exige au minimum `first_name + last_name + company`.

Source : `recherche-entreprises.api.gouv.fr` (Annuaire des Entreprises, DINUM) —
gratuite, sans clé, officielle, et déjà autorisée par `docs/LEGAL.md` § « annuaires
professionnels publics » (règle #2).

⚠️ **Cette API ne remplace pas Sirene** : identité, NAF, adresse et effectif font
double emploi avec la collecte (#15). On l'utilise en **lookup ciblé par SIREN**,
uniquement pour ce que Sirene n'a pas :
- `dirigeants[]` — nom et prénom du dirigeant personne physique ;
- `finances` — CA / résultat net (signal de santé, conservé pour le scoring #24) ;
- `nom_commercial` / `liste_enseignes` — nom d'usage, parfois plus « cherchable »
  que la raison sociale (mesuré : ~1 garage sur 8 seulement).

Elle ne contient **aucune donnée de contact** (ni site web, ni email, ni téléphone)
— vérifié en direct : elle ne résout donc pas l'enrichissement à elle seule.

RGPD — minimisation : la réponse expose la date et l'année de naissance des
dirigeants. On ne les conserve **pas** : seuls prénom, nom et qualité sont utiles à
la prospection B2B. Voir aussi #65 pour le cas des entreprises individuelles, où le
dirigeant se confond avec l'entreprise.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Iterable, NamedTuple

import httpx

from models.prospect import Prospect

logger = logging.getLogger(__name__)

API_URL = "https://recherche-entreprises.api.gouv.fr/search"
MIN_INTERVAL_S = 0.2  # API publique sans clé — on reste poli sur le débit
UA = "agent-prospection-b2b/0.1 (+https://github.com/95902/Agent-IA-de-prospection-B2B-)"


class Dirigeant(NamedTuple):
    prenom: str
    nom: str
    qualite: str | None = None

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()


def _nettoyer(valeur: str) -> str:
    """Retire les parenthèses de l'état civil et normalise les espaces.

    Les données réelles contiennent des doublons entre parenthèses, ex.
    « PEDRO TEIXEIRA (PEDRO TEIXEIRA) ».
    """
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", valeur or "")).strip()


def _premier_prenom(prenoms: str) -> str:
    """« STÉPHANE DOMA YOANNE » -> « STÉPHANE ».

    Les enrichisseurs attendent un prénom unique ; envoyer la liste complète
    dégrade le taux de correspondance.
    """
    nettoye = _nettoyer(prenoms)
    return nettoye.split(" ")[0] if nettoye else ""


def extraire_dirigeant(resultat: dict) -> Dirigeant | None:
    """Premier dirigeant **personne physique** exploitable, sinon None.

    Les personnes morales (ex. « GROUPE OPTIMUM HOLDING », `type_dirigeant`
    = `personne morale`) sont ignorées : on ne peut pas en tirer un email
    nominatif.
    """
    for brut in (resultat.get("dirigeants") or []):
        if brut.get("type_dirigeant") == "personne morale" or brut.get("denomination"):
            continue
        prenom = _premier_prenom(brut.get("prenoms") or "")
        nom = _nettoyer(brut.get("nom") or "")
        if prenom and nom:
            return Dirigeant(prenom, nom, brut.get("qualite"))
    return None


def _nom_commercial(resultat: dict) -> str | None:
    siege = resultat.get("siege") or {}
    enseignes = siege.get("liste_enseignes") or []
    return siege.get("nom_commercial") or (enseignes[0] if enseignes else None)


async def chercher_par_siren(
    siren: str, client: httpx.AsyncClient
) -> dict | None:
    """Fiche Annuaire des Entreprises pour ce SIREN. None si absente ou API KO."""
    try:
        resp = await client.get(
            API_URL,
            params={"q": siren, "per_page": 1},
            headers={"User-Agent": UA},
            timeout=20.0,
        )
        resp.raise_for_status()
        resultats = resp.json().get("results") or []
    except Exception as exc:  # une fiche manquante ne casse pas le run
        logger.warning("annuaire-entreprises KO (%s) : %s", siren, exc)
        return None
    for resultat in resultats:
        if str(resultat.get("siren") or "") == str(siren):
            return resultat
    return None


async def enrichir_dirigeants(
    prospects: Iterable[Prospect], client: httpx.AsyncClient | None = None
) -> dict[str, Dirigeant | None]:
    """Renseigne `nom_dirigeant` depuis l'Annuaire des Entreprises.

    Écrit aussi `raw_data['annuaire']` : prénom/nom séparés (attendus tels quels
    par Dropcontact), qualité, nom commercial et finances. Retourne le cache
    {siren: dirigeant} pour inspection et tests.
    """
    prospects = list(prospects)
    cache: dict[str, Dirigeant | None] = {}

    ferme_client = client is None
    client = client or httpx.AsyncClient()
    try:
        premier = True
        for prospect in prospects:
            siren = prospect.siren
            if not siren:
                continue
            if siren not in cache:
                if not premier:
                    await asyncio.sleep(MIN_INTERVAL_S)
                premier = False
                resultat = await chercher_par_siren(siren, client)
                if resultat is None:
                    continue
                cache[siren] = extraire_dirigeant(resultat)
                prospect.raw_data = {
                    **(prospect.raw_data or {}),
                    "annuaire": {
                        # Minimisation RGPD : ni date ni année de naissance.
                        "dirigeant": (
                            {"prenom": cache[siren].prenom, "nom": cache[siren].nom,
                             "qualite": cache[siren].qualite}
                            if cache[siren] else None
                        ),
                        "nom_commercial": _nom_commercial(resultat),
                        "finances": resultat.get("finances"),
                        "at": datetime.now(timezone.utc).isoformat(),
                    },
                }
            dirigeant = cache.get(siren)
            if dirigeant and not prospect.nom_dirigeant:
                prospect.nom_dirigeant = dirigeant.nom_complet
    finally:
        if ferme_client:
            await client.aclose()

    trouves = sum(1 for p in prospects if p.nom_dirigeant)
    logger.info(
        "annuaire : %d/%d prospects avec dirigeant (%d SIREN interrogés)",
        trouves, len(prospects), len(cache),
    )
    return cache


def dirigeant_de(prospect: Prospect) -> Dirigeant | None:
    """Prénom/nom séparés depuis `raw_data` — format attendu par Dropcontact."""
    brut = (prospect.raw_data or {}).get("annuaire", {}).get("dirigeant")
    if not brut:
        return None
    return Dirigeant(brut.get("prenom", ""), brut.get("nom", ""), brut.get("qualite"))
