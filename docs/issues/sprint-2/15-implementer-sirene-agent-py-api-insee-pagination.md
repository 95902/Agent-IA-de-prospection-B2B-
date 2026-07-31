# #15 — Implémenter sirene_agent.py — API INSEE + pagination

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/15
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `collecte`, `sirene`, `sprint-2`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 3 pts
**Labels :** collecte, sirene, sprint-2

## Objectif
Premier node de collecte du pipeline : interroger l'API Sirene INSEE pour récupérer les établissements correspondant à l'ICP de la campagne en cours (départements + codes NAF chargés par `init_campagne`, #11), et les convertir en objets `Prospect` (#5).

## Endpoint INSEE
NAF et DEPT viennent de `criteres_ciblage`, jamais codés en dur :
```
GET https://api.insee.fr/entreprises/sirene/V3.11/siret
?q=activitePrincipaleEtablissement:{NAF}
  AND codePostalEtablissement:{DEPT}*
  AND etatAdministratifEtablissement:A
&nombre=100&debut=0
```

## Fonctions
- [ ] `fetch_sirene(etat, api_key)` — node LangChain, itère sur tous les couples (département, code NAF) de l'ICP de la campagne
- [ ] `_fetch_etablissements(client, headers, dept, naf, limit)` — pagination via `debut`/`nombre`
- [ ] `_parser_etablissement(etab)` — parse la réponse JSON INSEE → `Prospect` (mapping des champs `effectif_code`/`effectif_estime`, `code_naf`, `date_creation`, adresse)

## Gestion
- [ ] Rate limit 429 → `sleep 2s` + retry (max 3 tentatives)
- [ ] Pagination automatique jusqu'à `limit` ou fin des résultats
- [ ] Respect du quota INSEE (30 req/min, voir `.env.example`)

## Contraintes
- Filtre `etatAdministratifEtablissement:A` obligatoire (établissements actifs uniquement)
- Aucun code NAF ni département codé en dur — uniquement ceux de `criteres_ciblage` de la campagne (CLAUDE.md règle #3)

## Critères d'acceptance
- [ ] 50 prospects (ICP pilote, dept. 75 en exemple) récupérés en < 30s
- [ ] 100% des SIRET retournés sont valides (14 chiffres)


