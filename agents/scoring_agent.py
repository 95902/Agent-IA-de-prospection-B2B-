"""Agent de scoring hybride 3 couches (règles + Claude + embeddings).

Issue #11 — squelette. **Les 3 couches (règles #24, LLM #25, embeddings #26) et
l'agrégation/persistance (#27) sont implémentées ci-dessous.** Seul l'assemblage
dans le graphe (`scoring_node`, #28) reste à câbler.

Rappels (CLAUDE.md règles #3/#4/#5/#6) :
- **Aucune valeur métier codée en dur** : NAF, effectif, mots-clés viennent tous de
  `CriteresCiblage` (l'ICP du client), jamais de constantes Python.
- Un prospect qui matche une exclusion ICP (`mots_cles_negatifs`) → score = 0 (règle #4).
- Embeddings **locaux sur CPU** via Ollama (règle #5) — aucune API d'embedding tierce.

Barème détaillé et échelles : `docs/SCORING.md`.
"""
from __future__ import annotations

import json
import logging
import math
from datetime import date
from pathlib import Path

import anthropic
from jinja2 import Environment, FileSystemLoader

# ⟳ RÉUTILISÉ, jamais redéfini : l'exclusion par mot entier (garde légale/business,
# règle #4) a une seule source de vérité, partagée avec le nettoyage (#19).
from agents.nettoyage_agent import _matche_exclusion
from config.settings import get_settings
from graph.state import EtatAgent
from models.criteres import CriteresCiblage
from models.prospect import Prospect
from models.score import ScoreResult
from utils.db import save_score, upsert_prospect, upsert_prospect_embedding
from utils.embeddings import get_embedding

logger = logging.getLogger(__name__)

# Observabilité LangSmith (#30) — OPTIONNELLE. `@traceable` trace l'appel Claude
# (latence, tokens, coût) quand LANGCHAIN_TRACING_V2 + une clé sont présents (config
# propagée par `utils.tracing.configure_tracing`, appelée au démarrage du pipeline).
# Import gardé : si `langsmith` n'est pas installé, le décorateur devient un no-op —
# le scoring fonctionne à l'identique, sans traçage (jamais de dépendance dure).
try:
    from langsmith import traceable
except ImportError:  # pragma: no cover - langsmith optionnel
    def traceable(*d_args, **d_kwargs):  # type: ignore[misc]
        """No-op : supporte @traceable ET @traceable(...) quand langsmith est absent."""
        if d_args and callable(d_args[0]) and not d_kwargs:
            return d_args[0]
        def _decore(fn):
            return fn
        return _decore

# Environnement Jinja des templates de prompt (rendus dynamiquement depuis l'ICP, #25).
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_JINJA_ENV = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)), autoescape=False)


# --- Couche 1 : règles métier (#24) -----------------------------------------
# Pures, déterministes, entièrement paramétrées par l'ICP client. Aucune I/O,
# aucun appel réseau : 100 % testables hors ligne.

def _score_effectif(
    effectif_estime: int | None, effectif_min: int, effectif_max: int
) -> int:
    """Max 20. Pleins points si l'effectif estimé est dans la fourchette ICP,
    dégressif au-delà. Effectif inconnu (`None`) → 0 : on ne devine pas une
    donnée absente (cohérent avec le filtre effectif du nettoyage, #19)."""
    if effectif_estime is None:
        return 0
    if effectif_min <= effectif_estime <= effectif_max:
        return 20
    ecart = min(abs(effectif_estime - effectif_min), abs(effectif_estime - effectif_max))
    return 10 if ecart <= 3 else 5


def _score_anciennete(date_creation: date, anciennete_min_ans: int) -> int:
    """Max 15. Barème relatif au seuil minimal d'ancienneté défini par le client.
    Sous le seuil → 0 ; puis paliers à +2 ans et +7 ans au-dessus du seuil."""
    anciennete_ans = (date.today() - date_creation).days / 365.25
    if anciennete_ans < anciennete_min_ans:
        return 0
    if anciennete_ans >= anciennete_min_ans + 7:
        return 15
    if anciennete_ans >= anciennete_min_ans + 2:
        return 10
    return 5


def _score_mots_cles_positifs(prospect: Prospect, mots_cles: list[str] | None) -> int:
    """Max 10. +5 par mot-clé positif de l'ICP présent dans les données du
    prospect (nom + libellé NAF + notes d'enrichissement), plafonné à 10,
    insensible à la casse."""
    if not mots_cles:
        return 0
    texte = (
        f"{prospect.nom_entreprise} "
        f"{prospect.libelle_naf or ''} "
        f"{prospect.notes or ''}"
    ).lower()
    hits = sum(1 for mot in mots_cles if mot.lower() in texte)
    return min(hits * 5, 10)


def _score_regles(prospect: Prospect, criteres: CriteresCiblage) -> int:
    """Score règles 0-100, déterministe, entièrement paramétré par l'ICP client.

    Le téléphone et l'email sont déjà normalisés/nettoyés à la construction du
    `Prospect` (validators E.164 et `_clean_email` — politique email #65 appliquée
    en amont) : on crédite simplement leur présence, sans re-filtrer ici. Un
    prospect qui matche une exclusion ICP est forcé à 0 (règle #4). Voir
    `docs/SCORING.md` (couche 1) pour le détail des sous-scores.
    """
    score = 0

    # CONTACT (max 35)
    if prospect.telephone:
        score += 25
    if prospect.email:
        score += 10

    # EFFECTIF (max 20)
    score += _score_effectif(
        prospect.effectif_estime, criteres.effectif_min, criteres.effectif_max
    )

    # ANCIENNETÉ (max 15)
    if prospect.date_creation:
        score += _score_anciennete(prospect.date_creation, criteres.anciennete_min_ans)

    # PRÉSENCE DIGITALE (max 10)
    if prospect.site_web:
        score += 8
    if prospect.notes and "avis google" in prospect.notes.lower():
        score += 2

    # GÉOGRAPHIE (max 10) — bonus si dans les départements prioritaires de l'ICP
    if prospect.departement in (criteres.departements or []):
        score += 10

    # MOTS-CLÉS POSITIFS (max 10)
    score += _score_mots_cles_positifs(prospect, criteres.mots_cles_positifs)

    # PÉNALITÉS
    if _matche_exclusion(prospect, criteres.mots_cles_negatifs):
        return 0  # exclusion ICP (règle #4) — prime sur tout le reste
    if not prospect.telephone and not prospect.email:
        score -= 20
    if criteres.codes_naf and prospect.code_naf not in criteres.codes_naf:
        score -= 30

    return max(0, min(100, score))


# --- Couche 2 : scoring LLM Claude (#25) ------------------------------------
# API Claude UNIQUEMENT (règle #6), AsyncAnthropic (règle #8). Sortie STRUCTURÉE
# (output_config.format) plutôt que parsing regex. Modèle = settings.claude_scoring_model
# (défaut Haiku 4.5), jamais codé en dur (règle #6). Code AGNOSTIQUE du modèle : on ne
# fixe NI effort, NI temperature, NI thinking (Haiku refuse effort ; Sonnet 5 refuse
# temperature/top_p) — défauts + schéma suffisent pour une classification bornée. Repli
# sur le score règles si Claude est indisponible. Voir docs/SCORING.md (couche 2).

# ⚠️ La sortie structurée ne contraint NI les bornes (minimum/maximum) NI la longueur
# (minLength) — non supportés. "score" est donc borné [0, 100] côté code.
_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "justification": {"type": "string"},
        "signaux_positifs": {"type": "array", "items": {"type": "string"}},
        "signaux_negatifs": {"type": "array", "items": {"type": "string"}},
        "priorite": {"type": "string", "enum": ["haute", "moyenne", "basse"]},
    },
    "required": [
        "score", "justification", "signaux_positifs", "signaux_negatifs", "priorite",
    ],
    "additionalProperties": False,
}


def rendre_system(criteres: CriteresCiblage, client_nom: str | None = None) -> str:
    """Rend le prompt système depuis l'ICP du client. À rendre UNE FOIS par campagne
    (candidat au cache), réutilisé pour chaque prospect. Aucune valeur métier codée
    en dur — tout vient de `criteres` (règle #3)."""
    return _JINJA_ENV.get_template("scorer_system.txt.j2").render(
        client_nom=client_nom,
        description_icp=criteres.description_icp,
        codes_naf=criteres.codes_naf,
        effectif_min=criteres.effectif_min,
        effectif_max=criteres.effectif_max,
        mots_cles_positifs=criteres.mots_cles_positifs,
        mots_cles_negatifs=criteres.mots_cles_negatifs,
    )


def rendre_user(prospect: Prospect, mots_cles_detectes: list[str] | None = None) -> str:
    """Rend le prompt utilisateur pour un prospect donné (par prospect)."""
    return _JINJA_ENV.get_template("scorer_user.txt.j2").render(
        nom_entreprise=prospect.nom_entreprise,
        siret=prospect.siret,
        code_naf=prospect.code_naf,
        libelle_naf=prospect.libelle_naf,
        effectif_estime=prospect.effectif_estime,
        ville=prospect.ville,
        departement=prospect.departement,
        site_web=prospect.site_web,
        mots_cles_detectes=mots_cles_detectes or [],
    )


def _fallback_llm(score_regles: int, raison: str) -> dict:
    """Repli déterministe quand Claude est indisponible ou sa réponse inexploitable :
    le score LLM emprunte le score règles (comportement prévu par docs/SCORING.md)."""
    return {
        "score": max(0, min(100, int(score_regles))),
        "justification": f"Repli sur le score règles ({raison}).",
        "signaux_positifs": [],
        "signaux_negatifs": [],
        "priorite": "moyenne",
    }


@traceable(run_type="llm", name="score_llm_claude")
async def _score_llm(
    client: anthropic.AsyncAnthropic,
    system_rendu: str,
    user_rendu: str,
    score_regles_fallback: int,
) -> dict:
    """Score LLM 0-100 + justification/signaux/priorité via Claude (sortie structurée).

    Renvoie un dict `{score, justification, signaux_positifs, signaux_negatifs,
    priorite}`. En cas d'indisponibilité de l'API (ou de réponse inexploitable),
    repli sur le score règles. Le mapping vers `ScoreResult` (`score` -> `score_llm`,
    `justification` -> `justification_llm`) est fait à l'agrégation (#27).
    """
    settings = get_settings()
    try:
        resp = await client.messages.create(
            model=settings.claude_scoring_model,        # jamais codé en dur (règle #6)
            max_tokens=400,
            system=[{                                    # rendu 1×/campagne, candidat au cache
                "type": "text",
                "text": system_rendu,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_rendu}],
            output_config={"format": {"type": "json_schema", "schema": _SCORE_SCHEMA}},
            # ⚠️ NI effort, NI temperature, NI thinking (agnostique du modèle — cf. en-tête).
        )
        texte = next(b.text for b in resp.content if getattr(b, "type", None) == "text")
        data = json.loads(texte)
    except anthropic.APIError as exc:                    # rate-limit / status / connexion
        logger.warning("Scoring LLM indisponible (%s) — repli sur le score règles.", exc)
        return _fallback_llm(score_regles_fallback, "Claude indisponible")
    except (StopIteration, ValueError, TypeError) as exc:  # JSON tronqué / bloc texte absent
        logger.warning("Réponse LLM inexploitable (%s) — repli sur le score règles.", exc)
        return _fallback_llm(score_regles_fallback, "réponse LLM inexploitable")

    return {
        "score": max(0, min(100, int(data.get("score", score_regles_fallback)))),
        "justification": str(data.get("justification", "")),
        "signaux_positifs": list(data.get("signaux_positifs", [])),
        "signaux_negatifs": list(data.get("signaux_negatifs", [])),
        "priorite": data.get("priorite", "moyenne"),
    }


# --- Couche 3 : similarité embeddings ICP (#26) -----------------------------
# Cosinus en Python pur (pas de numpy). Vecteur du prospect généré localement sur
# CPU via Ollama (règle #5). Renvoie un COSINUS 0-1 ; le ×100 n'a lieu qu'à
# l'agrégation (#27), cohérent avec models.score.ScoreResult.score_embedding
# (Field ge=0.0, le=1.0).

def _cosinus(a: list[float], b: list[float]) -> float:
    """Similarité cosinus entre deux vecteurs, en Python pur (pas de numpy).
    Renvoie 0.0 si l'un des vecteurs est nul (norme 0) — pas de division par zéro."""
    produit = sum(x * y for x, y in zip(a, b))
    norme_a = math.sqrt(sum(x * x for x in a))
    norme_b = math.sqrt(sum(y * y for y in b))
    if norme_a == 0.0 or norme_b == 0.0:
        return 0.0
    return produit / (norme_a * norme_b)


async def _score_embedding(
    prospect: Prospect,
    icp_embedding: list[float] | None,
    prospect_id: str | None = None,
) -> float:
    """Similarité cosinus 0-1 entre le prospect et l'ICP du client.

    `icp_embedding` vient de `EtatAgent["icp_embedding"]` (chargé par init_campagne
    #16 via `get_icp_embedding`). Absent (ICP non initialisé, #12) → couche neutre
    (`0.0`), on ne bloque pas. Le vecteur du prospect est généré localement (Ollama
    CPU, règle #5) puis, si un `prospect_id` (UUID BDD retourné par `upsert_prospect`)
    est fourni, persisté dans Qdrant. Retourne le cosinus borné à [0, 1] ; le ×100
    est fait à l'agrégation (#27).
    """
    if not icp_embedding:
        return 0.0

    texte = (
        f"{prospect.nom_entreprise}, {prospect.libelle_naf or ''}, "
        f"{prospect.effectif_estime or '?'} salariés, "
        f"{prospect.ville or ''} ({prospect.departement or ''}), "
        f"créé {prospect.date_creation or '?'}, "
        f"{'site web présent' if prospect.site_web else 'pas de site web'}"
    ).strip()

    vecteur = await get_embedding(texte)
    cosinus = max(0.0, _cosinus(vecteur, icp_embedding))

    if prospect_id:
        await upsert_prospect_embedding(
            prospect_id=prospect_id,
            embedding=vecteur,
            payload={
                "campagne_id": str(prospect.campagne_id),
                "code_naf": prospect.code_naf,
                "departement": prospect.departement,
                "nom_entreprise": prospect.nom_entreprise,
            },
        )
    return cosinus


# --- Agrégation + persistance (#27) -----------------------------------------
# Combine les 3 couches en un score final pondéré (poids PAR CAMPAGNE), en déduit
# le statut, et historise via `save_score`. Le calcul est pur et testable hors ligne.

# Poids par défaut = ceux du DEFAULT SQL de `campagnes.config_scoring`. Utilisés
# seulement en repli quand la campagne n'a pas (ou plus) de config — jamais une
# valeur métier codée en dur (règle #2) : la config campagne prime toujours.
_POIDS_DEFAUT = {"poids_regles": 0.35, "poids_llm": 0.45, "poids_embedding": 0.20}

# Seuils de statut (SCORING.md, critère d'acceptance #27) — respectés à l'unité près.
_SEUIL_QUALIFIE = 60
_SEUIL_INVALIDE = 30


def _statut_pour_score(score_final: int) -> str:
    """`qualifie` si ≥ 60, `invalide` si < 30, `nouveau` sinon (bornes exactes)."""
    if score_final >= _SEUIL_QUALIFIE:
        return "qualifie"
    if score_final < _SEUIL_INVALIDE:
        return "invalide"
    return "nouveau"


def _agreger(
    score_regles: int,
    score_llm: int,
    score_embedding: float,
    poids: dict | None = None,
) -> tuple[int, str]:
    """Score final 0-100 + statut, à partir des 3 sous-scores. Pur, déterministe.

    `score_regles`/`score_llm` sont déjà sur 0-100 ; `score_embedding` est un COSINUS
    0-1 (cf. `ScoreResult.score_embedding`) — le ×100 n'a lieu QUE dans cette somme
    pondérée, jamais dans ce qui est persisté en base. Poids manquants → repli sur
    `_POIDS_DEFAUT`, clé par clé (une config partielle reste valide)."""
    p = poids or {}
    w_regles = p.get("poids_regles", _POIDS_DEFAUT["poids_regles"])
    w_llm = p.get("poids_llm", _POIDS_DEFAUT["poids_llm"])
    w_embedding = p.get("poids_embedding", _POIDS_DEFAUT["poids_embedding"])

    brut = w_regles * score_regles + w_llm * score_llm + w_embedding * (score_embedding * 100)
    score_final = max(0, min(100, round(brut)))
    return score_final, _statut_pour_score(score_final)


async def agreger_et_sauvegarder(
    prospect_id: str,
    score_regles: int,
    llm: dict,
    score_embedding: float,
    config_scoring: dict | None = None,
    *,
    prompt_version: str | None = None,
    modele_llm: str | None = None,
) -> ScoreResult:
    """Agrège les 3 couches, persiste (historique `scores` + scores/statut courants
    du prospect + compteur qualifiés), et renvoie le `ScoreResult`.

    `llm` = dict renvoyé par `_score_llm` (`score`, `justification`, `signaux_*`,
    `priorite`). `config_scoring` = poids PAR CAMPAGNE, déjà chargés dans
    `EtatAgent["config_scoring"]` par `init_campagne` (#16) depuis
    `campagnes.config_scoring` — passés ici par le node (#28), pas re-lus en base ;
    repli sur `_POIDS_DEFAUT` si None/incomplet. NB : le vecteur du prospect est déjà
    persisté dans Qdrant par `_score_embedding` (#26) — pas de `qdrant_client` ici
    (contrairement au brouillon de l'issue). `save_score` pose le `statut` et
    incrémente `prospects_qualifies` (garde de transition)."""
    poids = config_scoring
    score_llm = llm["score"]
    score_final, statut = _agreger(score_regles, score_llm, score_embedding, poids)

    resultat = ScoreResult(
        score_regles=score_regles,
        score_llm=score_llm,
        score_embedding=score_embedding,
        score_final=score_final,
        justification_llm=llm.get("justification", ""),
        signaux_positifs=list(llm.get("signaux_positifs", [])),
        signaux_negatifs=list(llm.get("signaux_negatifs", [])),
        priorite=llm.get("priorite", "moyenne"),
    )

    await save_score(
        prospect_id,
        {
            "score_regles": score_regles,
            "score_llm": score_llm,
            "score_embedding": score_embedding,  # cosinus 0-1 — JAMAIS ×100 en base
            "score_final": score_final,
            "statut": statut,
            "justification_llm": resultat.justification_llm,
            "prompt_version": prompt_version,
            "modele_llm": modele_llm,
            "details": {
                "signaux_positifs": resultat.signaux_positifs,
                "signaux_negatifs": resultat.signaux_negatifs,
                "priorite": resultat.priorite,
                "poids": poids or _POIDS_DEFAUT,
            },
        },
    )
    return resultat


# --- Node de scoring hybride (#28) ------------------------------------------
async def scoring_node(state: EtatAgent) -> EtatAgent:
    """Score + persiste chaque prospect de `state["prospects"]`.

    Par prospect : `upsert_prospect` (→ id) → règles (#24) + LLM (#25) + embedding
    (#26) → `agreger_et_sauvegarder` (#27, persiste scores/statut + compteur BDD).
    Incrémente le compteur in-run `state["qualifies"]`.

    Robustesse (#28) :
    - **Panne Claude** : `_score_llm` bascule seul sur le score règles
      (score_final = 0.80·règles + 0.20·embedding, cf. SCORING.md) — pas d'arrêt.
    - **Échec d'UN prospect** (upsert/embedding/persistance) : loggé + ajouté à
      `state["erreurs"]`, on passe au suivant — un prospect ne fait pas échouer la campagne.

    La persistance est câblée ICI plutôt que dans un node « sauvegarder » distinct :
    `save_score` et `_score_embedding` (upsert du vecteur Qdrant) ont besoin de l'`id`
    retourné par `upsert_prospect`, indisponible avant le scoring."""
    prospects = state.get("prospects") or []
    state.setdefault("erreurs", [])
    state.setdefault("qualifies", 0)
    if not prospects:
        return state

    criteres = state["criteres"]
    icp_embedding = state.get("icp_embedding")
    config_scoring = state.get("config_scoring")
    settings = get_settings()

    # Rendu 1×/campagne (system = candidat au cache) ; un seul client Claude pour le lot.
    system_rendu = rendre_system(criteres)
    async with anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key) as client:
        for prospect in prospects:
            try:
                prospect_id = await upsert_prospect(prospect.to_db_dict())
                score_regles = _score_regles(prospect, criteres)
                user_rendu = rendre_user(prospect)
                llm = await _score_llm(
                    client, system_rendu, user_rendu, score_regles_fallback=score_regles
                )
                score_embedding = await _score_embedding(prospect, icp_embedding, prospect_id)
                resultat = await agreger_et_sauvegarder(
                    prospect_id, score_regles, llm, score_embedding, config_scoring,
                    modele_llm=settings.claude_scoring_model,
                )
                if _statut_pour_score(resultat.score_final) == "qualifie":
                    state["qualifies"] += 1
            except Exception as exc:  # un prospect en échec ne casse pas la campagne (#28)
                logger.warning(
                    "Scoring échoué pour '%s' (%s) — prospect ignoré.",
                    prospect.nom_entreprise, exc,
                )
                state["erreurs"].append(f"scoring:{prospect.nom_entreprise}:{exc}")
    return state
