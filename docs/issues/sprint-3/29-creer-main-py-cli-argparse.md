# #29 — Créer main.py CLI argparse

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/29
> État : 🟢 Ouverte
> Sprint : Sprint 3 — Scoring & Pipeline
> Labels : `sprint-3`, `cli`

---

**Sprint :** Sprint 3 — Scoring & Pipeline (Sem. 5-6)
**Points :** 1 pt
**Labels :** cli, sprint-3

## Objectif
Fournir le point d'entrée unique du pipeline (déjà stubé en #11), qui pilote le graphe LangChain (#28) via `argparse`, paramétré par client et par campagne — jamais par des constantes en dur.

## Fichier
`main.py`

## Usage cible
```bash
python main.py --campagne-id {uuid}
python main.py --depts 75,92 --naf 4520Z --limit 200
python main.py --depts 75 --limit 10 --dry-run
python main.py --list-campagnes
```

## Comportement
- [ ] `--campagne-id` : charge une campagne existante et lance le pipeline complet
- [ ] `--depts` / `--naf` / `--limit` : mode ad hoc pour tests locaux (ne remplace pas `criteres_ciblage` en production, cf. `.env.example` — ces valeurs restent des params CLI, pas des defaults globaux)
- [ ] `--dry-run` : exécute le pipeline sans écriture en base (utile pour valider la collecte/l'enrichissement)
- [ ] `--list-campagnes` : liste les campagnes existantes avec leur statut

## Critères d'acceptance
- [ ] Les 4 usages ci-dessus fonctionnent sans erreur
- [ ] `--dry-run` ne modifie aucune table (vérifiable par un diff avant/après)
- [ ] Messages d'erreur clairs si `--campagne-id` invalide ou arguments manquants


