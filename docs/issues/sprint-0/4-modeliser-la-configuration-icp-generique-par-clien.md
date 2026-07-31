# #4 — Modéliser la configuration ICP générique (par client)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/4
> État : 🟢 Ouverte
> Sprint : Sprint 0 — Conception & Design
> Labels : `sprint-0`, `conception`, `ia`, `icp`, `enattvalidation`

---

**Sprint :** Sprint 0 — Conception & Design (Sem. 0)
**Points :** 1 pts
**Labels :** ia, icp, conception, sprint-0

**Livrables :**
- Formulaire/script de saisie ICP par client : `description_icp`, `codes_naf`, `effectif_min/max`, `anciennete_min_ans`, `departements`, `mots_cles_positifs/negatifs`
- Validation qu'aucune de ces valeurs n'est codée en dur ailleurs dans le code (agents, prompts, scripts)
- Pour le client pilote : renseigner un premier ICP concret (ex. garages indépendants — codes NAF 4520Z/4511Z/4531Z/4532Z, effectif 2-15, ancienneté 3 ans) comme donnée de test, pas comme valeur par défaut du produit

Le produit n'est pas verrouillé sur un secteur : l'ICP est une configuration par client, pas du code.

