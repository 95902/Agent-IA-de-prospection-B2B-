# Deferred Work

## Deferred from: code review of 1-6-docker-compose (2026-07-31)

- Makefile portabilité Windows/PowerShell — cible réelle Linux VPS + Git Bash ; `read -p`, `column`, `date` fonctionnent en Git Bash. Documenter la cible Linux.
- Healthcheck Qdrant faible (`test -d /qdrant/storage`) — l'image qdrant ne fournit ni curl/wget/nc/python. Un fix propre nécessite une image custom ou un sidecar. Aucun consumer `depends_on` Qdrant actuellement.
- `initdb.d` exécuté au 1er init uniquement — les évolutions de schéma doivent passer par des migrations dédiées (story séparée).
- `!override` (docker-compose.prod.yml) requiert Docker Compose v2.20+ — documenter la prérequis VPS.
- Qdrant `on_disk:false` — conserve tous les vecteurs en RAM. À repasser à `true` si la collection dépasse la RAM VPS (post-MVP).
- Qdrant `max_request_size_mb:32` — les upserts batch > 32MB seraient rejetés (413). Le batching client (issues #4/#9) doit chunker en dessous.
- Backoff du pull Ollama : 3 tentatives fixes à 5s, sans timeout/jitter. Améliorer en backoff exponentiel + timeout si pull lent/hang.
- pgAdmin/Metabase sans healthcheck — outils UI hors chemin critique données, profil-gated.
- Stack dev binds 0.0.0.0 avec creds `changeme` — acceptable en local ; l'exposition prod est gérée par l'override 127.0.0.1.
- Port gRPC Qdrant 6334 exposé — utilisé par `AsyncQdrantClient` (CLAUDE.md) ; prod le lie à 127.0.0.1.
- docker-compose v1 (binaire hyphen) non supporté — l'env cible a compose v2 ; documenter.
## Deferred from: code review of spec-gh-4-modele-icp (2026-08-04)

- source_spec: `_bmad-output/implementation-artifacts/spec-gh-4-modele-icp.md`
  summary: Race condition TOCTOU sur l'upsert applicatif (`_upsert_criteres`/`_upsert_icp_profile` : SELECT-then-INSERT non atomique → doublon si exécutions parallèles).
  evidence: Le schéma `criteres_ciblage`/`icp_profiles` n'a pas de contrainte UNIQUE sur `(client_id, nom)` (spéc #4 interdit de modifier le schéma #7). Sans `ON CONFLICT` possible, deux seeds parallèles sur le même client+nom créent deux lignes. Fix propre = migration ajoutant `UNIQUE (client_id, nom)` (story séparée, hors scope #4).

- source_spec: `_bmad-output/implementation-artifacts/spec-gh-4-modele-icp.md`
  summary: `clients.contact_email` UNIQUE — collision non catchée (`asyncpg.UniqueViolationError`) si deux clients seedés avec le même email non-null.
  evidence: `icp_payload.py` n'a pas de validator `EmailStr` et `seed_icp.py` ne catche pas `UniqueViolationError`. Faible car `contact_email` est Optional et souvent None (NULLs distincts en PG). À gérer quand le front saisira de vrais contacts.

- source_spec: `_bmad-output/implementation-artifacts/spec-gh-4-modele-icp.md`
  summary: Garde-fou anti-hardcodage ne détecte pas les hardcodages dynamiques (concaténation `"4520"+"Z"`, f-string, variable externe, `list("4520Z")`).
  evidence: Limitation structurelle d'un scan AST statique sur les `ast.Constant`. C'est un garde-fou d'alerte, pas une preuve formelle. Documenté dans la docstring du test. Amélioration possible = analyse de dataflow, hors scope MVP.
