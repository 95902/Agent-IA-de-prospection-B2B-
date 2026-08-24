# Relevé d'acceptance — #37, #116, #39 (clôture en review)

> Trois issues **livrées** mais restées **ouvertes** : leurs PR de livraison portaient
> `Refs #N` (et non `Closes #N`), donc GitHub ne les a jamais fermées automatiquement.
> Le **code est déjà sur `main`** (voir SHA ci-dessous) ; ce document coche, par issue,
> **ce qui l'a livrée** et **comment ça a été vérifié**. **Mesuré sur le VPS, pas déclaré.**
>
> Preuves live datées du **2026-08-24** (VPS OVH, services `prospection-api` /
> `ngrok-prospection` / conteneur `metabase`). Cette PR **clôt #37 et #116** au merge (décision
> équipe, même schéma que [`DEPLOY_ACCEPTANCE.md`](DEPLOY_ACCEPTANCE.md) / #33). **#39 est
> documentée mais volontairement gardée OUVERTE** jusqu'à la 1ʳᵉ campagne réelle de 500 (voir
> plus bas) — cette PR ne la clôt donc pas (`Refs #39`, pas `Closes`).

---

## #37 — Installer Metabase sur le VPS (dashboard KPIs)

**Livré par :** PR **#115** (`feat/metabase-prod-37`, merge `cf47b5a`) **+ la configuration
du dashboard en direct** sur l'instance.

- **Code sur `main`** : service `metabase` ajouté à `docker-compose.prod.yml` (profil
  `monitoring`, **lié à `127.0.0.1:${METABASE_PORT:-3000}`** pour rester hors du VPS malgré le
  pare-feu) + section de déploiement dans `docs/DEPLOY.md`.
- **Vérifié live (2026-08-24)** :

  | Critère | Preuve |
  |---|---|
  | Conteneur actif | `docker ps` → `prospection_b2b_metabase  Up 2 days  127.0.0.1:3000->3000/tcp` |
  | Health OK | `curl 127.0.0.1:3000/api/health` → **200** |
  | Non exposé (tunnel-only) | binding `127.0.0.1` uniquement ; accès via tunnel SSH, jamais public |
  | Dashboard configuré | admin + datasource Postgres (`host=postgres`) + dashboard **« Prospection — KPIs »**, persisté dans le volume Metabase |

**Statut : ✅ livré et opérationnel.**

---

## #116 — Intégration front ↔ back (API de données + câblage du dashboard)

**Livré par :** **#118** (front, toutes slices — merge `fe99a9b`) + **#119** (API lecture+écriture,
supersède #117 — merge `40ae581`) + **#120** (déploiement front+API via `deploy/serve.py` + ngrok
— merge `eb1cae2`).

- **Code sur `main`** (vérifié `git ls-tree origin/main`) : `api/main.py`, `deploy/serve.py`,
  `src/lib/api.ts`, `docs/DEPLOY_FRONT_NGROK.md`.
- **Vérifié live (2026-08-24)** :

  | Critère | Preuve |
  |---|---|
  | Services systemd actifs | `systemctl is-active prospection-api ngrok-prospection` → **active / active** |
  | API santé | `curl 127.0.0.1:8000/health` → **200** |
  | Front servi same-origin | `curl 127.0.0.1:8000/` → **200** (SPA `dist/` servie par FastAPI) |
  | Données réelles câblées | `curl 127.0.0.1:8000/api/kpis` → `{"collectes":400,"qualifies":37,"score_moy_qualifies":67.9,...}` (BDD prod, pas des mocks) |
  | Accès public gardé | URL ngrok → **302** `idp.ngrok.com/oauth2/authn` (Google OAuth + allowlist email) |

**Statut : ✅ intégration complète (lecture + écriture), vérifiée en direct.**
*(Restent volontairement mock, hors périmètre #116 : onboarding workspace, pages Support/Info/Paramètres.)*

---

## #39 — Rétrospective MVP + plan Phase 2

**Livré par :** PR **#124** (`docs/retrospective-mvp-39`, merge `7472c7d`).

- **Code sur `main`** : `docs/RETROSPECTIVE_MVP.md` (vérifié `git ls-tree origin/main`).
- **Contenu** : rétrospective mesurée du MVP — dont le constat central que la pré-passe
  **OSM n'a jamais tourné en prod** (`osm_tags` vide sur les 3 campagnes) et que le compteur de
  qualifiés s'érode (`POST /outcome` mute `statut`, mais les KPI comptent `statut='qualifie'`) —
  et le **plan Phase 2** priorisé.

**Statut : ✅ rétrospective livrée — 🔶 issue #39 volontairement gardée OUVERTE.**
> **Pourquoi ne pas fermer #39 maintenant** : la rétro mesure une **config dégradée** (OSM éteint
> sur les 3 campagnes — `osm_tags` vide) ; ses conclusions et le **plan Phase 2** ne seront
> **validés qu'après la 1ʳᵉ vraie campagne de 500** (#35, OSM activé, à partir du 1ᵉʳ sept). On
> garde donc **#39 comme point d'ancrage** — la fermer une fois le premier run réel mesuré **et**
> le §8 ratifié en équipe. Cette PR **documente** la livraison de la rétro sans la clôturer.
>
> Les **actions correctives** identifiées (allumer `osm_tags`, compter les qualifiés par
> `score_final ≥ 60`, écrire de vraies lignes `appels`) sont suivies en Phase 2 / #35.

---

## Portée

- **Document uniquement**, base `main`, PR autonome (une PR = une base `main`).
- `Closes #37`, `Closes #116` **au merge** (décision équipe — ne pas fermer avant review).
- **`Refs #39`** seulement : #39 **reste ouverte** jusqu'à la 1ʳᵉ campagne réelle de 500 (#35) — à re-clôturer après le premier run mesuré + ratification du §8.
- Hors périmètre, suivis ailleurs : #38 (cron rapport hebdo, PR dédiée), #34 (cron campagne, gaté crédits), #35 (1ʳᵉ campagne réelle).
