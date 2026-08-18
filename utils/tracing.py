"""Configuration LangSmith — traces + coûts LLM (issue #30).

Bootstrap **par variables d'environnement** (mécanisme LangSmith confirmé). Ce
module n'importe PAS `langsmith` : il ne fait que propager la config `LANGCHAIN_*`
depuis `settings` vers l'environnement, pour que le SDK langsmith la capte quand le
graphe (#28) instancie et trace le client Claude.

⚠️ Périmètre #30 = config uniquement. Le traçage EFFECTIF des appels Claude
(`@traceable` / wrapper sur le call site) est câblé à l'assemblage du graphe (#28) —
ça touche `agents/scoring_agent.py`, hors de ce module.

Convention `LANGCHAIN_*` alignée sur `.env.example` (acceptée par le SDK langsmith).
"""
from __future__ import annotations

import logging
import os

from config.settings import get_settings

logger = logging.getLogger(__name__)


def configure_tracing() -> bool:
    """Active le traçage LangSmith si `LANGCHAIN_TRACING_V2` **et** une clé API sont
    présents, en propageant `LANGCHAIN_*` dans l'environnement pour le SDK langsmith.

    À appeler une fois au démarrage (CLI #29 / orchestrateur). Idempotent.

    Returns:
        True si le traçage est activé ; False sinon — désactivé, ou clé absente
        (on ne trace jamais « à moitié » en silence).
    """
    settings = get_settings()

    if not settings.langchain_tracing_v2:
        return False

    if not settings.langchain_api_key:
        logger.warning(
            "LangSmith : LANGCHAIN_TRACING_V2 activé mais LANGCHAIN_API_KEY absente "
            "— traçage désactivé (pas de trace partielle silencieuse)."
        )
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

    logger.info("LangSmith activé (projet=%s).", settings.langchain_project or "default")
    return True
