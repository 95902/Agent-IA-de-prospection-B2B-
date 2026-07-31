# #18 — Implémenter enrichissement_agent.py (Tavily+Crawl4AI+DDG)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/18
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `sprint-2`, `enrichissement`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 3 pts
**Labels :** enrichissement, sprint-2

## Objectif
Enrichir les prospects collectés (souvent sans téléphone/email dans Sirene) via une cascade de sources légales, pour atteindre les cibles PRD (≥40% téléphone, ≥20% email).

## Fichier
`agents/enrichissement_agent.py`

## Cascade de sources
- [ ] **Tavily** (source primaire, API légale)
- [ ] **Crawl4AI + Playwright** en fallback sur le site web du prospect s'il existe (`prospect.site_web`)
- [ ] **DuckDuckGo** en dernier recours

## Traitement
- [ ] Batch de 5 prospects en parallèle (`asyncio.gather`)
- [ ] Extraction via regex :
```python
RE_PHONE = r'(?:(?:\+33|0033|0)[1-9])(?:[\s.\-]?\d{2}){4}'
RE_EMAIL = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
```
- [ ] Normalisation E.164 immédiate des numéros trouvés (réutilise le validator de #10)

## Contraintes
- Sources légales uniquement (CLAUDE.md règle #2) — pas de scraping de réseaux sociaux personnels ni de bases achetées (voir `docs/LEGAL.md`)
- Respecter le quota Tavily (1000 req/mois gratuit) — logger la consommation (voir #23)

## Critères d'acceptance
- [ ] Taux d'enrichissement téléphone > 40% sur un échantillon de test
- [ ] Le fallback DuckDuckGo se déclenche bien si Tavily échoue ou quota épuisé (voir risque PRD)


