---
baseline_commit: e0ff5ca9d8025695577738bc7af015bb6dd921d1
---

# #12 — Configurer profil ICP + script init_icp.py

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/12
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `ia`, `icp`, `sprint-1`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 1 pt
**Labels :** ia, icp, sprint-1

## Objectif
Fournir le script qui génère l'embedding d'un ICP client (à partir de sa `description_icp` en langage naturel) et le stocke dans Qdrant, pour alimenter la couche 3 du scoring (#26).

## Fichiers
- [x] `config/icp_seed_example.py` — exemple illustratif pour bootstrap d'un nouveau client (ex. garages indépendants, voir SCORING.md), **pas une valeur par défaut utilisée en prod** — *déjà livré par #4 (`ICP_SEEDS`), vérifié — non modifié ici.*
- [x] `scripts/init_icp.py --client-id <uuid>` — lit `criteres_ciblage.description_icp` du client, génère l'embedding via `utils/embeddings.py` (#8), l'upsert dans la collection Qdrant `icp_profiles` et enregistre le `qdrant_point_id` sur `icp_profiles`

## Contraintes
- Un client = un ICP = une configuration (CLAUDE.md règle #3) : le script ne doit jamais écrire de valeur ICP en dur, tout vient de `criteres_ciblage`
- Doit pouvoir être ré-exécuté si le client modifie sa `description_icp` (ré-upsert, pas de doublon de point Qdrant)

## Critères d'acceptance
- [x] `python scripts/init_icp.py --client-id <uuid>` → embedding inséré dans Qdrant
- [x] La collection `icp_profiles` contient bien 1 vecteur pour ce client
- [x] Une seconde exécution pour le même client met à jour le vecteur existant plutôt que d'en créer un second

---

## Dev Agent Record

### Implementation Plan
Issue #12 : générer l'embedding ICP d'un client et le stocker dans Qdrant pour
alimenter la couche 3 du scoring (#26).

État préexistant (déjà sur main) :
- `utils/embeddings.py` (#8) : `get_embedding(text)` via Ollama nomic-embed-text
  (768 dims, règle #5).
- `utils/db.py` (#9) : `get_pg_pool`, `get_qdrant`, `ensure_collections` (crée la
  collection `icp_profiles` + index payload `client_id`/`critere_id`),
  `COLLECTION_ICP`, `get_icp_embedding`.
- `scripts/seed_icp.py` (#4) : insère `clients` + `criteres_ciblage` +
  `icp_profiles` en PG, reset `qdrant_point_id = NULL` quand la description
  change — explicitement laissé comme hook pour #12.
- `config/icp_seed_example.py` (#4) : `ICP_SEEDS` (seed pilote "garages", donnée
  de test). Déjà livré — non modifié ici.
- `tests/test_no_hardcoded_icp.py` (#4) : garde-fou anti-hardcodage ICP (règle #3).

Approche :
1. `_load_icp(conn, client_id)` : joint `icp_profiles` + `criteres_ciblage`,
   renvoie `{icp_profile_id, description, critere_id, codes_naf, departements,
   effectif_*, mots_cles_*}`. Fallback du `critere_id` si NULL sur
   `icp_profiles`.
2. `_build_icp_text(row)` : enrichit la `description` libre avec les critères
   structurés (NAF, départements, effectif, mots-clés) pour un embedding plus
   expressif. Lève `ValueError` si tout est vide (rien à embarber).
3. `_run(client_id)` : load → `embeddings.get_embedding` → `db.ensure_collections`
   → `qdrant.upsert` (id du point = `icp_profile_id` UUID PG → AC #3
   idempotence) → `UPDATE icp_profiles SET qdrant_point_id, embedding_version`.
4. `main()` : argparse `--client-id` (required), `asyncio.run` sur une seule
   loop (pool asyncpg créé ET fermé sur la même loop, cf. seed_icp.py).
5. `_force_utf8_stdio()` : fix cp1252 Windows pour `--help` (accents français),
   même correction que main.py (#11).

### Debug Log
- `SyntaxError: ) from exc` sur un `print(...)` — `from exc` ne marche qu'avec
  `raise`, pas `print`. Corrigé en supprimant le `from exc`.
- Test `test_main_invalid_uuid_exits_nonzero` attendait `SystemExit` mais le
  contrat réel (et correct) est que `_run` retourne 2 → `main` retourne 2 (pas
  de SystemExit). Test corrigé pour assumer le vrai contrat (`rc == 2`).
- `python scripts/init_icp.py --help` crashait sur console cp1252 Windows
  (UnicodeEncodeError sur les accents) → ajout de `_force_utf8_stdio()` (même
  fix que #11, `codecs.lookup` + `except` large).

### Completion Notes
- ✅ AC #1 : `python scripts/init_icp.py --client-id <uuid>` → embedding inséré
  dans Qdrant (upsert collection `icp_profiles`). Validé par test mocké
  (`test_run_end_to_end_embeds_and_upserts_and_updates_pg`) — l'orchestration
  complète (load → embed → ensure_collections → upsert Qdrant → update PG) est
  couverte. L'appel réel nécessite PG + Ollama live (test d'intégration à
  activer quand la stack Docker tourne).
- ✅ AC #2 : 1 vecteur par client — l'upsert Qdrant insère exactement 1
  `PointStruct` (id = `icp_profile_id`).
- ✅ AC #3 : idempotence — le point Qdrant utilise `icp_profiles.id` (UUID PG)
  comme id de point. Une 2e exécution upsert le MÊME id (pas de doublon). Validé
  par `test_run_idempotent_reuses_same_qdrant_point_id` (2 runs → même
  `point_id`).
- Contrainte #3 respectée : aucune valeur ICP codée en dur dans le script. Le
  garde-fou `test_no_hardcoded_icp.py` passe (vérifié).
- `--help` fonctionne (exit 0) avec accents UTF-8 sur console Windows cp1252.
- Suite : **65 passed**, 0 regression. 7 nouveaux tests (`test_init_icp.py`).
- Aucune dépendance ajoutée (réutilise `utils/embeddings.py` + `utils/db.py`).
- Note : les tests d'intégration (vraie DB + Ollama) ne sont pas marqués
  `@pytest.mark.integration` ici car la logique est entièrement mockée — un
  test d'intégration end-to-end live pourra être ajouté quand la stack Docker
  tournera en CI.

## File List

Fichiers **créés** :
- `tests/test_init_icp.py` — 7 tests unitaires (build_icp_text, orchestration
  mockée, idempotence AC #3, client introuvable, UUID invalide)

Fichiers **modifiés** :
- `scripts/init_icp.py` — implémentation réelle (remplace le stub #11) :
  `_load_icp`, `_build_icp_text`, `_run`, `_force_utf8_stdio`, `main`
- `docs/issues/sprint-1/12-configurer-profil-icp-script-init-icp-py.md` —
  frontmatter `baseline_commit`, cases cochées, Dev Agent Record, File List,
  Change Log, Status

## Change Log
- 2026-08-04 : Implémentation de l'issue #12 — `scripts/init_icp.py` génère
  l'embedding ICP d'un client (description + critères structurés) via Ollama
  nomic-embed-text, l'upsert dans Qdrant (collection `icp_profiles`) avec id =
  `icp_profile_id` (idempotence AC #3), et enregistre `qdrant_point_id` +
  `embedding_version` en PG. Fix UTF-8 sur `--help` (cp1252 Windows). 7 tests
  unitaires (mocks), 65 passed au total. Conforme règles #3 (aucun ICP codé en
  dur), #5 (embeddings locaux CPU), #7 (Pydantic via IcpPayload #4), #8 (async).
- 2026-08-04 : Revue de code (3 couches adversariales) — 7 patches appliqués
  (1 High, 5 Medium, 1 Low) : LEFT JOIN + ORDER BY subquery + COALESCE
  description (honore spec), `cc.id AS critere_id` (payload correct), point id
  coercé en str, gestion drift Qdrant/PG (log + exit 2), Ollama down → exit 2
  propre, `_as_list` contre JSONB scalaire (anti-corruption embedding),
  `_embedding_version()` mis en cache local. 3 tests ajoutés pour les fixes
  clés. 3 findings différés (concurrence, versionning ICP, robustesse emoji
  Windows). Suite : 68 passed.

## Status
done

## Senior Developer Review (AI)

**Review date:** 2026-08-04
**Review outcome:** Approved (changes applied)
**Action items:** 11 (1 decision-needed résolu, 7 patch appliqués, 3 defer)
**Severity breakdown:** 1 High, 5 Medium, 5 Low

### Review Findings

#### Decision-needed
- [x] [Review][Decision] `finally: await db.close()` ferme le singleton pool+Qdrant à chaque run [scripts/init_icp.py:213-215] — Résolu : choix utilisateur #1 (garder `db.close()` en finally, pattern CLI one-shot cohérent avec `seed_icp.py` #4). Aucune modification.

#### Patch
- [x] [Review][Patch] INNER JOIN + subquery sans ORDER BY + description source != spec [scripts/init_icp.py:106-131] — Fix : LEFT JOIN + `ORDER BY created_at DESC` dans la subquery fallback + `COALESCE(icp.description, cc.description_icp) AS description` (honore le spec et le docstring).
- [x] [Review][Patch] payload `critere_id` enregistre `icp.critere_id` (NULL) au lieu du critère résolu [scripts/init_icp.py:111,185] — Fix : `cc.id AS critere_id` au lieu de `icp.critere_id`.
- [x] [Review][Patch] point id `uuid.UUID` non coercé en str [scripts/init_icp.py:181] — Fix : `icp_profile_id = str(row["icp_profile_id"])`.
- [x] [Review][Patch] Drift Qdrant/PG : upsert OK puis UPDATE KO → vecteur orphelin [scripts/init_icp.py:177-205] — Fix : try/except autour de l'UPDATE PG ; si échec, logge le drift (vecteur orphelin) + return 2.
- [x] [Review][Patch] Ollama down → traceback brut au lieu de exit 2 propre [scripts/init_icp.py:167] — Fix : try/except autour de `get_embedding` avec message friendly + return 2. Test `test_run_ollama_down_returns_2_with_message` couvre le fix.
- [x] [Review][Patch] `_build_icp_text` : `join` sur un string scalaire itère les caractères [scripts/init_icp.py:64,68,83,87] — Fix : helper `_as_list` qui wrap les scalaires dans une liste avant `join`. Test `test_build_icp_text_scalar_string_does_not_iterate_characters` couvre le fix.
- [x] [Review][Patch] `_embedding_version()` appelé 3× (compute une fois) [scripts/init_icp.py:204,210] — Fix : variable locale `embedding_version = _embedding_version()`, réutilisée dans l'UPDATE et les prints.

#### Defer
- [x] [Review][Defer] Concurrence : pas de `SELECT FOR UPDATE` (embed non-atomique) [scripts/init_icp.py:148-205] — différé, pré-existant à l'architecture (deux opérateurs lancent `init_icp.py` pour le même client simultanément → embed-upsert-update non-atomique, last-writer-wins sur Qdrant). Le verrouillage de ligne PG est une décision d'architecture plus large (concerne aussi `seed_icp.py`). À traiter dans une issue dédiée de concurrence, pas ce patch.
- [x] [Review][Defer] Idempotence par `icp_profile_id` : nouvelle row orpheline l'ancien point Qdrant [scripts/init_icp.py:140] — différé. Si une nouvelle row `icp_profiles` est créée (versionning) plutôt qu'update in-place, l'ancien point Qdrant (keyed par l'ancien `icp_profile_id`) n'est jamais supprimé → >1 vecteur pour le client. `seed_icp.py` (#4) fait de l'upsert applicatif (update in-place), donc ce cas ne se produit pas avec le workflow actuel. À traiter si le versionning des ICP est introduit.
- [x] [Review][Defer] Emoji `❌`/`✓` crash si `reconfigure` échoue silencieusement [scripts/init_icp.py:163,207] — différé, robustesse Windows extrême. Si `_force_utf8_stdio` ne peut pas reconfigurer (stream non reconfigurable) et que le stream reste cp1252, `print("❌ ...")` lève `UnicodeEncodeError` depuis le handler d'erreur lui-même. Le `errors="replace"` n'est appliqué qu'en cas de reconfigure réussi. Low : cas limite (redirection brisée), le path principal est couvert.

#### Dismissed (bruit / faux positifs)
- Import `from qdrant_client import models` inside `_run` — harmless : `utils/db.py` l'importe déjà en top-level, l'import local est cached et ne change rien.
- `db.close()` sur pool jamais créé dans le path UUID invalide — non-finding : l'UUID parse est dans un try séparé avant le `try` qui porte le `finally`, donc `close()` n'est pas appelé pour ce path.
- `len(embedding)` suppose une list — contract garanti par `utils/embeddings.py`.
- Test "PG unreachable" manquant — spéculatif, pas un defect actuel.


