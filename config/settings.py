"""Configuration centralisée — chargée depuis `.env` via pydantic-settings.

Aucune valeur métier (ICP : NAF, effectif, mots-clés…) ici : uniquement de
l'infra et des clés API (règle #3). L'ICP vit en base (`criteres_ciblage`).

Les noms de champs correspondent aux variables de `.env.example`
(pydantic-settings mappe `POSTGRES_DB` -> `postgres_db`, insensible à la casse).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolère les variables front/autres présentes dans .env
    )

    # ---------- PostgreSQL ----------
    postgres_db: str = "prospection_b2b"
    postgres_user: str = "scraper"
    postgres_password: str = "changeme_postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # ---------- Qdrant ----------
    qdrant_api_key: str = "changeme_qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334

    # ---------- Ollama (embeddings CPU — règle #5) ----------
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_embed_model: str = "nomic-embed-text"

    # ---------- Claude (scoring — jamais codé en dur dans les prompts, règle #6) ----------
    anthropic_api_key: str = ""
    claude_scoring_model: str = "claude-sonnet-5"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def ollama_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


@lru_cache
def get_settings() -> Settings:
    """Instance unique (mémoïsée) — évite de relire `.env` à chaque accès."""
    return Settings()
