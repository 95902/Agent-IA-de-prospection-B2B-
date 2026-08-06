"""Node d'enrichissement (#18) — trouve tél/email des prospects collectés.

`sirene_node` (#15) produit des prospects sans contact (Sirene n'en fournit pas).
Ce node les enrichit via une **cascade de résolveurs** de sources légales
(règle #2), essayés dans l'ordre jusqu'à trouver un email + un téléphone :

    Tavily (recherche + contenu)  →  Crawl4AI (rendu JS du site)  →  DuckDuckGo

Produit orienté **email-first** (l'appel = Phase 2). La politique email de #10
est conservée telle quelle (`contact@`/`info@` restent mis à None sur
`Prospect.email`), MAIS **tous** les contacts bruts trouvés sont stockés dans
`raw_data['enrichissement']` — terrain de test pour un futur réalignement RGPD.

⚠️ Précision : un email/téléphone glané au hasard dans des résultats de recherche
appartient souvent à une AUTRE entreprise. On applique donc un **filtre par
domaine** : on ne retient un email que si son domaine == celui de la page source
(l'email propre de l'entreprise), et on ne fait confiance aux téléphones d'une
page que si elle a aussi livré un email au bon domaine.

Architecture pluggable : `RESOLVERS` est une liste ordonnée ; on peut retirer
Crawl4AI (dépendance lourde) plus tard sans refactor.
"""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config.settings import Settings, get_settings
from graph.state import EtatAgent
from models.prospect import Prospect, _clean_email, _normalize_phone

logger = logging.getLogger(__name__)

# Regex fournies par l'issue #18.
RE_PHONE = re.compile(r"(?:(?:\+33|0033|0)[1-9])(?:[\s.\-]?\d{2}){4}")
RE_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}")

# Extensions d'assets → faux positifs du regex email (ex. `image@2x.png`).
_ASSET_EXTS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tiff",
    ".css", ".js", ".ico", ".woff", ".woff2",
)

BATCH_SIZE = 5           # prospects traités en parallèle
MAX_RAW = 20             # cap des contacts bruts stockés par prospect
_TAVILY_URL = "https://api.tavily.com/search"


@dataclass
class Contacts:
    """Résultat brut d'un résolveur (avant validation / politique #10)."""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    site_web: str | None = None
    source: str = ""


# --- Domaines ---------------------------------------------------------------
def _domain(url: str) -> str:
    """Domaine enregistrable approximatif : `www.garage-x.fr/contact` → `garage-x.fr`."""
    host = urlparse(url if "//" in url else f"//{url}").netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _email_domain(email: str) -> str:
    return _domain(email.rsplit("@", 1)[-1])


# Mots trop génériques pour identifier une entreprise (secteur/forme juridique).
_GENERIC_TOKENS = frozenset({
    "garage", "auto", "autos", "automobile", "automobiles", "carrosserie",
    "mecanique", "reparation", "pieces", "pneus", "pare", "brise", "service",
    "services", "sarl", "sas", "sasu", "eurl", "sa", "ets", "etablissements",
    "groupe", "compagnie", "cie", "france", "paris", "societe",
})


def _name_tokens(nom: str) -> list[str]:
    """Tokens significatifs du nom (sans accents, ≥4 lettres, hors génériques)."""
    n = unicodedata.normalize("NFKD", nom.lower()).encode("ascii", "ignore").decode()
    return [t for t in re.split(r"[^a-z0-9]+", n) if len(t) >= 4 and t not in _GENERIC_TOKENS]


def _name_matches_domain(nom: str, domain: str) -> bool:
    """Le domaine appartient-il vraisemblablement à l'entreprise ? True si sa
    racine contient un token significatif du nom. False si le nom est trop
    générique (on ne peut pas confirmer → on préfère ne rien retenir)."""
    root = domain.rsplit(".", 1)[0].replace("-", "")
    tokens = _name_tokens(nom)
    return any(t in root or root in t for t in tokens) if tokens else False


# --- Extraction -------------------------------------------------------------
def _extract_from_text(text: str, source_domain: str | None = None) -> tuple[list[str], list[str]]:
    """Emails/téléphones du texte. Si `source_domain` est fourni, ne garde que les
    emails de ce domaine (l'email propre de l'entreprise, pas ceux glanés ailleurs)."""
    emails = [e for e in RE_EMAIL.findall(text or "") if not e.lower().endswith(_ASSET_EXTS)]
    if source_domain:
        emails = [e for e in emails if _email_domain(e) == source_domain]
    return emails, RE_PHONE.findall(text or "")


def _extract_from_html(html: str, source_domain: str | None = None) -> tuple[list[str], list[str]]:
    """Emails via `mailto:` (fiable) + regex ; téléphones via regex. Filtre domaine."""
    mailtos: list[str] = []
    try:
        soup = BeautifulSoup(html or "", "html.parser")
        for a in soup.select('a[href^="mailto:"]'):
            addr = a.get("href", "")[len("mailto:"):].split("?")[0].strip()
            if addr:
                mailtos.append(addr)
        text = soup.get_text(" ")
    except Exception:  # HTML malformé → on retombe sur le brut
        text = html or ""
    if source_domain:
        mailtos = [m for m in mailtos if _email_domain(m) == source_domain]
    e, phones = _extract_from_text(text, source_domain)
    return mailtos + e, phones


# --- Résolveurs (ordre = cascade) ------------------------------------------
async def _resolve_tavily(
    prospect: Prospect, client: httpx.AsyncClient, settings: Settings, site_web: str | None
) -> Contacts | None:
    """Recherche Tavily sur nom+ville ; extrait par résultat en filtrant sur le
    domaine de la page (email propre de l'entreprise). Propose un site candidat."""
    if not settings.tavily_api_key:
        return None
    query = f"{prospect.nom_entreprise} {prospect.ville or ''} contact email".strip()
    resp = await client.post(
        _TAVILY_URL,
        headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
        json={"query": query, "include_raw_content": True, "max_results": 5},
    )
    logger.info("Tavily +1 (quota 1000/mois, #23) — %s", prospect.siret)
    resp.raise_for_status()
    data = resp.json()

    emails: list[str] = []
    phones: list[str] = []
    candidate_site = site_web
    for result in data.get("results", []):
        url = result.get("url", "")
        domain = _domain(url)
        # On n'extrait que des pages dont le domaine matche le nom de l'entreprise
        # (sinon on récupère les contacts d'une AUTRE société).
        if not _name_matches_domain(prospect.nom_entreprise, domain):
            continue
        content = f"{result.get('raw_content') or ''} {result.get('content') or ''}"
        e, p = _extract_from_text(content, source_domain=domain)
        emails += e
        phones += p  # page confirmée = l'entreprise → son tél est fiable
        if candidate_site is None and url:
            candidate_site = url
    return Contacts(emails, phones, candidate_site, "tavily")


async def _resolve_crawl4ai(
    prospect: Prospect, client: httpx.AsyncClient, settings: Settings, site_web: str | None
) -> Contacts | None:
    """Crawl du site (rendu JS) via Crawl4AI. Dégrade proprement si non installé
    (`crawl4ai-setup` non fait) — la cascade continue sans lui."""
    if not site_web:
        return None
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        logger.info("crawl4ai non installé — résolveur ignoré")
        return None
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=site_web)
        html = getattr(result, "html", None) or getattr(result, "cleaned_html", "") or ""
    except Exception as exc:
        logger.warning("crawl4ai KO (%s) : %s", site_web, exc)
        return None
    emails, phones = _extract_from_html(html, source_domain=_domain(site_web))
    return Contacts(emails, phones, site_web, "crawl4ai")


async def _resolve_ddg(
    prospect: Prospect, client: httpx.AsyncClient, settings: Settings, site_web: str | None
) -> Contacts | None:
    """Dernier recours : recherche DuckDuckGo (sans clé, rate-limité) puis fetch
    httpx des résultats, en filtrant les emails sur le domaine de chaque page."""
    query = f"{prospect.nom_entreprise} {prospect.ville or ''}".strip()

    def _search() -> list[str]:
        from ddgs import DDGS
        with DDGS() as ddgs:
            return [r.get("href") for r in ddgs.text(query, max_results=3)]

    try:
        urls = await asyncio.to_thread(_search)
    except Exception as exc:
        logger.info("ddgs KO (%s) : %s", prospect.siret, exc)
        return None

    emails: list[str] = []
    phones: list[str] = []
    site = site_web
    for url in [u for u in urls if u][:2]:
        domain = _domain(url)
        if not _name_matches_domain(prospect.nom_entreprise, domain):
            continue
        site = site or url
        try:
            resp = await client.get(url, timeout=15.0, follow_redirects=True)
            e, p = _extract_from_html(resp.text, source_domain=domain)
            emails += e
            phones += p
        except Exception:
            continue
        await asyncio.sleep(1.0)  # throttle DDG
    return Contacts(emails, phones, site, "ddg")


RESOLVERS = [_resolve_tavily, _resolve_crawl4ai, _resolve_ddg]


# --- Enrichissement d'un prospect ------------------------------------------
async def _enrich_prospect(
    prospect: Prospect, client: httpx.AsyncClient, settings: Settings
) -> None:
    all_emails: list[str] = []
    all_phones: list[str] = []
    sources: list[str] = []
    site = prospect.site_web

    for resolver in RESOLVERS:
        try:
            contacts = await resolver(prospect, client, settings, site)
        except Exception as exc:  # un résolveur KO ne casse pas le prospect
            logger.warning("%s KO (%s) : %s", resolver.__name__, prospect.siret, exc)
            continue
        if contacts is None:
            continue
        all_emails += contacts.emails
        all_phones += contacts.phones
        sources.append(contacts.source)
        if contacts.site_web and not site:
            site = contacts.site_web
        if all_emails and all_phones:  # email + tél trouvés → stop
            break

    all_emails = list(dict.fromkeys(all_emails))[:MAX_RAW]
    all_phones = list(dict.fromkeys(all_phones))[:MAX_RAW]

    # Politique #10 conservée : validators (email générique → None) via les
    # helpers réutilisés. On garde le 1er contact valide.
    if prospect.email is None:
        for raw in all_emails:
            cleaned = _clean_email(raw)
            if cleaned:
                prospect.email = cleaned
                break
    if prospect.telephone is None:
        for raw in all_phones:
            norm = _normalize_phone(raw)
            if norm:
                prospect.telephone = norm
                break
    if site and not prospect.site_web:
        prospect.site_web = site

    # Terrain de test pour le réalignement RGPD : on garde TOUT le brut trouvé
    # (y compris les emails génériques que la politique #10 a mis à None).
    prospect.raw_data = {
        **(prospect.raw_data or {}),
        "enrichissement": {
            "emails": all_emails,
            "phones_raw": all_phones,
            "site_web": site,
            "sources": sources,
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }


# --- Node -------------------------------------------------------------------
async def enrichissement_node(state: EtatAgent, batch_size: int = BATCH_SIZE) -> EtatAgent:
    """Enrichit `state['prospects']` en tél/email via la cascade. Batch parallèle."""
    prospects: list[Prospect] = state.get("prospects", [])
    if not prospects:
        return state
    settings = get_settings()
    semaphore = asyncio.Semaphore(batch_size)

    async with httpx.AsyncClient(timeout=20.0) as client:
        async def _one(prospect: Prospect) -> None:
            async with semaphore:
                await _enrich_prospect(prospect, client, settings)

        await asyncio.gather(*(_one(p) for p in prospects))

    with_email = sum(1 for p in prospects if p.email)
    with_phone = sum(1 for p in prospects if p.telephone)
    total = len(prospects)
    logger.info(
        "enrichissement : email %d/%d (%.0f%%), tél %d/%d (%.0f%%)",
        with_email, total, 100 * with_email / total,
        with_phone, total, 100 * with_phone / total,
    )
    state["prospects"] = prospects
    return state
