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