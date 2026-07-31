# #21 — Intégrer Dropcontact — enrichissement emails B2B

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/21
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `sprint-2`, `enrichissement`, `email`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 2 pts
**Labels :** enrichissement, email, sprint-2

## Objectif
Compléter l'enrichissement email (#18) via Dropcontact quand Tavily/Crawl4AI n'ont rien trouvé, en respectant les conditions de coût et de conformité RGPD (`docs/LEGAL.md`).

## Fichier
`utils/dropcontact.py`

## Flow
- [ ] `POST /batch` avec les prospects éligibles → récupération d'un `request_id`
- [ ] Polling toutes les 5s jusqu'à disponibilité du résultat (avec timeout raisonnable et gestion d'erreur)
- [ ] Upsert de l'email trouvé sur le prospect concerné

## Condition d'appel (pour maîtriser le coût — 24€/mois pour ~1000 enrichissements)
```
email IS None ET nom_dirigeant IS NOT None ET site_web IS NOT None
```

## Contraintes
- Dropcontact génère l'email algorithmiquement (prénom.nom@entreprise.fr), certifié RGPD et hébergé en Europe — ne pas appeler ce service hors de la condition ci-dessus (voir `docs/LEGAL.md`)
- Logger le nombre d'appels Dropcontact par campagne pour suivre le coût (voir #23)

## Critères d'acceptance
- [ ] Seuls les prospects respectant la condition d'appel déclenchent une requête Dropcontact
- [ ] Le taux d'enrichissement email global (Tavily + Crawl4AI + Dropcontact) atteint la cible PRD (≥20%)


