# #10 — Créer modèles Pydantic v2 — Prospect, Score, EtatAgent

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/10
> État : 🟢 Ouverte
> Sprint : Sprint 1 — Fondations
> Labels : `sprint-1`, `modèles`, `pydantic`

---

**Sprint :** Sprint 1 — Fondations (Sem. 1-2)
**Points :** 2 pts
**Labels :** modèles, pydantic, sprint-1

## Objectif
Modéliser en Pydantic v2 (CLAUDE.md règle #7) les structures de données centrales du pipeline : le prospect, son score, et l'état du graphe LangChain.

## Fichiers
- [ ] `models/prospect.py` — `Prospect` (BaseModel), tous les champs de la table `prospects` (voir `docs/ARCHITECTURE.md`)
- [ ] `models/score.py` — `ScoreResult` (BaseModel) : `score_regles`, `score_llm`, `score_embedding`, `score_final`, `justification_llm`, `signaux_positifs`, `signaux_negatifs`, `priorite`
- [ ] `graph/state.py` — `EtatAgent` (TypedDict) : état partagé entre les 6 nodes du graphe (#28), incluant les `CriteresCiblage` de la campagne en cours

## Validators obligatoires
- [ ] `telephone` → normalisation E.164 via la librairie `phonenumbers`
- [ ] `email` → validation regex + blacklist de domaines (`pagesjaunes.fr`, `laposte.net`, `noreply.`, `contact@`, `info@`, `mairie.` — voir SCORING.md)
- [ ] `siret` → exactement 14 chiffres, sinon `ValidationError`
- [ ] `to_db_dict()` sur `Prospect` → dict compatible `asyncpg` (types Python natifs, pas de types Pydantic)

## Critères d'acceptance
- [ ] `0612345678` → normalisé en `+33612345678`
- [ ] SIRET invalide (≠ 14 chiffres) → lève `ValidationError`
- [ ] Email sur domaine blacklisté → champ `email` mis à `None` (pas d'erreur bloquante)


