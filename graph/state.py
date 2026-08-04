"""État partagé du graphe LangChain (règles #7/#8, issue #10).

`EtatAgent` est le TypedDict passé entre les 6 nodes du pipeline (#28) :
init_campagne -> fetch_sirene -> enrichir -> nettoyer -> scorer -> sauvegarder.

`total=False` : les champs se remplissent progressivement au fil du pipeline
(un node lit ce qui existe déjà et ajoute sa contribution). La forme définitive
sera confirmée à l'assemblage du graphe (#28).
"""
from typing import TypedDict

from models.criteres import CriteresCiblage
from models.prospect import Prospect


class EtatAgent(TypedDict, total=False):
    # Contexte de campagne (posé par init_campagne, #16)
    campagne_id: str
    client_id: str
    criteres: CriteresCiblage
    icp_embedding: list[float] | None

    # Données en cours de traitement
    prospects: list[Prospect]
    config_scoring: dict  # poids des 3 couches (depuis campagnes.config_scoring)

    # Suivi d'exécution
    erreurs: list[str]
    collectes: int
    qualifies: int
