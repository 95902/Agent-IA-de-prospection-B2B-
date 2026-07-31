# #16 — Node init_campagne — charger critères depuis BDD

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/16
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `database`, `collecte`, `sprint-2`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 2 pts
**Labels :** collecte, database, sprint-2

## Objectif
Premier node du graphe LangChain (#28) : charger, pour une campagne donnée, les critères de ciblage du client depuis la BDD, afin qu'aucune valeur ICP ne soit jamais codée en dur dans les nodes suivants (collecte Sirene #15, nettoyage #19, scoring #24-26).

## Fichier
`graph/workflow.py` (premiers nodes du graphe)

## Implémentation
- [ ] Node `init_campagne(etat: EtatAgent) -> EtatAgent` : lit `campagnes.critere_id` puis charge la ligne `criteres_ciblage` correspondante (codes NAF, départements, effectif min/max, ancienneté min, mots-clés +/-) et le vecteur ICP associé (`icp_profiles.qdrant_point_id`)
- [ ] Peuple `EtatAgent` (#10) avec l'objet `CriteresCiblage` complet, utilisé par tous les nodes suivants
- [ ] Gestion d'erreur explicite si `campagne_id` inconnu ou `criteres_ciblage` manquant (fail fast, pas de valeurs par défaut silencieuses)

## Fixtures de test
- [ ] Fixtures SQL de test incluses : un client pilote générique + ses `criteres_ciblage` + une campagne de test — nom neutre, non lié à un secteur particulier (ne pas coder « garage » en dur dans les fixtures de test générique)

## Critères d'acceptance
- [ ] `init_campagne` retourne un `EtatAgent` avec tous les critères de la campagne correctement chargés
- [ ] Erreur claire et explicite si la campagne ou ses critères n'existent pas


