"""Génération d'embeddings 100% locale sur CPU via Ollama (règle #5, issue #8).

Aucune API OpenAI. Le modèle est configurable via `OLLAMA_EMBED_MODEL`
(défaut : `nomic-embed-text`, 768 dims, 137 MB, Apache 2.0).

Utilisé par la couche 3 du scoring (#26) et `scripts/init_icp.py` (#12).
"""
from __future__ import annotations

import httpx

from config.settings import get_settings

# Dimension attendue pour nomic-embed-text. Sert de garde-fou : si le modèle
# configuré renvoie une autre taille, les collections Qdrant (#9) seront
# incohérentes — on préfère échouer explicitement.
EMBEDDING_DIM = 768


async def get_embedding(text: str, *, timeout: float = 30.0) -> list[float]:
    """Retourne l'embedding (`EMBEDDING_DIM` floats) du texte via Ollama.

    Args:
        text: texte non vide à encoder.
        timeout: délai max de la requête HTTP (s).

    Raises:
        ValueError: texte vide.
        httpx.HTTPStatusError: Ollama répond un code d'erreur.
        RuntimeError: réponse sans embedding ou dimension inattendue.
    """
    if not text or not text.strip():
        raise ValueError("Le texte à encoder ne peut pas être vide.")

    settings = get_settings()
    url = f"{settings.ollama_url}/api/embed"
    payload = {"model": settings.ollama_embed_model, "input": text}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    # /api/embed renvoie {"embeddings": [[...]]} ; on gère aussi l'ancien
    # /api/embeddings ({"embedding": [...]}) par tolérance.
    embeddings = data.get("embeddings")
    vector = embeddings[0] if embeddings else data.get("embedding")

    if not vector:
        raise RuntimeError(f"Réponse Ollama sans embedding : {data!r}")
    if len(vector) != EMBEDDING_DIM:
        raise RuntimeError(
            f"Dimension d'embedding inattendue : {len(vector)} "
            f"(attendu {EMBEDDING_DIM} pour {settings.ollama_embed_model})."
        )
    return vector
