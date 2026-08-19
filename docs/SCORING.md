# SCORING.md — Système de scoring hybride (générique, piloté par l'ICP client)

> **Réconcilié le 2026-08-17 avec le code réellement livré** (Sprint 2 fusionné sur
> `main`). Le pseudocode précédent avait dérivé du modèle Pydantic et des utils réels ;
> cette version documente les signatures et échelles telles qu'elles existent en base de
> code, pour que le Sprint 3 (#24-27) code contre le vrai, pas contre le doc. Les points
> corrigés sont signalés par « **⟳ dérive corrigée** ».

## Vue d'ensemble

Le scoring combine 3 couches indépendantes pour évaluer le potentiel commercial de chaque prospect, **selon l'ICP défini par le client** (table `criteres_ciblage` / `icp_profiles`). Aucun seuil, code NAF ou mot-clé métier n'est codé en dur : tout est lu depuis la campagne en cours.

```
score_final = round(
    w_regles    × score_regles          +  # 0-100, règles Python déterministes (ICP client)
    w_llm       × score_llm             +  # 0-100, Claude API, prompt généré depuis l'ICP
    w_embedding × (score_embedding × 100)   # score_embedding est un COSINUS 0-1 → ×100 ici
)
score_final = max(0, min(100, score_final))
```

**Poids par défaut** : `w_regles = 0.35`, `w_llm = 0.45`, `w_embedding = 0.20`. Ils sont lus depuis `state["config_scoring"]` (dict `{"poids_regles", "poids_llm", "poids_embedding"}`, alimenté par `init_campagne` #16 depuis `campagnes.config_scoring` JSONB) — **par campagne, jamais globalement**. Absent → défauts ci-dessus.

> **⟳ dérive corrigée — échelle embedding.** `models.score.ScoreResult.score_embedding` est un **cosinus 0-1** (`Field(ge=0.0, le=1.0)`). On stocke le cosinus 0-1 tel quel ; le **×100 n'a lieu que dans la somme pondérée** ci-dessus. Ne jamais persister un embedding déjà ×100.

### Seuils de qualification

| Score final | Statut | Action |
|---|---|---|
| ≥ 60 | `qualifie` | Apparaît dans `file_appel` |
| 30–59 | `nouveau` | À revoir manuellement |
| < 30 | `invalide` | Exclu du pipeline |

`qualifie`, `nouveau`, `invalide` font tous partie de `models.prospect.STATUTS_PROSPECT` (CHECK de la table `prospects`).

---

## Ordre de persistance — prérequis d'architecture (#28)

> **⟳ dérive corrigée — `prospect.id` n'existe pas.** Le modèle `models.prospect.Prospect`
> **n'a pas de champ `id`** (l'UUID est généré en base). Toute la persistance du scoring a
> besoin de cet id :
>
> - `utils.db.upsert_prospect(data: dict) -> str` **retourne l'UUID** (str). Le node de
>   scoring doit donc **upserter le prospect AVANT de scorer/sauvegarder**, récupérer l'id,
>   et le porter jusqu'à `save_score` et `upsert_prospect_embedding`.
> - `save_score(prospect_id, ...)` et `upsert_prospect_embedding(prospect_id, ...)` prennent
>   cet id str, pas `prospect.id`.
>
> Décision pour l'assemblage du graphe (#28) : `… → nettoyer → upsert_prospects → scorer →
> sauver`. On score sur `(prospect, prospect_id)`.

---

## Couche 1 — Règles métier Python (poids 0.35 par défaut)

Fichier : `agents/scoring_agent.py` → `_score_regles(prospect, criteres) -> int`

`criteres` est l'objet `models.criteres.CriteresCiblage` chargé depuis `criteres_ciblage`
(injecté dans `EtatAgent`, cf. `graph/state.py`). **Aucune valeur ci-dessous n'est une
constante Python** — toutes viennent de `criteres`.

### Barème détaillé (max 100 avant pénalités)

```python
import re
from datetime import date

from agents.nettoyage_agent import _matche_exclusion  # ⟳ RÉUTILISÉ, pas redéfini (voir plus bas)
from models.criteres import CriteresCiblage
from models.prospect import Prospect


def _score_regles(prospect: Prospect, criteres: CriteresCiblage) -> int:
    score = 0

    # CONTACT (max 35) — générique, indépendant du secteur.
    if prospect.telephone:
        score += 25
    if prospect.email:                       # ⟳ email DÉJÀ nettoyé à la construction (voir §Emails)
        score += 10

    # EFFECTIF (max 20) — position dans la fourchette ICP.
    score += _score_effectif(prospect.effectif_estime, criteres.effectif_min, criteres.effectif_max)

    # ANCIENNETÉ (max 15) — seuil minimal défini par le client.
    if prospect.date_creation:
        score += _score_anciennete(prospect.date_creation, criteres.anciennete_min_ans)

    # PRÉSENCE DIGITALE (max 10) — générique.
    if prospect.site_web:
        score += 8
    if prospect.notes and "avis google" in prospect.notes.lower():
        score += 2

    # GÉOGRAPHIE (max 10) — bonus si dans les départements prioritaires.
    if prospect.departement in (criteres.departements or []):
        score += 10

    # MOTS-CLÉS POSITIFS (max 10) — signaux définis par le client.
    score += _score_mots_cles_positifs(prospect, criteres.mots_cles_positifs)

    # PÉNALITÉS
    if _matche_exclusion(prospect, criteres.mots_cles_negatifs):   # ⟳ retourne str|None → truthy = exclu
        return 0  # Exclusion ICP client (règle #4) — jamais de liste codée en dur.
    if not prospect.telephone and not prospect.email:
        score -= 20
    if criteres.codes_naf and prospect.code_naf not in criteres.codes_naf:
        score -= 30

    return max(0, min(100, score))


def _score_effectif(effectif_estime: int | None, effectif_min: int, effectif_max: int) -> int:
    """Max 20. ⟳ prend `effectif_estime` (int), PAS `effectif` (libellé texte).
    Pleins points si dans la fourchette ICP, dégressif sinon."""
    if effectif_estime is None:
        return 0
    if effectif_min <= effectif_estime <= effectif_max:
        return 20
    ecart = min(abs(effectif_estime - effectif_min), abs(effectif_estime - effectif_max))
    return 10 if ecart <= 3 else 5


def _score_anciennete(date_creation: date, anciennete_min_ans: int) -> int:
    """Max 15. Barème relatif au seuil minimal défini par le client."""
    anciennete_ans = (date.today() - date_creation).days / 365.25
    if anciennete_ans < anciennete_min_ans:
        return 0
    if anciennete_ans >= anciennete_min_ans + 7:
        return 15
    if anciennete_ans >= anciennete_min_ans + 2:
        return 10
    return 5


def _score_mots_cles_positifs(prospect: Prospect, mots_cles: list[str] | None) -> int:
    """Max 10. +5 par mot-clé positif trouvé dans les données du prospect, plafonné à 10."""
    if not mots_cles:
        return 0
    texte = f"{prospect.nom_entreprise} {prospect.libelle_naf or ''} {prospect.notes or ''}".lower()
    hits = sum(1 for mot in mots_cles if mot.lower() in texte)
    return min(hits * 5, 10)
```

### Exclusion — réutiliser `_matche_exclusion`, ne pas la redéfinir

> **⟳ dérive corrigée — `_matche_exclusion` existe déjà.** Elle vit dans
> `agents/nettoyage_agent.py` avec la signature réelle :
>
> ```python
> def _matche_exclusion(prospect: Prospect, negatifs: list[str]) -> str | None:
>     """Retourne le 1er mot-clé négatif présent en MOT ENTIER dans le nom de
>     l'entreprise (multi-mots supportés : « groupe casino »), ou None."""
> ```
>
> Elle prend le **`Prospect` entier** (pas `nom_entreprise: str`) et retourne le
> **mot-clé matché ou `None`** (pas un bool). Matching par mot entier normalisé
> (`_normalize`, sans accents), jamais par sous-chaîne — « Carrefour » n'exclut pas
> « Garage du Carrefour ». **Le scoring l'importe et fait un test de vérité** (`if
> _matche_exclusion(...)`). Aucune liste de marques/groupes en dur (règle #4).
>
> `_matche_exclusion` et `_normalize` sont « privées » à `nettoyage_agent`. Deux options
> pour #24 : (a) les importer telles quelles (le plus rapide, conforme à « ne pas
> redéfinir ») ; (b) les promouvoir dans un `utils/text.py` partagé et faire pointer
> nettoyage + scoring dessus. Option (a) recommandée pour ce jalon ; (b) si l'équipe
> préfère éviter la dépendance inter-agents.

### Emails — la politique vit dans le modèle, pas dans le scoring

> **⟳ dérive corrigée — pas de re-blacklist dans le scoring.** L'ancienne version listait
> `EMAIL_BLACKLIST_DOMAINS = ['contact@', 'info@', …]` : **faux depuis #65**. La politique
> réelle est appliquée **à la construction du `Prospect`** par `models.prospect._clean_email`
> (validator `email`), qui met `email = None` si :
>
> - domaine hors-entreprise : `EMAIL_BLACKLIST_DOMAINS = ("pagesjaunes.fr", "laposte.net",
>   "noreply.", "mairie.")` (sous-chaîne sur le **domaine** uniquement) ;
> - rôle à écarter : `EMAIL_BLACKLIST_ROLES = {"noreply", "reply", "dpo", "rgpd", "cnil",
>   "privacy", "personnelles"}` (comparé à la **partie locale tokenisée**, jamais par
>   sous-chaîne — « dupont » ne matche pas « dpo »).
>
> Les génériques **commerciales** (`contact@`, `info@`, `reservation@`, `bonjour@`,
> `reception@`…) sont **conservées** (décision équipe D1 / #65 — ~30 % des emails de la
> chaîne gratuite). Conséquence pour le scoring : quand un `Prospect` existe, `prospect.email`
> est **soit une adresse acceptable, soit `None`**. La couche règles crédite donc simplement
> `if prospect.email: score += 10`. **Ne pas re-filtrer ici.**

---

## Couche 2 — Scoring LLM Claude (poids 0.45 par défaut)

Fichier : `agents/scoring_agent.py` → `_score_llm(...)`, templates
`prompts/scorer_system.txt.j2` + `prompts/scorer_user.txt.j2` (aujourd'hui des **stubs**
à compléter en #25).

**API Claude UNIQUEMENT** (règle #6 — pas d'OpenRouter ni de passerelle tierce : surface
RGPD/DPA sur des PII prospects). **Async** (règle #8) : `AsyncAnthropic`.

### Modèle — configurable, jamais codé en dur

`settings.claude_scoring_model` (défaut **`claude-haiku-4-5`**, acté ; #32 ré-arbitre Haiku
vs Sonnet). Jamais écrit dans le prompt.

> **⚠️ Le code doit rester agnostique du modèle** — c'est le piège n°1 de #25. Les
> paramètres n'ont pas la même validité selon le modèle configuré :
>
> | Paramètre | Haiku 4.5 | Sonnet 5 |
> |---|---|---|
> | `output_config.effort` | **erreur** | OK (`low`…`max`) |
> | `temperature` / `top_p` | OK | **400** |
> | `thinking` adaptatif | non supporté | OK |
> | `output_config.format` (sortie structurée) | **OK** | **OK** |
> | `cache_control` system | OK (min **4096** tok) | OK (min **1024** tok) |
>
> → **Ne fixer NI `effort`, NI `temperature`/`top_p`, NI `thinking`.** S'appuyer sur les
> défauts + la **sortie structurée** (`output_config.format`), valide sur les deux modèles.
> C'est suffisamment déterministe pour une classification bornée.

### Prompts — rendus dynamiquement depuis l'ICP (Jinja2)

Les stubs actuels utilisent des **variables plates** (pas des objets `client.`/`prospect.`) —
respecter ce contrat en #25 :

- `scorer_system.txt.j2` reçoit : `client_nom`, `description_icp`, `codes_naf`,
  `effectif_min`, `effectif_max`, `mots_cles_positifs`, `mots_cles_negatifs`.
- `scorer_user.txt.j2` reçoit : `nom_entreprise`, `siret`, `code_naf`, `libelle_naf`,
  `effectif_estime`, `ville`, `departement`, `site_web`, `mots_cles_detectes`.

Le **system varie par campagne** (pas par prospect) : le rendre **une fois par campagne** et
le réutiliser pour chaque prospect (candidat au cache, cf. ci-dessous). Le user est rendu par
prospect. À compléter dans les templates : les instructions de scoring + le **schéma JSON de
sortie** (aujourd'hui un `TODO` dans les stubs).

### Appel + sortie structurée + cache

```python
import json
from anthropic import AsyncAnthropic, APIConnectionError, APIStatusError, RateLimitError

from config.settings import get_settings

_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},                 # 0-100 (borne validée côté code)
        "justification": {"type": "string"},
        "signaux_positifs": {"type": "array", "items": {"type": "string"}},
        "signaux_negatifs": {"type": "array", "items": {"type": "string"}},
        "priorite": {"type": "string", "enum": ["haute", "moyenne", "basse"]},
    },
    "required": ["score", "justification", "signaux_positifs", "signaux_negatifs", "priorite"],
    "additionalProperties": False,
}

async def _score_llm(client: AsyncAnthropic, system_rendu: str, user_rendu: str,
                     score_regles_fallback: int) -> dict:
    settings = get_settings()
    try:
        resp = await client.messages.create(
            model=settings.claude_scoring_model,       # jamais codé en dur (règle #6)
            max_tokens=400,                            # score + justification courte + signaux
            system=[{                                  # rendu 1×/campagne, réutilisé par prospect
                "type": "text",
                "text": system_rendu,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_rendu}],
            output_config={"format": {"type": "json_schema", "schema": _SCORE_SCHEMA}},
            # ⚠️ NI effort, NI temperature, NI thinking — cf. tableau modèle ci-dessus.
        )
    except (RateLimitError, APIStatusError, APIConnectionError) as e:
        logger.warning("Claude indisponible (%s) — fallback score règles.", e)
        return {"score": score_regles_fallback, "justification": "Fallback règles (Claude indisponible)",
                "signaux_positifs": [], "signaux_negatifs": [], "priorite": "moyenne"}

    # output_config.format garantit un 1er bloc texte = JSON valide conforme au schéma.
    data = json.loads(next(b.text for b in resp.content if b.type == "text"))
    data["score"] = max(0, min(100, int(data["score"])))   # borne (le schéma ne l'impose pas)
    return data
```

> **⚠️ Cache : ne pas promettre 90 %.** Le minimum cacheable est **4096 tokens sur Haiku 4.5**
> (1024 sur Sonnet 5). Un system d'ICP court **ne se mettra pas en cache** (échec silencieux :
> `cache_creation_input_tokens = 0`). **Vérifier `resp.usage.cache_read_input_tokens`** avant
> d'annoncer une économie. Le `cache_control` reste posé (bénéfice réel quand l'ICP est long),
> mais l'économie n'est pas garantie pour tous les clients.
>
> **⟳ dérive corrigée — plus de regex.** L'ancien `_parse_score_llm` (regex + `json.loads` +
> assertions) est remplacé par `output_config.format` : plus robuste, supporté Haiku 4.5 et
> Sonnet 5. Le schéma JSON **ne peut pas** contraindre la longueur (`minLength` non supporté) →
> si une justification minimale est requise, la valider côté code (ou l'abandonner).

### Mapping vers `ScoreResult`

> **⟳ dérive corrigée — noms de champs.** La sortie LLM `justification` → `ScoreResult.
> justification_llm` (le modèle Pydantic utilise `justification_llm`, pas `justification`).
> `score` → `score_llm` ; `signaux_positifs`/`signaux_negatifs`/`priorite` mappent tels quels
> (`priorite` ∈ `{"haute","moyenne","basse"}`, cohérent avec le `Literal` du modèle).

### Fallback si Claude down

Déjà intégré ci-dessus : sur `RateLimitError`/`APIStatusError`/`APIConnectionError`, `score_llm
= score_regles`. Effet sur l'agrégation (poids par défaut) :
`0.35·règles + 0.45·règles + 0.20·(embedding×100) = 0.80·règles + 0.20·(embedding×100)`.

---

## Couche 3 — Similarité embeddings ICP (poids 0.20 par défaut)

Fichier : `agents/scoring_agent.py` → `_score_embedding(...)`

> **⚠️ Portée réelle de la couche (mesuré, audit #32 — 19/08/2026).** Sur une campagne
> **mono-secteur** (tous les prospects partagent le code NAF de l'ICP, ce qui est le cas par
> construction : Sirene collecte PAR NAF), le cosinus prospect↔ICP est **quasi constant** —
> mesuré 0.61–0.78 (médiane ~0.71) sur 100 hôtels réels (5510Z, dép. 75/92, Haiku 4.5). Avec
> le poids 0.20, la couche ajoute donc **~+14 points quasi identiques à TOUS les prospects** :
> elle ne **discrimine pas** à l'intérieur d'une campagne mono-secteur, elle fixe surtout un
> **plancher**. Le classement intra-campagne est piloté par les règles (0.35) et le LLM (0.45).
>
> La couche garde son intérêt pour **écarter le hors-profil** dans un lot hétérogène (ex. holdings/
> SCI enregistrées sous le NAF du secteur mais qui ne sont pas de vraies cibles) — mais le LLM
> joue déjà ce rôle et plus finement (il note ces coquilles à 0). **Ne pas attendre de la couche
> embedding qu'elle range des hôtels entre eux.** Piste : si les campagnes restent mono-secteur,
> ré-arbitrer le poids `w_embedding` (le rapprocher de 0, au profit du LLM) est défendable —
> décision **par campagne** via `campagnes.config_scoring`, jamais en dur (règle #2).

> **⟳ dérive corrigée — utils réels + cosinus Python pur.** L'ancienne version appelait
> `ollama_client.embeddings(model=…, prompt=…)` et `numpy`. La réalité :
>
> - Embedding : `utils.embeddings.get_embedding(text) -> list[float]` (async, Ollama
>   `/api/embed`, 768 dims, garde-fou dimension). **Pas de client Ollama à passer.**
> - `numpy` **n'est pas une dépendance** → cosinus en **Python pur** (dot/normes).
> - Retourne le **cosinus 0-1** (pas ×100). Le ×100 est fait à l'agrégation.
> - Vecteur ICP : `state["icp_embedding"]` (alimenté par `init_campagne` #16 via
>   `utils.db.get_icp_embedding`). Si `None` (ICP non initialisé, #12) → couche neutralisée
>   (retourner `0.0`, ne pas planter).
> - Persistance Qdrant : `utils.db.upsert_prospect_embedding(prospect_id, vector, payload)`
>   avec **l'id BDD** (str, issu de `upsert_prospect`), pas `prospect.id`.

```python
import math

from utils.db import upsert_prospect_embedding
from utils.embeddings import get_embedding


def _cosinus(a: list[float], b: list[float]) -> float:
    """Cosinus en Python pur (pas de numpy)."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


async def _score_embedding(prospect: Prospect, icp_embedding: list[float] | None,
                           prospect_id: str | None = None) -> float:
    if not icp_embedding:                     # ICP non initialisé → couche neutre
        return 0.0

    texte = (
        f"{prospect.nom_entreprise}, {prospect.libelle_naf or ''}, "
        f"{prospect.effectif_estime or '?'} salariés, {prospect.ville or ''} "
        f"({prospect.departement or ''}), créé {prospect.date_creation or '?'}, "
        f"{'site web présent' if prospect.site_web else 'pas de site web'}"
    ).strip()

    vecteur = await get_embedding(texte)      # 768 dims (Ollama CPU, gratuit)
    cos = max(0.0, _cosinus(vecteur, icp_embedding))   # borne [0, 1]

    if prospect_id:                           # id BDD (str), pas prospect.id (inexistant)
        await upsert_prospect_embedding(
            prospect_id=prospect_id,
            embedding=vecteur,
            payload={                         # cohérent avec db._PAYLOAD_INDEXES (keyword)
                "campagne_id": str(prospect.campagne_id),
                "code_naf": prospect.code_naf,
                "departement": prospect.departement,
                "nom_entreprise": prospect.nom_entreprise,
            },
        )
    return cos                                # COSINUS 0-1 (×100 seulement à l'agrégation)
```

### Profil ICP — stocké par client, jamais codé en dur

Le profil ICP vit en base, pas dans un fichier Python :

- `criteres_ciblage.description_icp` (TEXT) — description ICP en langage naturel ;
- `criteres_ciblage.{codes_naf, departements, effectif_min/max, anciennete_min_ans,
  mots_cles_positifs/negatifs, osm_tags}` — critères structurés (`models.criteres.CriteresCiblage`) ;
- vecteur ICP dans Qdrant (collection `icp_profiles`), généré par `scripts/init_icp.py`,
  récupéré via `get_icp_embedding` et injecté dans `state["icp_embedding"]`.

**Exemple illustratif** (client courtier ciblant des garages indépendants — à adapter
entièrement pour tout autre client/secteur, règle #3) :

```
description_icp = "Garage automobile indépendant, mécanicien ou carrossier, 2 à 15
                   salariés, en activité depuis au moins 3 ans. Hors réseau franchisé."
codes_naf       = ['4520Z', '4511Z', '4531Z', '4532Z']
effectif_min/max = 2 / 15 ; anciennete_min_ans = 3 ; departements = ['75','92','93','94']
mots_cles_negatifs = ['norauto', 'midas', 'speedy', 'feu vert']
osm_tags        = ['shop=car_repair']
```

---

## Agrégation finale + persistance

Fichier : `agents/scoring_agent.py` → agrégation dans le node, puis `utils.db.save_score`.

```python
from models.score import ScoreResult

# Repli seulement : la config campagne (state["config_scoring"]) prime toujours.
_POIDS_DEFAUT = {"poids_regles": 0.35, "poids_llm": 0.45, "poids_embedding": 0.20}


def _statut_pour_score(score_final: int) -> str:
    return "qualifie" if score_final >= 60 else "invalide" if score_final < 30 else "nouveau"


def _agreger(score_regles: int, score_llm: int, score_embedding: float,
             poids: dict | None = None) -> tuple[int, str]:
    p = poids or {}
    w_r = p.get("poids_regles", 0.35)
    w_l = p.get("poids_llm", 0.45)
    w_e = p.get("poids_embedding", 0.20)
    score_final = round(
        w_r * score_regles + w_l * score_llm + w_e * (score_embedding * 100)  # ×100 ICI seulement
    )
    score_final = max(0, min(100, score_final))
    return score_final, _statut_pour_score(score_final)


async def agreger_et_sauvegarder(prospect_id: str, score_regles: int, llm: dict,
                                 score_embedding: float, config_scoring: dict | None = None,
                                 *, prompt_version: str | None = None,
                                 modele_llm: str | None = None) -> ScoreResult:
    # config_scoring vient de state["config_scoring"] (chargé 1×/campagne par #16) —
    # passé par le node #28, PAS relu en base par prospect.
    score_final, statut = _agreger(score_regles, llm["score"], score_embedding, config_scoring)
    resultat = ScoreResult(
        score_regles=score_regles, score_llm=llm["score"], score_embedding=score_embedding,
        score_final=score_final, justification_llm=llm.get("justification", ""),
        signaux_positifs=list(llm.get("signaux_positifs", [])),
        signaux_negatifs=list(llm.get("signaux_negatifs", [])),
        priorite=llm.get("priorite", "moyenne"),
    )
    await save_score(prospect_id, {
        "score_regles": score_regles, "score_llm": llm["score"],
        "score_embedding": score_embedding,   # cosinus 0-1 (colonne dédiée — jamais ×100)
        "score_final": score_final, "statut": statut,
        "justification_llm": resultat.justification_llm,
        "prompt_version": prompt_version, "modele_llm": modele_llm,
        "details": {"signaux_positifs": resultat.signaux_positifs,
                    "signaux_negatifs": resultat.signaux_negatifs,
                    "priorite": resultat.priorite, "poids": config_scoring or _POIDS_DEFAUT},
    })
    return resultat
```

> **Livré en #27.** `update_prospect_score(...)` / `increment_campagne_kpi(...)` n'existent
> toujours pas — tout passe par `save_score` :
>
> - **`save_score(prospect_id, score_data)`** insère dans `scores` **ET** met à jour
>   `prospects.score_{regles,llm,embedding,final}` dans une transaction. Champs acceptés :
>   `score_regles, score_llm, score_embedding, score_final, statut, justification_llm,
>   prompt_version, modele_llm, details`.
> - ✅ **`save_score` pose désormais le `statut`** (`COALESCE`) **et incrémente
>   `campagnes.prospects_qualifies`** — mais UNIQUEMENT sur une transition vers `qualifie`
>   (ancien statut ≠ 'qualifie', ligne verrouillée `FOR UPDATE`) : l'historique `scores`
>   autorise les re-scorings, un simple +1 par scoring double-compterait.
> - Le compteur DB `campagnes.prospects_qualifies` est distinct du compteur in-run
>   `state["qualifies"]` (incrémenté par le node #28) ; il n'y a pas d'`increment_campagne_kpi`.

---

## Calibration et ajustement (par client/campagne)

Après l'audit qualité (#32), si l'accord humain/score est insuffisant pour un client :

```python
# Ajuster les poids de LA campagne concernée (jamais globalement).
config_scoring = {
    "poids_regles":    0.35,  # ↑ si les règles sont plus fiables pour ce secteur
    "poids_llm":       0.45,  # ↓ si Claude hallucine trop sur cet ICP
    "poids_embedding": 0.20,  # ↑ si la similarité ICP est particulièrement pertinente
}
# Stocké dans campagnes.config_scoring (JSONB) → chargé par init_campagne dans state["config_scoring"].
```

Suivi coût/prospect via LangSmith (#30) + `utils.metrics` (#23). Cible < 0,003 €/prospect.
