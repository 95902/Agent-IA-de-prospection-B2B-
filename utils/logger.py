"""Logger structuré (Loguru) + config LangSmith/observabilité.

Issue #11 — STUB. Implémentation détaillée portée par une issue dédiée.
Loguru remplace le logging stdlib pour la sortie structurée (JSON en prod).
LangSmith : tracing des appels LLM (config via LANGCHAIN_* dans .env).
"""
from __future__ import annotations


def get_logger(name: str | None = None):  # type: ignore[no-untyped-def]
    """STUB — retourne un logger Loguru nommé. À implémenter."""
    raise NotImplementedError("utils/logger non implémenté — voir issue dédiée.")