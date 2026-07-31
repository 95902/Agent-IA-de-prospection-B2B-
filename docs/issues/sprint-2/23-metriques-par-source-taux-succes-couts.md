# #23 — Métriques par source (taux succès + coûts)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/23
> État : 🟢 Ouverte
> Sprint : Sprint 2 — Collecte & Enrichissement
> Labels : `sprint-2`, `monitoring`

---

**Sprint :** Sprint 2 — Collecte & Enrichissement (Sem. 3-4)
**Points :** 1 pt
**Labels :** monitoring, sprint-2

## Objectif
Donner de la visibilité sur la performance et le coût de chaque source de données (Sirene, Tavily, Dropcontact, etc.), pour arbitrer plus tard (ex. ajouter Pappers si le taux d'enrichissement est insuffisant — voir risque PRD).

## Fichier
`utils/metrics.py`

## Contenu
- [ ] Fonction appelée après chaque étape de collecte/enrichissement pour incrémenter les compteurs de la table `sources` (`derniere_collecte`, `nb_prospects`)
- [ ] Métriques par source : nombre de prospects apportés, taux de succès (trouvé vs tenté), quota consommé le cas échéant (ex. Tavily 1000 req/mois)
- [ ] Log structuré (via `utils/logger.py`, Loguru) à chaque mise à jour

## Critères d'acceptance
- [ ] Après un run de campagne, la table `sources` reflète des compteurs à jour pour chaque source utilisée
- [ ] Les métriques sont consultables sans requête SQL manuelle (ex. via un script ou le futur dashboard Metabase, #37)


