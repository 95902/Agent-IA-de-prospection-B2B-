"""Agent de scoring hybride 3 couches (règles + Claude + embeddings).

Issue #11 — squelette. **Couche 1 (règles métier, #24) implémentée ci-dessous.**
Les couches 2 (LLM Claude, #25) et 3 (embeddings, #26), l'agrégation/persistance
(#27) et l'assemblage dans le graphe (`scoring_node`, #28) suivent.

Rappels (CLAUDE.md règles #3/#4/#5/#6) :
- **Aucune valeur métier codée en dur** : NAF, effectif, mots-clés viennent tous de
  `CriteresCiblage` (l'ICP du client), jamais de constantes Python.
- Un prospect qui matche une exclusion ICP (`mots_cles_negatifs`) → score = 0 (règle #4).

Barème détaillé et échelles : `docs/SCORING.md` (couche 1).
"""
from __future__ import annotations

from datetime import date

# ⟳ RÉUTILISÉ, jamais redéfini : l'exclusion par mot entier (garde légale/business,
# règle #4) a une seule source de vérité, partagée avec le nettoyage (#19).
from agents.nettoyage_agent import _matche_exclusion
from models.criteres import CriteresCiblage
from models.prospect import Prospect


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


# --- Node d'assemblage (#28) — stub -----------------------------------------
async def scoring_node(state: dict) -> dict:
    """STUB — node de scoring hybride. Couches 2/3 + agrégation + câblage à venir
    (#25, #26, #27, #28). La couche règles ci-dessus est prête et testée (#24)."""
    raise NotImplementedError("scoring_node non assemblé — voir #28.")
