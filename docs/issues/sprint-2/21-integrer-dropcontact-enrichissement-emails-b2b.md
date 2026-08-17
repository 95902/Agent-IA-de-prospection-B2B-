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

## Flow (API réelle — spec d'origine corrigée)
- [x] `POST https://api.dropcontact.com/v1/enrich/all` (corps `{"data":[...],"siren":true}`, header `X-Access-Token`) → `request_id`
- [x] Polling `GET /v1/enrich/all/{request_id}` jusqu'à `success:true` (timeout + gestion d'erreur, jamais bloquant)
- [x] Upsert de l'email trouvé (appariement par ordre de réponse)

## Condition d'appel (corrigée — website NON requis, garde légale ajoutée)
```
email IS None  ET  nom_dirigeant IS NOT None  ET  peut_etre_contacte(p)
```
`site_web IS NOT None` retiré : jamais vrai en pratique (0 % de sites obtenus) et inutile — Dropcontact matche sans domaine. `nom_dirigeant` désormais peuplé par #67. Website envoyé s'il existe, en bonus.

## Contraintes
- **Garde légale** : n'interroger Dropcontact que pour les prospects vérifiés non opposés (`peut_etre_contacte()`) — le nettoyage #19 tourne avant. Envoyer un prospect opposé chez un enrichisseur tiers est interdit (art. R123-232).
- Pay on success : les échecs ne coûtent rien ; `budget` plafonne quand même la dépense.
- Compteurs {eligibles, soumis, emails} exposés pour le suivi de coût (#23).

## Critères d'acceptance
- [x] Seuls les prospects respectant la condition d'appel déclenchent une requête
- [x] Aucun prospect opposé (ou non vérifié) n'est soumis
- [ ] Taux email global (chaîne gratuite + Dropcontact) ≥ 20 % PRD — mesure live (ops)


