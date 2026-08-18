"""Node de collecte Sirene INSEE (#15) — 1er node du pipeline.

Interroge l'API Sirene 3.11 pour les établissements correspondant à l'ICP de la
campagne (départements × codes NAF de `CriteresCiblage`), et les convertit en
objets `Prospect` (#10). Aucune valeur métier codée en dur : NAF/dept viennent
de `criteres_ciblage` (règle #3).

⚠️ Pièges API vérifiés en direct (voir mémoire projet) :
- `activitePrincipaleEtablissement` et `etatAdministratifEtablissement` sont des
  champs « période » → à envelopper dans `periode(...)`, sinon HTTP 400.
- Le code NAF s'écrit avec un point côté INSEE (`45.20Z`), alors que
  `criteres_ciblage.codes_naf` stocke `4520A` → on insère le point.
- Sirene ne renvoie NI téléphone NI email → enrichissement (#18). Le JSON brut
  est conservé dans `raw_data` (contient aussi le signal personne physique/morale
  utile pour la loi 2025-594).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from config.settings import get_settings
from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from models.prospect import Prospect

logger = logging.getLogger(__name__)

INSEE_BASE = "https://api.insee.fr/api-sirene/3.11"
PAGE_SIZE = 1000        # maximum autorisé par requête
MIN_INTERVAL_S = 2.0    # 30 req/min → 1 requête / 2 s
MAX_RETRIES = 3

# Tranches d'effectif INSEE → (libellé, borne basse). 'NN' / absent → non déterminé.
EFFECTIF_TRANCHES: dict[str, tuple[str, int]] = {
    "00": ("0 salarié", 0), "01": ("1 ou 2 salariés", 1),
    "02": ("3 à 5 salariés", 3), "03": ("6 à 9 salariés", 6),
    "11": ("10 à 19 salariés", 10), "12": ("20 à 49 salariés", 20),
    "21": ("50 à 99 salariés", 50), "22": ("100 à 199 salariés", 100),
    "31": ("200 à 249 salariés", 200), "32": ("250 à 499 salariés", 250),
    "41": ("500 à 999 salariés", 500), "42": ("1000 à 1999 salariés", 1000),
    "51": ("2000 à 4999 salariés", 2000), "52": ("5000 à 9999 salariés", 5000),
    "53": ("10000 salariés et plus", 10000),
}


def _naf_avec_point(naf: str) -> str:
    """`4520A` → `45.20A` (format attendu par l'API). Idempotent."""
    naf = naf.strip().upper()
    if "." in naf or len(naf) < 5:
        return naf
    return f"{naf[:2]}.{naf[2:]}"


def _build_query(naf: str, dept: str) -> str:
    """Requête `q` correcte : champs période enveloppés dans `periode(...)`."""
    return (
        f"periode(activitePrincipaleEtablissement:{_naf_avec_point(naf)} "
        f"AND etatAdministratifEtablissement:A) "
        f"AND codePostalEtablissement:{dept}*"
    )


def _parser_etablissement(etab: dict, campagne_id) -> Prospect | None:
    """Réponse JSON INSEE → `Prospect`. None si le SIRET est invalide (le
    validator #10 lèverait) : on ignore l'établissement sans casser le run."""
    ul = etab.get("uniteLegale", {})
    ad = etab.get("adresseEtablissement", {})
    per = (etab.get("periodesEtablissement") or [{}])[0]

    nom = ul.get("denominationUniteLegale")
    if not nom:  # personne physique : prénom + nom
        nom = " ".join(
            p for p in (ul.get("prenom1UniteLegale"), ul.get("nomUniteLegale")) if p
        )
    nom = (nom or "").strip() or "SANS DÉNOMINATION"

    tranche = ul.get("trancheEffectifsUniteLegale")
    libelle_eff, borne = EFFECTIF_TRANCHES.get(tranche, (None, None))

    adresse = " ".join(
        str(x) for x in (
            ad.get("numeroVoieEtablissement"),
            ad.get("typeVoieEtablissement"),
            ad.get("libelleVoieEtablissement"),
        ) if x
    ) or None
    cp = ad.get("codePostalEtablissement")

    try:
        return Prospect(
            campagne_id=campagne_id,
            siret=etab.get("siret"),
            siren=etab.get("siren"),
            nom_entreprise=nom,
            code_naf=per.get("activitePrincipaleEtablissement"),
            effectif=libelle_eff,
            effectif_code=tranche,
            effectif_estime=borne,
            date_creation=etab.get("dateCreationEtablissement"),
            adresse=adresse,
            code_postal=cp,
            ville=ad.get("libelleCommuneEtablissement"),
            departement=(cp[:2] if cp else None),
            raw_data=etab,
        )
    except Exception as exc:  # SIRET invalide, etc.
        logger.warning("Établissement ignoré (siret=%s) : %s", etab.get("siret"), exc)
        return None


async def _fetch_etablissements(
    client: httpx.AsyncClient, headers: dict, dept: str, naf: str, limit: int
) -> list[dict]:
    """Pagine l'API pour un couple (dept, naf) jusqu'à `limit` établissements ou
    épuisement. Gère le 429 (retry ×3) et le throttle 30 req/min."""
    query = _build_query(naf, dept)
    collected: list[dict] = []
    debut = 0
    while len(collected) < limit:
        nombre = min(PAGE_SIZE, limit - len(collected))
        params = {"q": query, "nombre": nombre, "debut": debut}
        data = None
        for attempt in range(1, MAX_RETRIES + 1):
            resp = await client.get(f"{INSEE_BASE}/siret", params=params, headers=headers)
            if resp.status_code == 429:
                logger.warning("429 INSEE (%s/%s, tentative %d) — pause", dept, naf, attempt)
                await asyncio.sleep(MIN_INTERVAL_S)
                continue
            if resp.status_code == 404:
                # INSEE renvoie 404 (et non 200 vide) quand une requête valide ne
                # matche AUCUN établissement (couple dept/NAF sans résultat).
                logger.info("Aucun établissement pour %s / %s", dept, naf)
                return collected
            resp.raise_for_status()
            data = resp.json()
            break
        if data is None:
            raise RuntimeError(f"INSEE : 429 persistant pour {dept}/{naf}")

        etabs = data.get("etablissements", [])
        collected.extend(etabs)
        total = data.get("header", {}).get("total", 0)
        debut += nombre
        if not etabs or debut >= total:
            break
        await asyncio.sleep(MIN_INTERVAL_S)  # throttle entre deux requêtes
    return collected[:limit]


async def sirene_node(state: EtatAgent, limit: int = 500) -> EtatAgent:
    """Node de collecte : interroge Sirene pour l'ICP de la campagne et ajoute
    les `Prospect` obtenus à `state['prospects']`.

    Itère sur tous les couples (département, code NAF) de `state['criteres']`.
    La clé API vient de `settings.insee_api_key` (jamais codée en dur).
    """
    criteres: CriteresCiblage = state["criteres"]
    campagne_id = state["campagne_id"]
    limit = state.get("limit") or limit  # plafond CLI (#29) prioritaire sur le défaut
    api_key = get_settings().insee_api_key
    if not api_key:
        raise RuntimeError("INSEE_API_KEY manquante (voir .env / config.settings).")

    headers = {"X-INSEE-Api-Key-Integration": api_key, "Accept": "application/json"}
    prospects: list[Prospect] = list(state.get("prospects", []))

    async with httpx.AsyncClient(timeout=30.0) as client:
        for dept in criteres.departements:
            if len(prospects) >= limit:
                break
            for naf in criteres.codes_naf:
                if len(prospects) >= limit:
                    break
                reste = limit - len(prospects)
                etabs = await _fetch_etablissements(client, headers, dept, naf, reste)
                for etab in etabs:
                    prospect = _parser_etablissement(etab, campagne_id)
                    if prospect is not None:
                        prospects.append(prospect)

    state["prospects"] = prospects
    state["collectes"] = len(prospects)
    logger.info("sirene_node : %d prospects collectés", len(prospects))
    return state
