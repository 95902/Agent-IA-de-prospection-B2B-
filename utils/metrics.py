"""Métriques par source (#23) — visibilité performance ET coût.

Chaque source d'enrichissement renvoie déjà un dict de compteurs (osm :
`{geocodes, rapproches, emails, telephones}` ; dropcontact : `{eligibles, soumis,
emails}`). Ce module les agrège en une vue comparable — **rendement vs coût** — pour
arbitrer : quand OSM (gratuit) suffit, on n'appelle pas Dropcontact (payant).

Volontairement **pur et sans I/O** (aucune dépendance Postgres) : il consomme des
prospects + des dicts de stats et produit un rapport texte + un log. La persistance
dans la table `sources` (`derniere_collecte`, `nb_prospects`) se fera à l'assemblage
du pipeline (#28), quand un pool asyncpg sera disponible — hors périmètre ici.

Note : `utils/logger.py` (Loguru) est encore un stub → on utilise le `logging`
stdlib, comme le reste des modules réels.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from models.prospect import Prospect
from utils.opposition_commerciale import peut_etre_contacte

logger = logging.getLogger(__name__)


@dataclass
class MetriquesSource:
    """Rendement et coût d'une source sur un run."""
    source: str
    gratuite: bool
    tentes: int = 0          # prospects sur lesquels la source a été tentée
    reussis: int = 0         # prospects pour qui elle a apporté un contact
    cout_credits: int = 0    # crédits payants consommés (0 si gratuite)

    @property
    def taux(self) -> float:
        return self.reussis / self.tentes if self.tentes else 0.0


def depuis_osm(stats: dict) -> MetriquesSource:
    """Adapte les compteurs d'`utils.osm.enrichir_par_osm`."""
    return MetriquesSource(
        source="osm", gratuite=True,
        tentes=stats.get("geocodes", 0),
        reussis=stats.get("rapproches", 0),
        cout_credits=0,
    )


def depuis_dropcontact(stats: dict) -> MetriquesSource:
    """Adapte les compteurs d'`utils.dropcontact.enrichir_emails`.

    Pay on success : le coût en crédits = le nombre d'emails effectivement trouvés."""
    return MetriquesSource(
        source="dropcontact", gratuite=False,
        tentes=stats.get("soumis", 0),
        reussis=stats.get("emails", 0),
        cout_credits=stats.get("emails", 0),
    )


def _pct(part: int, total: int) -> float:
    return 100.0 * part / total if total else 0.0


def couverture_globale(prospects: Iterable[Prospect]) -> dict:
    """Métriques têtes d'affiche (cibles PRD), tous enrichisseurs confondus."""
    prospects = list(prospects)
    n = len(prospects)
    email = sum(1 for p in prospects if p.email)
    telephone = sum(1 for p in prospects if p.telephone)
    site = sum(1 for p in prospects if p.site_web)
    doublons = sum(1 for p in prospects if p.doublon)
    contactables = sum(1 for p in prospects if peut_etre_contacte(p))
    return {
        "n": n,
        "email": email, "email_pct": _pct(email, n),
        "telephone": telephone, "telephone_pct": _pct(telephone, n),
        "site_web": site, "site_web_pct": _pct(site, n),
        "doublons": doublons,
        "contactables": contactables,
    }


def rapport(couverture: dict, sources: Iterable[MetriquesSource]) -> str:
    """Rapport texte lisible sans requête SQL (pour log / revue équipe / Metabase)."""
    n = couverture["n"]
    lignes = [
        f"=== Métriques de run — {n} prospects ===",
        f"  email     : {couverture['email']:>4} ({couverture['email_pct']:.0f}%)  cible PRD ≥ 20% — PRIORITAIRE (D6)",
        f"  téléphone : {couverture['telephone']:>4} ({couverture['telephone_pct']:.0f}%)  bonus (D6) — indicatif ~40%",
        f"  site web  : {couverture['site_web']:>4} ({couverture['site_web_pct']:.0f}%)",
        f"  doublons  : {couverture['doublons']:>4}",
        f"  contactables (opposition vérifiée) : {couverture['contactables']:>4}",
        "  --- par source (rendement / coût) ---",
    ]
    for m in sources:
        cout = "gratuit" if m.gratuite else f"{m.cout_credits} crédit(s)"
        lignes.append(
            f"  {m.source:<12} : {m.reussis:>3}/{m.tentes:<3} "
            f"({m.taux * 100:.0f}%)  {cout}"
        )
    return "\n".join(lignes)


def logger_metriques(couverture: dict, sources: Iterable[MetriquesSource]) -> str:
    """Construit le rapport, le logge (une ligne par entrée) et le retourne."""
    txt = rapport(couverture, list(sources))
    for ligne in txt.splitlines():
        logger.info(ligne)
    return txt
