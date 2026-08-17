"""Tests de la couche règles du scoring (#24) — purs, déterministes, hors ligne.

Couvre les sous-scorers (`_score_effectif`, `_score_anciennete`,
`_score_mots_cles_positifs`) et le barème intégré `_score_regles` : crédit
contact/effectif/ancienneté/présence/géo/mots-clés, pénalités (sans contact,
NAF hors ICP), exclusion ICP forcée à 0 (règle #4), et le plafonnement 0-100.
Toutes les valeurs métier viennent de `CriteresCiblage` (règle #3). Aucun réseau.
"""
from __future__ import annotations

import asyncio
import inspect
import uuid
from datetime import date, timedelta

import pytest

from agents.scoring_agent import (
    _score_anciennete,
    _score_effectif,
    _score_mots_cles_positifs,
    _score_regles,
)
from models.criteres import CriteresCiblage
from models.prospect import Prospect

CID = uuid.uuid4()

# Valeurs qui PASSENT les validators du Prospect (sinon mises à None à la construction).
TEL_OK = "0123456789"                      # ligne fixe FR -> +33123456789
EMAIL_OK = "contact@garage-durand.fr"      # générique commerciale -> conservée (#65)


def _p(nom="Garage Durand", **o) -> Prospect:
    return Prospect(campagne_id=CID, nom_entreprise=nom, **o)


def _criteres(**o) -> CriteresCiblage:
    base = dict(nom="ICP test")
    base.update(o)
    return CriteresCiblage(**base)


def _il_y_a(annees: float) -> date:
    """Date de création située `annees` en arrière (via 365.25 j/an, comme le barème)."""
    return date.today() - timedelta(days=round(annees * 365.25))


# --- _score_effectif (max 20) -----------------------------------------------
@pytest.mark.parametrize(
    "effectif, attendu",
    [
        (8, 20),     # dans la fourchette
        (2, 20),     # borne basse
        (15, 20),    # borne haute
        (16, 10),    # ecart 1 <= 3
        (18, 10),    # ecart 3 <= 3
        (19, 5),     # ecart 4 > 3
        (0, 10),     # ecart min(|0-2|,|0-15|)=2 <= 3
        (100, 5),    # loin au-dessus de la fourchette
    ],
)
def test_score_effectif(effectif, attendu):
    assert _score_effectif(effectif, 2, 15) == attendu


def test_score_effectif_inconnu_ne_devine_pas():
    assert _score_effectif(None, 2, 15) == 0


# --- _score_anciennete (max 15), seuil ICP = 3 ans --------------------------
@pytest.mark.parametrize(
    "annees_ago, attendu",
    [
        (11, 15),    # >= min+7 (10)
        (6, 10),     # >= min+2 (5), < 10
        (3.5, 5),    # >= min (3), < 5
        (2, 0),      # < min
    ],
)
def test_score_anciennete(annees_ago, attendu):
    assert _score_anciennete(_il_y_a(annees_ago), anciennete_min_ans=3) == attendu


# --- _score_mots_cles_positifs (max 10) -------------------------------------
def test_mots_cles_none_ou_vide():
    p = _p(libelle_naf="Carrosserie")
    assert _score_mots_cles_positifs(p, None) == 0
    assert _score_mots_cles_positifs(p, []) == 0


def test_mots_cles_un_hit():
    p = _p(libelle_naf="Entretien et réparation, carrosserie")
    assert _score_mots_cles_positifs(p, ["carrosserie"]) == 5


def test_mots_cles_deux_hits():
    p = _p(libelle_naf="Carrosserie et peinture automobile")
    assert _score_mots_cles_positifs(p, ["carrosserie", "peinture"]) == 10


def test_mots_cles_plafonne_a_10():
    p = _p(nom="Carrosserie Peinture Mécanique Durand", libelle_naf="carrosserie peinture")
    assert _score_mots_cles_positifs(p, ["carrosserie", "peinture", "mécanique"]) == 10


def test_mots_cles_insensible_casse():
    p = _p(libelle_naf="CARROSSERIE")
    assert _score_mots_cles_positifs(p, ["carrosserie"]) == 5


def test_mots_cles_cherche_dans_notes():
    p = _p(libelle_naf="Réparation", notes="Signalé comme spécialiste peinture")
    assert _score_mots_cles_positifs(p, ["peinture"]) == 5


# --- _score_regles : barème intégré -----------------------------------------
def test_regles_prospect_ideal():
    """Contact + effectif + ancienneté + site + avis + géo + mot-clé = 95, sans pénalité."""
    crit = _criteres(
        codes_naf=["4520Z"], departements=["75"], effectif_min=2, effectif_max=15,
        anciennete_min_ans=3, mots_cles_positifs=["carrosserie"],
    )
    p = _p(
        code_naf="4520Z", departement="75", effectif_estime=8,
        telephone=TEL_OK, email=EMAIL_OK, site_web="https://garage-durand.fr",
        date_creation=_il_y_a(20), libelle_naf="Réparation, carrosserie",
        notes="Bien noté sur avis google",
    )
    # 25 + 10 + 20 + 15 + 8 + 2 + 10 + 5 = 95
    assert _score_regles(p, crit) == 95


def test_regles_exclusion_force_a_zero():
    """Une exclusion ICP (mot entier) prime sur un prospect par ailleurs excellent."""
    crit = _criteres(
        departements=["75"], effectif_min=2, effectif_max=15,
        mots_cles_negatifs=["durand"],
    )
    p = _p(
        nom="Garage Durand", departement="75", effectif_estime=8,
        telephone=TEL_OK, email=EMAIL_OK, site_web="https://x.fr",
    )
    assert _score_regles(p, crit) == 0


def test_regles_exclusion_mot_entier_pas_sous_chaine():
    """« durand » n'exclut pas « Durandal » (mot entier, réutilise nettoyage #19)."""
    crit = _criteres(effectif_min=2, effectif_max=15, mots_cles_negatifs=["durand"])
    p = _p(nom="Garage Durandal", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(p, crit) == 45  # 25 (tel) + 20 (effectif), pas d'exclusion


def test_regles_penalite_sans_contact():
    """Sans téléphone NI email : -20. Le contact vaut 35 + évite la pénalité."""
    crit = _criteres(effectif_min=2, effectif_max=15, departements=["75"])
    avec = _p(departement="75", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    sans = _p(departement="75", effectif_estime=8)
    assert _score_regles(avec, crit) == 65   # 35 + 20 + 10
    assert _score_regles(sans, crit) == 10   # 20 + 10 - 20


def test_regles_credit_email_isole():
    """Téléphone présent dans les deux : l'email seul vaut +10 (pas de pénalité contact)."""
    crit = _criteres(effectif_min=2, effectif_max=15)
    avec = _p(effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    sans = _p(effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(avec, crit) == 55   # 25 + 10 + 20
    assert _score_regles(sans, crit) == 45   # 25 + 20


def test_regles_penalite_naf_hors_icp():
    """NAF hors des codes ICP : -30. NAF dans l'ICP : pas de pénalité."""
    crit = _criteres(codes_naf=["1234Z"], effectif_min=2, effectif_max=15)
    dedans = _p(code_naf="1234Z", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    dehors = _p(code_naf="9999Z", effectif_estime=8, telephone=TEL_OK, email=EMAIL_OK)
    assert _score_regles(dedans, crit) == 55   # 35 + 20
    assert _score_regles(dehors, crit) == 25   # 35 + 20 - 30


def test_regles_codes_naf_vides_pas_de_penalite():
    """ICP sans codes_naf : aucune pénalité NAF, quel que soit le code du prospect."""
    crit = _criteres(codes_naf=[], effectif_min=2, effectif_max=15)
    p = _p(code_naf="9999Z", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(p, crit) == 45   # 25 + 20, pas de -30


def test_regles_plancher_a_zero():
    """Cumul de pénalités : jamais en dessous de 0 (clamp)."""
    crit = _criteres(codes_naf=["1234Z"], effectif_min=2, effectif_max=15)
    p = _p(code_naf="9999Z")  # ni contact, ni effectif connu, NAF hors ICP
    assert _score_regles(p, crit) == 0   # max(0, 0 - 20 - 30)


def test_regles_bonus_geo_uniquement_si_departement_prioritaire():
    """Le bonus géo (+10) ne s'applique que dans les départements de l'ICP."""
    crit = _criteres(effectif_min=2, effectif_max=15, departements=["75", "92"])
    dedans = _p(departement="92", effectif_estime=8, telephone=TEL_OK)
    dehors = _p(departement="13", effectif_estime=8, telephone=TEL_OK)
    assert _score_regles(dedans, crit) == 55   # 25 + 20 + 10
    assert _score_regles(dehors, crit) == 45   # 25 + 20


def test_regles_effectif_estime_pas_le_libelle():
    """Le barème lit effectif_estime (int), pas le libellé texte effectif."""
    crit = _criteres(effectif_min=2, effectif_max=15)
    # Libellé renseigné mais effectif_estime absent -> 0 pt d'effectif (on ne devine pas).
    p = _p(effectif="20 à 49 salariés", effectif_estime=None, telephone=TEL_OK)
    assert _score_regles(p, crit) == 25   # 25 (tel) + 0 (effectif inconnu)


# --- Node d'assemblage (#28) — reste un stub tant que le graphe n'est pas câblé ----
# Conservés depuis #11 : la couche règles est prête (#24) mais `scoring_node` (câblage
# des 3 couches + agrégation) n'est assemblé qu'en #28.
def test_scoring_node_is_async_coroutine() -> None:
    """`scoring_node` est bien une coroutine async (règle #8)."""
    from agents.scoring_agent import scoring_node

    assert inspect.iscoroutinefunction(scoring_node)


def test_scoring_node_stub_raises_not_implemented() -> None:
    """Le node lève NotImplementedError tant que #28 ne l'a pas assemblé."""
    from agents.scoring_agent import scoring_node

    with pytest.raises(NotImplementedError):
        asyncio.run(scoring_node({"prospects": []}))
