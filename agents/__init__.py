"""Agents (nodes LangChain) — pipeline de prospection B2B.

Chaque module ici est un node du graphe LangChain (issue #28) :

- `sirene_agent`        : collecte INSEE (api-sirene/3.11).
- `enrichissement_agent`: Tavily + Crawl4AI + Dropcontact.
- `nettoyage_agent`     : dédup + Bloctel + filtres (mots-clés négatifs client).
- `scoring_agent`        : scoring hybride 3 couches (règles + Claude + embeddings).

Issue #11 — STUBS. L'implémentation réelle est portée par les issues dédiées.
Aucune valeur métier (ICP) codée en dur — tout vient de la base (règle #3).
"""