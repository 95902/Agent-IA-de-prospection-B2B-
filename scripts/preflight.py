"""Préflight des API payantes — À LANCER AVANT un run de campagne (#garde-fou).

Contexte : un run de 500 a tourné avec une clé Anthropic **expirée** → chaque scoring
a basculé en repli règles-only *sans erreur pipeline* (« 0 erreur » ≠ « a marché »).
Ce script sonde les trois API externes du pipeline et **sort en code ≠ 0** si l'une
d'elles est cassée, pour qu'un lanceur (`run_campagne.sh`) refuse de démarrer un run
qui produirait des données dégradées.

Sondes (coût négligeable : 1 appel Claude minuscule + 1 recherche Tavily + 1 requête Sirene) :
  - Anthropic (scoring #25)         — 1 message Haiku ; 401 = clé invalide.
  - Tavily (enrichissement #18)     — 1 search ; 432 = quota épuisé, 401 = clé invalide.
  - INSEE Sirene (collecte #15)     — 1 /siret ; 200/404 = OK, 401 = clé invalide.

Usage :
    PYTHONPATH=. .venv/bin/python scripts/preflight.py        # → exit 0 si tout OK, 1 sinon
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_TAVILY_URL = "https://api.tavily.com/search"
_INSEE_SIRET = "https://api.insee.fr/api-sirene/3.11/siret"


def _probe_anthropic(s) -> tuple[str, bool, str]:
    name = "Anthropic (scoring)"
    if not s.anthropic_api_key:
        return name, False, "clé absente (.env ANTHROPIC_API_KEY)"
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=s.anthropic_api_key)
        r = c.messages.create(
            model=s.claude_scoring_model, max_tokens=5,
            messages=[{"role": "user", "content": "ping"}])
        _ = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
        return name, True, f"200 · {s.claude_scoring_model} · in={r.usage.input_tokens}"
    except Exception as e:  # anthropic.AuthenticationError -> 401
        cls = type(e).__name__
        if "Authentication" in cls or "401" in str(e):
            return name, False, "401 — clé invalide/expirée"
        return name, False, f"{cls}: {str(e)[:70]}"


def _probe_tavily(s) -> tuple[str, bool, str]:
    name = "Tavily (enrichissement)"
    if not s.tavily_api_key:
        return name, False, "clé absente (.env TAVILY_API_KEY)"
    try:
        import httpx
        r = httpx.post(_TAVILY_URL,
                       headers={"Authorization": f"Bearer {s.tavily_api_key}"},
                       json={"query": "preflight", "max_results": 1}, timeout=25)
        if r.status_code == 200:
            return name, True, "200 OK — quota dispo"
        if r.status_code == 432:
            return name, False, "432 — quota mensuel épuisé"
        if r.status_code in (401, 403):
            return name, False, f"{r.status_code} — clé invalide"
        return name, False, f"{r.status_code} — {r.text[:60]}"
    except Exception as e:
        return name, False, f"{type(e).__name__}: {str(e)[:70]}"


def _probe_insee(s) -> tuple[str, bool, str]:
    name = "INSEE Sirene (collecte)"
    if not s.insee_api_key:
        return name, False, "clé absente (.env INSEE_API_KEY)"
    try:
        import httpx
        r = httpx.get(_INSEE_SIRET,
                      params={"q": "activitePrincipaleUniteLegale:55.10Z", "nombre": 1},
                      headers={"X-INSEE-Api-Key-Integration": s.insee_api_key,
                               "Accept": "application/json"}, timeout=25)
        if r.status_code in (200, 404):  # 404 = requête valide sans match → auth OK
            return name, True, f"{r.status_code} — auth OK"
        if r.status_code in (401, 403):
            return name, False, f"{r.status_code} — clé invalide"
        if r.status_code == 429:
            return name, True, "429 — rate-limit (clé OK)"
        return name, False, f"{r.status_code} — {r.text[:60]}"
    except Exception as e:
        return name, False, f"{type(e).__name__}: {str(e)[:70]}"


def main() -> int:
    from config.settings import get_settings
    s = get_settings()
    results = [_probe_anthropic(s), _probe_tavily(s), _probe_insee(s)]

    print("Préflight API payantes — avant run  (coût : ~qq tokens + 1 Tavily + 1 Sirene)")
    print("-" * 66)
    all_ok = True
    for nm, ok, detail in results:
        print(f"  [{'OK  ' if ok else 'FAIL'}] {nm:<26} {detail}")
        all_ok = all_ok and ok
    print("-" * 66)
    if all_ok:
        print("✓ Les 3 API payantes répondent — run autorisé.")
        return 0
    print("✗ PRÉFLIGHT ÉCHOUÉ — corrige la/les clé(s) ci-dessus AVANT de lancer un run.")
    print("  (un run malgré ça produirait des données dégradées, sans erreur visible)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
