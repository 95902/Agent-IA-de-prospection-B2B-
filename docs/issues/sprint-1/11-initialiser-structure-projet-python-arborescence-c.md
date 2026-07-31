# #11 — Initialiser structure projet Python (arborescence complète)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/11
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `setup`, `sprint-1`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 1 pt
**Labels :** setup, sprint-1

## Objectif
Poser l'arborescence complète du projet Python avant que les autres issues du Sprint 1 ne commencent à écrire du code, pour éviter les conflits de structure.

## Arborescence à créer
(détail complet dans `docs/ARCHITECTURE.md`)
- [ ] `main.py` — CLI argparse, point d'entrée (implémenté en détail dans #29)
- [ ] `requirements.txt`, `.env.example`, `Makefile`
- [ ] `config/` — `settings.py` (Pydantic Settings depuis `.env`), `icp_seed_example.py`
- [ ] `agents/` — `sirene_agent.py`, `enrichissement_agent.py`, `nettoyage_agent.py`, `scoring_agent.py`
- [ ] `graph/` — `workflow.py`, `state.py`
- [ ] `models/` — `prospect.py`, `score.py`
- [ ] `utils/` — `db.py`, `embeddings.py`, `bloctel.py`, `dropcontact.py`, `airtable_sync.py`, `logger.py`
- [ ] `prompts/` — `scorer_system.txt.j2`, `scorer_user.txt.j2`
- [ ] `scripts/` — `smoke_test.py`, `init_icp.py`, `run_campagne.sh`, `rapport_hebdo.py`
- [ ] `tests/` — `test_models.py`, `test_sirene.py`, `test_scoring.py`, `test_nettoyage.py`
- [ ] `docker/postgres/init/`, `docker/qdrant/`

## Contraintes
- Chaque fichier créé à ce stade peut être un stub (docstring + `pass`/`TODO`), l'implémentation réelle est portée par les issues dédiées
- Ne pas anticiper de code métier ici — cette issue ne fait que poser la structure

## Critères d'acceptance
- [ ] `python main.py --help` fonctionne (même en stub)
- [ ] `pip install -r requirements.txt` sans erreur
- [ ] Tous les imports inter-modules se résolvent (pas d'`ImportError`)


