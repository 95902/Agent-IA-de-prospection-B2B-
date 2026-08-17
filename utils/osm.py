"""Enrichissement contacts par jointure GÉOGRAPHIQUE OpenStreetMap (#69).

`enrichissement_agent.py` (#18) identifie l'entreprise par son **nom** sur le web
ouvert — mesuré à 0 % sur des garages enregistrés au nom civil du gérant. Ici on
joint par la **géographie**, ce qui contourne le problème d'identification :

    Sirene (adresse)
      → géocodage BAN (api-adresse.data.gouv.fr — gratuit, officiel, sans clé)
      → POI OSM du bon type le plus proche (Overpass — gratuit, sans clé)
      → tags phone / website / email

Un faux positif exigerait **deux entreprises du même secteur à la même adresse** —
bien plus rare qu'une collision de noms. Mesuré sur 40 hôtels parisiens réels :
75 % de jointure, 50 % de site, 32 % de téléphone, 30 % d'email, pour 0 €.

## Conception (batch par ZONE, pas par prospect)

Overpass est un service bénévole : **une seule requête par zone**, jamais une par
prospect (critère d'acceptance #69). D'où une fonction batch, sur le patron de
`utils/domiciliation.py` : on géocode le lot, on groupe par zone, une requête
Overpass par zone (cache), puis on rapproche chaque prospect au POI le plus proche.
Le câblage dans la cascade per-prospect de #18 se fera en pré-passe (l'ordre du
graphe est fixé en #28) — hors périmètre de ce module.

## Règle #3 — le type de POI est une donnée d'ICP

`shop=car_repair` ne vaut que pour des garages. Le(s) tag(s) viennent de
`CriteresCiblage.osm_tags` (par campagne), **jamais codés en dur**.

## Réglages confirmés par la mesure (ne pas re-découvrir)

- **BAN score ≥ 0.6** obligatoire : « 16 RUE DE MAGDEBOURG » a été géocodé « Rue de
  Musset » à 0.41 — faux rapprochement.
- **nom commun OU distance < ~30 m** : à 150 m sans correspondance de nom, faux positifs.
- **téléphone = tag `phone` d'OSM**, jamais du regex de page (bruit).
- **Overpass** : corps `data=<requête urlencodée>` en form-encoded + **vrai
  User-Agent**, sinon HTTP 406. `overpass.openstreetmap.fr` est arrêté → `overpass-api.de`
  (secours `overpass.kumi.systems`).

⚖️ Données OSM en **ODbL** (partage à l'identique) : usage interne OK, mais
**redistribuer** des fiches dérivées à un client peut déclencher attribution/partage.
À trancher avant la 1re campagne facturée (#35) — voir `docs/LEGAL.md`.
"""
from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import httpx

from config.settings import Settings, get_settings
from models.prospect import Prospect, _clean_email, _normalize_phone

logger = logging.getLogger(__name__)

BAN_URL = "https://api-adresse.data.gouv.fr/search/"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
# Overpass et BAN demandent un User-Agent identifiant (pas de navigateur usurpé).
USER_AGENT = "prospection-b2b/1.0 (+https://github.com/95902/Agent-IA-de-prospection-B2B-)"

BAN_SCORE_MIN = 0.6        # en deçà, le géocodage n'est pas fiable (mesuré)
RAYON_DEFAUT_M = 150       # rayon de rapprochement au POI
DISTANCE_NOM_LIBRE_M = 30  # sous cette distance, on accepte sans correspondance de nom
BBOX_MARGE_DEG = 0.01      # ~1,1 km de marge autour des points d'une zone
OVERPASS_MIN_INTERVAL_S = 3.0  # politesse : service bénévole

# Formes juridiques / mots sans pouvoir discriminant pour la similarité de nom.
_STOP_NOM = frozenset({
    "sarl", "sasu", "eurl", "sas", "sa", "ets", "etablissements", "societe",
    "entreprise", "entreprises", "france", "the", "les", "des", "aux",
})


@dataclass
class POI:
    """Point d'intérêt OSM, réduit à ce qu'on exploite."""
    lat: float
    lon: float
    nom: str | None = None
    phone: str | None = None
    website: str | None = None
    email: str | None = None


# --- Géométrie / nom (pur, testable) ----------------------------------------
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points (formule de haversine)."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _tokens_nom(nom: str) -> set[str]:
    """Tokens significatifs d'un nom (minuscule, sans accent, ≥ 4 lettres,
    hors formes juridiques)."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", (nom or "").lower())
    sans_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    bruts = "".join(c if c.isalnum() else " " for c in sans_accent).split()
    return {t for t in bruts if len(t) >= 4 and t not in _STOP_NOM}


def _nom_similaire(nom_entreprise: str | None, nom_poi: str | None) -> bool:
    """True si les deux noms partagent au moins un token significatif. Indice de
    confirmation, pas un veto (le POI peut ne pas avoir de `name`)."""
    if not nom_entreprise or not nom_poi:
        return False
    return bool(_tokens_nom(nom_entreprise) & _tokens_nom(nom_poi))


def _extraire_contacts_poi(tags: dict) -> dict:
    """Contacts d'un POI depuis ses tags OSM (variantes `contact:*` incluses)."""
    def premier(*cles: str) -> str | None:
        for c in cles:
            v = tags.get(c)
            if v:
                return v
        return None
    return {
        "phone": premier("phone", "contact:phone", "contact:mobile"),
        "website": premier("website", "contact:website", "url"),
        "email": premier("email", "contact:email"),
    }


def _meilleur_poi(
    prospect: Prospect, lat: float, lon: float, pois: Iterable[POI], rayon_m: float
) -> tuple[POI, float] | None:
    """POI le plus proche accepté : dans le rayon ET (distance < 30 m OU nom commun).
    Retourne (poi, distance_m) ou None."""
    candidats = sorted(
        ((p, _haversine_m(lat, lon, p.lat, p.lon)) for p in pois),
        key=lambda t: t[1],
    )
    for poi, dist in candidats:
        if dist > rayon_m:
            break  # triés : les suivants sont plus loin
        if dist < DISTANCE_NOM_LIBRE_M or _nom_similaire(prospect.nom_entreprise, poi.nom):
            return poi, dist
    return None


def _construire_requete_overpass(osm_tags: list[str], bbox: tuple[float, float, float, float]) -> str:
    """Requête Overpass QL : union node+way des tags donnés dans la bbox
    (sud, ouest, nord, est). `out center` fournit un point pour les `way`."""
    s, w, n, e = bbox
    zone = f"({s},{w},{n},{e})"
    clauses = []
    for tag in osm_tags:
        cle, _, valeur = tag.partition("=")
        sel = f'["{cle.strip()}"="{valeur.strip()}"]' if valeur else f'["{cle.strip()}"]'
        clauses.append(f"  node{sel}{zone};")
        clauses.append(f"  way{sel}{zone};")
    corps = "\n".join(clauses)
    return f"[out:json][timeout:60];\n(\n{corps}\n);\nout center tags;"


def _parser_pois(data: dict) -> list[POI]:
    """Éléments Overpass -> POI. `node` porte lat/lon ; `way` porte `center`."""
    pois: list[POI] = []
    for el in data.get("elements", []):
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lon = el.get("lon", (el.get("center") or {}).get("lon"))
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {}) or {}
        contacts = _extraire_contacts_poi(tags)
        pois.append(POI(lat=lat, lon=lon, nom=tags.get("name"), **contacts))
    return pois


# --- Réseau (mockable) ------------------------------------------------------
async def geocoder_ban(
    adresse: str, client: httpx.AsyncClient, score_min: float = BAN_SCORE_MIN
) -> tuple[float, float, float] | None:
    """Adresse -> (lat, lon, score) via la BAN. None si vide, échec, ou score
    sous le seuil (géocodage non fiable)."""
    if not adresse or not adresse.strip():
        return None
    try:
        resp = await client.get(
            BAN_URL, params={"q": adresse, "limit": 1},
            headers={"User-Agent": USER_AGENT}, timeout=20.0,
        )
        resp.raise_for_status()
        features = resp.json().get("features") or []
    except Exception as exc:
        logger.warning("BAN indisponible (%s) : %s", adresse[:40], exc)
        return None
    if not features:
        return None
    props = features[0].get("properties", {})
    lon, lat = features[0]["geometry"]["coordinates"]
    score = props.get("score", 0.0)
    if score < score_min:
        logger.debug("BAN score %.2f < %.2f pour %r — rejeté", score, score_min, adresse[:40])
        return None
    return lat, lon, score


async def interroger_overpass(
    osm_tags: list[str], bbox: tuple[float, float, float, float], client: httpx.AsyncClient
) -> list[POI]:
    """POI OSM des types donnés dans la bbox. Corps form-encoded + User-Agent
    (sinon 406). Bascule sur le miroir si le principal échoue. [] si tout échoue."""
    requete = _construire_requete_overpass(osm_tags, bbox)
    for url in OVERPASS_URLS:
        try:
            resp = await client.post(
                url, data={"data": requete},
                headers={"User-Agent": USER_AGENT,
                         "Content-Type": "application/x-www-form-urlencoded"},
                timeout=90.0,
            )
            resp.raise_for_status()
            return _parser_pois(resp.json())
        except Exception as exc:
            logger.warning("Overpass KO (%s) : %s", url, exc)
            continue
    return []


# --- Orchestration batch ----------------------------------------------------
def _zone_de(prospect: Prospect) -> str:
    """Clé de zone pour grouper les requêtes Overpass. Code postal si dispo,
    sinon département — assez fin pour garder une bbox petite."""
    return prospect.code_postal or prospect.departement or "?"


def _bbox_de(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return (min(lats) - BBOX_MARGE_DEG, min(lons) - BBOX_MARGE_DEG,
            max(lats) + BBOX_MARGE_DEG, max(lons) + BBOX_MARGE_DEG)


def _appliquer_contacts(prospect: Prospect, poi: POI, dist: float, score: float,
                        osm_tags: list[str]) -> None:
    """Remplit les champs manquants depuis le POI (jamais d'écrasement) et trace."""
    if prospect.telephone is None and poi.phone:
        prospect.telephone = _normalize_phone(poi.phone)
    if prospect.email is None and poi.email:
        prospect.email = _clean_email(poi.email)
    if not prospect.site_web and poi.website:
        prospect.site_web = poi.website
    prospect.raw_data = {
        **(prospect.raw_data or {}),
        "osm": {
            "rapproche": True,
            "poi_nom": poi.nom,
            "distance_m": round(dist, 1),
            "ban_score": round(score, 3),
            "tags_type": list(osm_tags),
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }


async def enrichir_par_osm(
    prospects: Iterable[Prospect],
    osm_tags: list[str],
    client: httpx.AsyncClient | None = None,
    settings: Settings | None = None,
    rayon_m: float = RAYON_DEFAUT_M,
) -> dict[str, int]:
    """Enrichit `prospects` en tél/email/site par jointure géographique OSM.

    `osm_tags` vient de l'ICP (`CriteresCiblage.osm_tags`) — vide = source
    inapplicable, on ne fait rien. Retourne des compteurs {geocodes, rapproches,
    emails, telephones} pour le log / les métriques (#23) / les tests.
    """
    settings = settings or get_settings()  # noqa: F841 — homogénéité de signature
    prospects = list(prospects)
    stats = {"geocodes": 0, "rapproches": 0, "emails": 0, "telephones": 0}
    if not osm_tags:
        logger.info("osm : aucun tag OSM dans l'ICP — source inapplicable")
        return stats
    if not prospects:
        return stats

    ferme_client = client is None
    client = client or httpx.AsyncClient()
    try:
        # 1. Géocoder tout le lot (BAN), garder les points fiables.
        points: dict[int, tuple[float, float, float]] = {}
        for p in prospects:
            geo = await geocoder_ban(p.adresse or "", client)
            if geo is not None:
                points[id(p)] = geo
                stats["geocodes"] += 1

        # 2. Grouper par zone, une requête Overpass par zone (cache).
        par_zone: dict[str, list[Prospect]] = {}
        for p in prospects:
            if id(p) in points:
                par_zone.setdefault(_zone_de(p), []).append(p)

        premier = True
        for zone, membres in par_zone.items():
            bbox = _bbox_de([points[id(p)][:2] for p in membres])
            if not premier:
                await asyncio.sleep(OVERPASS_MIN_INTERVAL_S)
            premier = False
            pois = await interroger_overpass(osm_tags, bbox, client)
            if not pois:
                continue
            # 3. Rapprocher chaque prospect de la zone.
            for p in membres:
                lat, lon, score = points[id(p)]
                trouve = _meilleur_poi(p, lat, lon, pois, rayon_m)
                if trouve is None:
                    continue
                poi, dist = trouve
                avait_tel = p.telephone is not None
                avait_mail = p.email is not None
                _appliquer_contacts(p, poi, dist, score, osm_tags)
                stats["rapproches"] += 1
                if not avait_tel and p.telephone:
                    stats["telephones"] += 1
                if not avait_mail and p.email:
                    stats["emails"] += 1
    finally:
        if ferme_client:
            await client.aclose()

    logger.info(
        "osm : %d géocodés, %d rapprochés, %d tél, %d email (sur %d prospects, %d zones)",
        stats["geocodes"], stats["rapproches"], stats["telephones"], stats["emails"],
        len(prospects), len(par_zone) if osm_tags else 0,
    )
    return stats
