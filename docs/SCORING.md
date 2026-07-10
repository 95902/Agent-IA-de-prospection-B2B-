# SCORING.md — Système de scoring hybride (générique, piloté par l'ICP client)

## Vue d'ensemble

Le scoring combine 3 couches indépendantes pour évaluer le potentiel commercial de chaque prospect, **selon l'ICP défini par le client** (table `criteres_ciblage` / `icp_profiles`). Aucun seuil, code NAF ou mot-clé métier n'est codé en dur : tout est lu depuis la campagne en cours.

```
score_final = round(
    0.35 × score_regles    +  # Règles Python déterministes, paramétrées par l'ICP client
    0.45 × score_llm       +  # Claude API, prompt généré dynamiquement depuis l'ICP client
    0.20 × score_embedding    # Similarité cosinus avec l'ICP du client via Qdrant
)
score_final = max(0, min(100, score_final))
```

### Seuils de qualification

| Score | Statut | Action |
|---|---|---|
| ≥ 60 | `qualifie` | Apparaît dans `file_appel` |
| 30–59 | `nouveau` | À revoir manuellement |
| < 30 | `invalide` | Exclu du pipeline |

---

## Couche 1 — Règles métier Python (35%)

Fichier : `agents/scoring_agent.py` → fonction `_score_regles(prospect, criteres)`

`criteres` est l'objet `CriteresCiblage` chargé depuis la table `criteres_ciblage` de la campagne en cours (voir `graph/state.py`). **Aucune valeur ci-dessous n'est une constante Python** — elles sont toutes lues depuis `criteres`.

### Barème détaillé

```python
def _score_regles(prospect: Prospect, criteres: CriteresCiblage) -> int:
    score = 0

    # CONTACT (max 35 pts) — générique, indépendant du secteur
    if prospect.telephone:
        score += 25
    if prospect.email and not _is_blacklisted_email(prospect.email):
        score += 10

    # EFFECTIF (max 20 pts) — position dans la fourchette ICP du client
    score += _score_effectif(prospect.effectif, criteres.effectif_min, criteres.effectif_max)

    # ANCIENNETÉ (max 15 pts) — seuil minimal défini par le client
    if prospect.date_creation:
        score += _score_anciennete(prospect.date_creation, criteres.anciennete_min_ans)

    # PRÉSENCE DIGITALE (max 10 pts) — générique
    if criteres.exiger_site_web is not False and prospect.site_web:
        score += 8
    if prospect.notes and "avis google" in prospect.notes.lower():
        score += 2

    # GÉOGRAPHIE (max 10 pts) — bonus si dans les départements prioritaires du client
    if prospect.departement in (criteres.departements or []):
        score += 10

    # MOTS-CLÉS POSITIFS (max 10 pts) — bonus si signaux définis par le client sont présents
    score += _score_mots_cles_positifs(prospect, criteres.mots_cles_positifs)

    # PÉNALITÉS
    if _matche_exclusion(prospect.nom_entreprise, criteres.mots_cles_negatifs):
        return 0  # Score forcé à 0 — exclusion définie par le client, jamais codée en dur
    if not prospect.telephone and not prospect.email:
        score -= 20
    if criteres.codes_naf and prospect.code_naf not in criteres.codes_naf:
        score -= 30

    return max(0, min(100, score))


def _score_effectif(effectif: int | None, effectif_min: int, effectif_max: int) -> int:
    """Max 20 pts. Pleins points si dans la fourchette ICP du client, dégressif sinon."""
    if effectif is None:
        return 0
    if effectif_min <= effectif <= effectif_max:
        return 20
    ecart = min(abs(effectif - effectif_min), abs(effectif - effectif_max))
    if ecart <= 3:
        return 10
    return 5


def _score_anciennete(date_creation: date, anciennete_min_ans: int) -> int:
    """Max 15 pts. Barème relatif au seuil minimal défini par le client."""
    anciennete_ans = (date.today() - date_creation).days / 365.25
    if anciennete_ans < anciennete_min_ans:
        return 0
    if anciennete_ans >= anciennete_min_ans + 7:
        return 15
    if anciennete_ans >= anciennete_min_ans + 2:
        return 10
    return 5


def _score_mots_cles_positifs(prospect: Prospect, mots_cles: list[str] | None) -> int:
    """Max 10 pts. +5 par mot-clé positif trouvé dans les données du prospect, plafonné à 10."""
    if not mots_cles:
        return 0
    texte = f"{prospect.nom_entreprise} {prospect.libelle_naf} {prospect.notes or ''}".lower()
    hits = sum(1 for mot in mots_cles if mot.lower() in texte)
    return min(hits * 5, 10)


def _matche_exclusion(nom_entreprise: str, mots_cles_negatifs: list[str] | None) -> bool:
    """Exclusion par mot entier (pas de sous-chaîne) pour éviter les faux positifs
    (ex: un garage "Le Carrefour Auto" ne doit pas matcher l'exclusion "Carrefour")."""
    if not mots_cles_negatifs:
        return False
    mots_prospect = set(re.findall(r"\w+", nom_entreprise.lower()))
    return any(mot.lower() in mots_prospect for mot in mots_cles_negatifs)
```

> ⚠️ **Point corrigé** : dans une version antérieure de ce document, le barème effectif définissait un dict `effectif_map` jamais appliqué au score, et utilisait une variable `anciennete` jamais calculée. Le code ci-dessus corrige les deux : `_score_effectif` et `_score_anciennete` sont des fonctions pures, testables indépendamment (voir issue #26).

### Exclusions — configurables par client, jamais codées en dur

Il n'existe **aucune liste de marques ou de groupes en dur dans le code**. Chaque client renseigne ses propres `mots_cles_negatifs` dans `criteres_ciblage` lors de la configuration de son ICP (issue #S0-4 / #7). Exemple pour un client ciblant des garages indépendants :

```
mots_cles_negatifs = ['norauto', 'midas', 'speedy', 'feu vert', 'mobivia']
```

Un client dans un autre secteur définira une liste totalement différente (ex: `['mcdonald', 'quick', 'burger king']` pour un client ciblant la restauration indépendante). Le matching se fait par **mot entier normalisé**, pas par sous-chaîne, pour éviter les faux positifs (ex: "Carrefour" ne doit pas exclure "Garage du Carrefour").

### Emails blacklistés (score email = 0) — générique, tous secteurs

```python
EMAIL_BLACKLIST_DOMAINS = [
    'pagesjaunes.fr', 'laposte.net', 'noreply.',
    'contact@', 'info@', 'mairie.'
]
```

---

## Couche 2 — Scoring LLM Claude (45%)

Fichier : `agents/scoring_agent.py` → fonction `_score_llm(prospect, criteres, client)`, template `prompts/scorer_system.txt.j2`, `prompts/scorer_user.txt.j2`

**Le prompt système n'est plus un texte figé** : il est généré dynamiquement à partir du profil du client (`clients.produit_vendu`, `clients.secteur`) et de la description ICP (`criteres_ciblage.description_icp`). Ceci permet au même agent de scorer des garages pour un courtier en assurance ou des cabinets comptables pour un éditeur SaaS RH, sans changer une ligne de code.

### Choix du modèle

Le modèle utilisé est configuré dans `config/settings.py` (variable `CLAUDE_SCORING_MODEL`), pas codé en dur dans le prompt. Pour une tâche de classification structurée (score + justification courte), `claude-haiku-4-5` est un bon point de départ coût/qualité — à arbitrer par A/B test contre un modèle plus capable si la précision de scoring l'exige (voir issue #27, audit qualité).

### Prompt système (`scorer_system.txt.j2`)

```jinja2
Tu es un expert commercial B2B. Tu évalues des prospects pour le compte de
{{ client.nom_entreprise }}, qui vend {{ client.produit_vendu }} à des
entreprises du secteur "{{ criteres.nom }}".

Profil client idéal (ICP) défini par ce client :
{{ criteres.description_icp }}

Ton rôle : évaluer le potentiel commercial de chaque prospect au regard de cet
ICP et retourner UNIQUEMENT un JSON valide, sans texte avant ou après.

Critères d'évaluation (à pondérer selon la description ICP ci-dessus) :
- Adéquation générale avec l'ICP décrit
- Taille d'entreprise adaptée (cible : {{ criteres.effectif_min }}-{{ criteres.effectif_max }} salariés)
- Ancienneté / stabilité (minimum {{ criteres.anciennete_min_ans }} ans)
- Zone géographique dans les départements ciblés
- Présence digitale pertinente pour ce secteur
- Tout signal d'activité pertinent au regard de l'ICP, même non listé explicitement
```

### Prompt utilisateur (`scorer_user.txt.j2`)

```jinja2
Évalue ce prospect :

Entreprise : {{ prospect.nom_entreprise }}
SIRET : {{ prospect.siret }}
Activité : {{ prospect.libelle_naf }} ({{ prospect.code_naf }})
Localisation : {{ prospect.ville }} ({{ prospect.departement }}, {{ prospect.code_postal }})
Effectif : {{ prospect.effectif }}
Créé le : {{ prospect.date_creation }}
Téléphone : {{ prospect.telephone }}
Email : {{ prospect.email }}
Site web : {{ prospect.site_web }}
Informations complémentaires : {{ prospect.notes }}

Retourne ce JSON exact :
{
  "score": <entier 0-100>,
  "justification": "<phrase de 20-50 mots expliquant le score au regard de l'ICP>",
  "signaux_positifs": ["<signal1>", "<signal2>"],
  "signaux_negatifs": ["<signal1>"],
  "priorite": "<haute|moyenne|basse>"
}
```

### Paramètres d'appel Claude + prompt caching

Le prompt système varie **par campagne** (pas par prospect) — c'est donc un excellent candidat au cache : des centaines de prospects d'une même campagne partagent le même system prompt rendu. Activer le cache dessus réduit son coût d'environ 90% sur tous les appels après le premier de la campagne.

```python
response = client.messages.create(
    model=settings.CLAUDE_SCORING_MODEL,  # jamais codé en dur, voir config/settings.py
    max_tokens=300,
    system=[{
        "type": "text",
        "text": system_prompt_rendu,       # rendu une fois par campagne, réutilisé pour chaque prospect
        "cache_control": {"type": "ephemeral"},
    }],
    messages=[{"role": "user", "content": user_prompt}],
)
# Coût cible : < 0.003€/prospect (surveiller via LangSmith, par client)
```

### Parsing robuste du JSON

```python
import json, re

def _parse_score_llm(response_text: str) -> dict:
    clean = re.sub(r'```json|```', '', response_text).strip()
    try:
        data = json.loads(clean)
        assert 0 <= data['score'] <= 100
        assert len(data['justification']) >= 20
        return data
    except Exception:
        return {"score": 50, "justification": "Parsing error",
                "signaux_positifs": [], "signaux_negatifs": [],
                "priorite": "moyenne"}
```

---

## Couche 3 — Similarité embeddings ICP (20%)

Fichier : `agents/scoring_agent.py` → fonction `_score_embedding(prospect)`

### Algorithme complet

```python
async def _score_embedding(
    prospect: Prospect,
    icp_embedding: list[float],   # vecteur ICP du client, chargé depuis icp_profiles
    ollama_client,
    qdrant_client
) -> float:

    # 1. Construire texte de description du prospect (générique, tous secteurs)
    texte = f"""
    {prospect.nom_entreprise}, {prospect.libelle_naf},
    {prospect.effectif} salariés, {prospect.ville} ({prospect.departement}),
    créé en {prospect.date_creation},
    {"site web présent" if prospect.site_web else "pas de site web"}
    """.strip()

    # 2. Générer embedding via Ollama (CPU, gratuit)
    response = await ollama_client.embeddings(
        model="nomic-embed-text",
        prompt=texte
    )
    prospect_embedding = response['embedding']  # 768 dims

    # 3. Calculer similarité cosinus avec l'ICP du client
    import numpy as np
    a = np.array(prospect_embedding)
    b = np.array(icp_embedding)
    similarite = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # 4. Stocker vecteur dans Qdrant
    await upsert_prospect_embedding(
        prospect_id=str(prospect.id),
        embedding=prospect_embedding,
        payload={
            "nom_entreprise": prospect.nom_entreprise,
            "code_naf": prospect.code_naf,
            "departement": prospect.departement,
            "effectif": prospect.effectif,
            "campagne_id": str(prospect.campagne_id),
            "score_final": 0  # mis à jour après agrégation
        }
    )

    # 5. Retourner score [0-100]
    return float(max(0, similarite)) * 100
```

### Profil ICP — stocké par client, pas codé en dur

Le profil ICP n'est **plus un fichier Python statique**. Il vit en base :

- `criteres_ciblage.description_icp` (TEXT) — la description ICP en langage naturel, rédigée par/avec le client
- `criteres_ciblage.codes_naf`, `.departements`, `.effectif_min/max`, `.anciennete_min_ans`, `.mots_cles_positifs/negatifs` — les critères structurés
- `icp_profiles.qdrant_point_id` — le vecteur embedding de la description ICP, généré une fois par `scripts/init_icp.py --client-id <uuid>` (voir issue #7)

**Exemple illustratif** (un client ciblant des garages indépendants pour un produit d'assurance — à adapter entièrement pour tout autre client/secteur) :

```
Exemple de description_icp saisie par un client courtier en assurance :

"Garage automobile indépendant, mécanicien ou carrossier, employant entre 2
et 15 salariés, en activité depuis au moins 3 ans. N'appartient pas à un
réseau franchisé."

codes_naf = ['4520Z', '4511Z', '4531Z', '4532Z']
effectif_min = 2, effectif_max = 15
anciennete_min_ans = 3
departements = ['75', '92', '93', '94']
mots_cles_negatifs = ['norauto', 'midas', 'speedy', 'feu vert']
```

Un autre client (ex: éditeur SaaS RH ciblant des PME industrielles) renseignerait une `description_icp`, des `codes_naf` et des `mots_cles_negatifs` complètement différents — **sans toucher au code**.

---

## Agrégation finale + persistance

```python
async def agreger_et_sauvegarder(
    prospect: Prospect,
    score_regles: int,
    score_llm: int,
    score_embedding: float,
    justification_llm: str,
    pool, qdrant_client
):
    score_final = round(
        0.35 * score_regles +
        0.45 * score_llm +
        0.20 * score_embedding
    )
    score_final = max(0, min(100, score_final))

    statut = (
        'qualifie' if score_final >= 60 else
        'invalide' if score_final < 30 else
        'nouveau'
    )

    await update_prospect_score(prospect.id, score_final, statut, pool)

    await save_score(prospect.id, {
        "score_regles": score_regles,
        "score_llm": score_llm,
        "score_embedding": score_embedding,
        "score_final": score_final,
        "justification_llm": justification_llm,
        "prompt_version": "v2.0-generique",
    }, pool)

    if statut == 'qualifie':
        await increment_campagne_kpi(prospect.campagne_id, 'prospects_qualifies', pool)
```

---

## Fallback si Claude API down

```python
async def scorer_avec_fallback(prospect, criteres, llm_client, ...):
    try:
        score_llm = await _score_llm_claude(prospect, criteres, llm_client)
    except Exception as e:
        logger.warning(f"Claude API indisponible: {e}. Fallback règles seules.")
        score_llm = score_regles  # utilise le score règles comme proxy
        # score_final = 0.35*règles + 0.45*règles + 0.20*embedding
        #             = 0.80*règles + 0.20*embedding
```

---

## Calibration et ajustement (par client/campagne)

Après l'audit qualité (issue #27), si l'accord humain/score < 75% pour un client donné :

```python
# Ajuster les poids dans la config de LA campagne concernée (pas globalement)
config_scoring = {
    "poids_regles":    0.35,  # ↑ si les règles sont plus fiables pour ce secteur
    "poids_llm":       0.45,  # ↓ si Claude hallucine trop sur cet ICP
    "poids_embedding": 0.20   # ↑ si la similarité ICP est particulièrement pertinente
}
# Stocké dans campagnes.config_scoring JSONB — par campagne, jamais globalement
```
