"""Exemple illustratif d'ICP pour bootstrap d'un nouveau client.

Issue #11 — STUB. Ce fichier est un EXEMPLE pédagogique uniquement (cf.
docs/ARCHITECTURE.md : « Exemple illustratif pour bootstrap d'un nouveau
client — pas une valeur par défaut utilisée en prod »).

Aucune valeur ici n'est utilisée en production. L'ICP réel de chaque client
vit dans `criteres_ciblage` / `icp_profiles` en base (CLAUDE.md règle #3 :
« Un client = un ICP = une configuration »). `scripts/init_icp.py` (#12)
génère l'embedding ICP d'un client depuis sa config en base, pas depuis ici.

Ce fichier montre juste la forme attendue d'un critère de ciblage.
"""
from __future__ import annotations

# Exemple illustratif — NON utilisé en prod. L'ICP réel vient de la base.
ICP_SEED_EXAMPLE = {
    "nom": "Courtiers en assurance (exemple)",
    "description_icp": "Cabinet de courtage en assurance, 2-10 salariés, Île-de-France.",
    "codes_naf": ["6522Z"],
    "departements": ["75", "92", "93", "94"],
    "effectif_min": 2,
    "effectif_max": 10,
    "anciennete_min_ans": 3,
    "exiger_site_web": True,
    "exiger_email": False,
    "mots_cles_positifs": ["courtage", "assurance"],
    "mots_cles_negatifs": ["agence bancaire"],
}