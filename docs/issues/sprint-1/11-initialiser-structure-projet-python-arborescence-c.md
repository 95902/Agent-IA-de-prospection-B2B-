---
baseline_commit: 3eb08372517f732d7ef43c15c3a31c18ec86121c
---

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
- [x] `main.py` — CLI argparse, point d'entrée (implémenté en détail dans #29)
- [x] `requirements.txt`, `.env.example`, `Makefile`
- [x] `config/` — `settings.py` (Pydantic Settings depuis `.env`), `icp_seed_example.py`
- [x] `agents/` — `sirene_agent.py`, `enrichissement_agent.py`, `nettoyage_agent.py`, `scoring_agent.py`
- [x] `graph/` — `workflow.py`, `state.py`
- [x] `models/` — `prospect.py`, `score.py`
- [x] `utils/` — `db.py`, `embeddings.py`, `bloctel.py`, `dropcontact.py`, `airtable_sync.py`, `logger.py`
- [x] `prompts/` — `scorer_system.txt.j2`, `scorer_user.txt.j2`
- [x] `scripts/` — `smoke_test.py`, `init_icp.py`, `run_campagne.sh`, `rapport_hebdo.py`
- [x] `tests/` — `test_models.py`, `test_sirene.py`, `test_scoring.py`, `test_nettoyage.py`
- [x] `docker/postgres/init/`, `docker/qdrant/`

## Contraintes
- Chaque fichier créé à ce stade peut être un stub (docstring + `pass`/`TODO`), l'implémentation réelle est portée par les issues dédiées
- Ne pas anticiper de code métier ici — cette issue ne fait que poser la structure

## Critères d'acceptance
- [x] `python main.py --help` fonctionne (même en stub)
- [x] `pip install -r requirements.txt` sans erreur
- [x] Tous les imports inter-modules se résolvent (pas d'`ImportError`)

---

## Dev Agent Record

### Implementation Plan
Issue de pure structure (1 pt) : poser l'arborescence Python avant que les autres
issues du Sprint 1 n'écrivent du code, pour éviter les conflits. Tous les fichiers
métier sont des **stubs** (`docstring` + `NotImplementedError`/`pass`/`TODO`) — aucune
logique métier introduite ici (conforme à la contrainte « Ne pas anticiper de code
métier »).

État préexistant (issues #8 embeddings + #9 db + #6 docker + #7 schéma SQL) — déjà
présents et **non réécrits** : `requirements.txt`, `.env.example`, `Makefile`,
`config/{__init__,settings}.py`, `utils/{__init__,db,embeddings}.py`,
`docker/postgres/init/01_schema.sql`, `docker/qdrant/config.yaml`,
`docker/ollama/entrypoint.sh`.

Approche :
1. Stubs créés pour tous les modules manquants (`agents/`, `graph/`, `models/`,
   `utils/{bloctel,dropcontact,airtable_sync,logger}.py`, `config/icp_seed_example.py`,
   `prompts/*.txt.j2`, `scripts/*`).
2. `main.py` : CLI argparse **fonctionnel** (sous-commandes `run`, `init-icp`, `smoke`)
   avec dispatcher stub — AC #1 exige `--help` opérationnel.
3. Tests de structure (`tests/test_structure.py`) : import de tous les modules
   inter-modules (AC #3), `main.py --help`, présence des templates Jinja, fins de
   ligne LF sur `run_campagne.sh` (piège CRLF docker documenté dans CLAUDE.md).
4. Tests stub métier (`test_models.py`, `test_sirene.py`, `test_scoring.py`,
   `test_nettoyage.py`) : valident l'état actuel (stubs = `NotImplementedError` /
   `BaseModel`) sans réclamer l'implémentation future.

### Debug Log
- `python main.py --help` crashait sur console Windows cp1252 (UnicodeEncodeError sur
  `→` flèche / accents français) → fix : `_force_utf8_stdio()` reconfigure stdout/stderr
  en UTF-8 (`errors="replace"`) au démarrage de `main()`.
- 5 tests stub initialement marqués `xfail` mais passaient (`xpassed`) → status
  malhonnête. Réécrits pour assumer l'état stub réel (assert `NotImplementedError` /
  `BaseModel`).
- `pytest.mark.integration` non enregistré → `conftest.py` ajoute le marker et skippe
  les tests d'intégration par défaut (CLAUDE.md : exclus des runs par défaut),
  activables via `pytest -m integration`.
- `pytest.mark.asyncio` évité (plugin non installé) → `asyncio.run()` dans les tests
  stub async.

### Completion Notes
- ✅ AC #1 : `python main.py --help` fonctionne (UTF-8 forcé sur Windows cp1252).
- ✅ AC #2 : `pip install -r requirements.txt` sans erreur (asyncpg, qdrant-client,
  httpx, pydantic, pydantic-settings installés).
- ✅ AC #3 : 25 modules inter-modules s'importent sans `ImportError`
  (`tests/test_structure.py::test_module_imports` paramétré).
- Suite de tests : **37 passed, 2 skipped** (2 skipped = tests d'intégration Sirene
  par défaut ; `pytest -m integration` → 2 passed).
- Aucun ICP codé en dur (règle #3 respectée) : `config/icp_seed_example.py` est un
  exemple illustratif non utilisé en prod ; l'ICP réel vient de `criteres_ciblage` /
  `icp_profiles` en base.
- Aucune dépendance ajoutée au-delà de `requirements.txt` existant (pas de nouvelle
  dépendance à approuver).
- `scripts/run_campagne.sh` en LF (pas de CRLF) — conforme `.gitattributes` / piège
  docker documenté.

## File List

Fichiers **créés** (stubs #11) :
- `main.py` — CLI argparse fonctionnel (dispatcher stub, sous-commandes run/init-icp/smoke)
- `conftest.py` — config pytest (marker `integration`, skip par défaut)
- `agents/__init__.py`
- `agents/sirene_agent.py`
- `agents/enrichissement_agent.py`
- `agents/nettoyage_agent.py`
- `agents/scoring_agent.py`
- `graph/__init__.py`
- `graph/state.py` — `EtatAgent` (TypedDict stub)
- `graph/workflow.py` — `build_graph`/`run` stubs
- `models/__init__.py`
- `models/prospect.py` — `Prospect` (BaseModel stub)
- `models/score.py` — `ScoreResult` (BaseModel stub)
- `utils/bloctel.py` — `verifier_bloctel` stub
- `utils/dropcontact.py` — `enrichir_email` stub
- `utils/airtable_sync.py` — `sync_file_appel` stub
- `utils/logger.py` — `get_logger` stub
- `config/icp_seed_example.py` — exemple ICP illustratif (non utilisé en prod)
- `prompts/scorer_system.txt.j2` — template Jinja (system, rendu depuis l'ICP client)
- `prompts/scorer_user.txt.j2` — template Jinja (user, données prospect)
- `scripts/__init__.py`
- `scripts/smoke_test.py` — `main` stub
- `scripts/init_icp.py` — `main` stub (CLI argparse, issue #12)
- `scripts/run_campagne.sh` — wrapper cron stub (LF, pas CRLF)
- `scripts/rapport_hebdo.py` — `main` stub
- `tests/__init__.py`
- `tests/test_structure.py` — tests de structure #11 (imports, `main.py --help`, templates, LF)
- `tests/test_models.py` — tests stub models (BaseModel)
- `tests/test_sirene.py` — tests stub Sirene (`@pytest.mark.integration`)
- `tests/test_scoring.py` — tests stub scoring
- `tests/test_nettoyage.py` — tests stub nettoyage

Fichiers **préexistants non modifiés** (issues #6/#7/#8/#9) :
- `requirements.txt`, `.env.example`, `Makefile`, `config/settings.py`, `config/__init__.py`,
  `utils/db.py`, `utils/embeddings.py`, `utils/__init__.py`, `docker/postgres/init/01_schema.sql`,
  `docker/qdrant/config.yaml`, `docker/ollama/entrypoint.sh`

Fichiers **modifiés** (ce dev) :
- `docs/issues/sprint-1/11-initialiser-structure-projet-python-arborescence-c.md` — frontmatter
  `baseline_commit`, cases cochées, Dev Agent Record, File List, Change Log, Status

## Change Log
- 2026-08-04 : Implémentation de l'issue #11 — arborescence Python complète posée (stubs),
  CLI `main.py` fonctionnel, suite de tests de structure (37 passed / 2 integration skipped).
  Fix UTF-8 sur `main.py --help` (console Windows cp1252). Conforme règles #3 (aucun ICP codé
  en dur), #7 (Pydantic v2), #8 (async), piège CRLF docker respecté.
- 2026-08-04 : Revue de code (3 couches adversariales) — 9 findings appliqués (3 Medium, 6 Low) :
  subparsers `required=True` + stub exit 2, tests subprocess en chemin absolu + encodage UTF-8
  explicite, marker `integration` retiré de `test_sirene.py` (tests stub), `--client-id required=True`
  sur `init-icp`, retrait des `# type: ignore[no-untyped-def]` sur fonctions typées, `conftest.py`
  match exact du marker, test LF rejette tout CR, `_force_utf8_stdio` robuste (`codecs.lookup` +
  except élargi). Suite : 39 passed.

## Status
done

## Senior Developer Review (AI)

**Review date:** 2026-08-04
**Review outcome:** Approved (changes applied)
**Action items:** 9 (1 decision-needed resolved → patch, 8 patch) — all fixed
**Severity breakdown:** 3 Medium, 6 Low

### Review Findings

#### Decision-needed
- [x] [Review][Decision] `main.py` returns exit 0 for unimplemented commands; subparsers not declared `required` [main.py:41,66-77] — Résolu : appliqué maintenant (choix utilisateur #1). Subparsers `required=True`, stub retourne `2`, `run_campagne.sh` exit `2`.

#### Patch
- [x] [Review][Patch] Subprocess tests use relative `main.py`, break under non-root cwd [tests/test_structure.py:62,76] — Fix : `cwd=_REPO_ROOT` (Path absolu).
- [x] [Review][Patch] `text=True` décode stdout en cp1252 tandis que l'enfant écrit en UTF-8 [tests/test_structure.py:62,76] — Fix : `encoding="utf-8", errors="replace"`.
- [x] [Review][Patch] Marker `integration` incohérent — seul `test_sirene.py` le porte [tests/test_sirene.py:9 vs tests/test_scoring.py, tests/test_nettoyage.py] — Fix : marker retiré de `test_sirene.py` (tests stub, pas d'API). Les 3 tests tournent maintenant par défaut.
- [x] [Review][Patch] `--client-id` `required=False` sur `init-icp` [main.py:52, scripts/init_icp.py] — Fix : `required=True` sur le subparser `init-icp` et le script `init_icp.py`.
- [x] [Review][Patch] `# type: ignore[no-untyped-def]` sur des fonctions typées [agents/*.py, utils/dropcontact.py, utils/airtable_sync.py] — Fix : `# type: ignore` retiré des 6 fonctions typées.
- [x] [Review][Patch] `conftest.py` substring check matche des markers non liés [conftest.py:17,24] — Fix : `item.get_closest_marker("integration")` + tokenisation exacte de l'expression `-m`.
- [x] [Review][Patch] Test LF ne rejette que CRLF, passe le CR seul [tests/test_structure.py:120] — Fix : `assert b"\r" not in content`.
- [x] [Review][Patch] `_force_utf8_stdio` : except trop étroit + normalisation d'encodage incomplète [main.py:20-28] — Fix : `except (AttributeError, ValueError, OSError, io.UnsupportedOperation)` + `codecs.lookup(encoding).name == "utf-8"`.


