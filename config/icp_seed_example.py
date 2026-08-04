"""ICP pilote — DONNÉE DE TEST, pas valeur par défaut du produit (issue #4).

Ce fichier est l'unique emplacement légitime contenant des valeurs métier ICP
concrètes (codes NAF, mots-clés sectoriels). Le garde-fou
`tests/test_no_hardcoded_icp.py` l'exclut explicitement de son scan.

Il illustre comment amorcer un nouveau client : un vrai client saisira son
propre ICP via `scripts/seed_icp.py --from-file <son-icp.json>`. Le seed
« garages » ci-dessous n'est jamais chargé en production comme défaut —
c'est un exemple pour bootstrap et les tests d'intégration.

L'embedding Qdrant de cet ICP n'est PAS généré ici (c'est l'issue #12).
On ne remplit que `clients` + `criteres_ciblage` + `icp_profiles`.
"""
from __future__ import annotations

# ICP pilote : garages indépendants (issue #4, livrable #3).
# L'objectif de prospection ciblé : garages auto/moto indépendants, petite
# structure, installés depuis au moins 3 ans (stabilité financière).
ICP_SEEDS: dict[str, dict] = {
    "garages": {
        # --- clients ---
        "nom_entreprise": "Client Pilote — Garages",
        "secteur": "Garages automobiles indépendants",
        "produit_vendu": "Logiciel SaaS de gestion d'atelier",
        "zone_intervention": "France métropolitaine",
        "contact_nom": None,
        "contact_email": None,
        "contact_telephone": None,
        # --- criteres_ciblage ---
        "nom": "Garages indépendants — cible pilote",
        "description_icp": (
            "Garages automobiles et motos indépendants, structure artisanale "
            "de 2 à 15 salariés, en activité depuis au moins 3 ans. Ciblent "
            "les réparateurs multi-marques plutôt que les concessions."
        ),
        # Codes NAF : réparation auto (4520Z), vente auto (4511Z),
        # réparation moto (4540Z — non inclus, hors cible), entretien/carrosserie
        # (4531Z), installation équipements auto (4532Z).
        "codes_naf": ["4520Z", "4511Z", "4531Z", "4532Z"],
        "departements": [],  # pas de restriction géo dans l'exemple pilote
        "effectif_min": 2,
        "effectif_max": 15,
        "anciennete_min_ans": 3,
        "exiger_site_web": False,
        "exiger_email": True,
        "mots_cles_positifs": ["réparation", "multi-marques", "atelier"],
        "mots_cles_negatifs": ["concession", "groupe", "centrale"],
    },
}