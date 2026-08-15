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

    # ---------- APIs collecte ----------
    insee_api_key: str = ""  # api-sirene/3.11 (header X-INSEE-Api-Key-Integration)
    tavily_api_key: str = ""  # enrichissement (#18) — auth Bearer, quota 1000/mois

    # ---------- APIs enrichissement ----------
    pappers_api_key: str = ""      # API Entreprise (auth : query param `api_token`)
    dropcontact_api_key: str = ""  # emails B2B (auth : header `X-Access-Token`)

    # ---------- Qualité des prospects (#68) ----------
    # Au-delà de N établissements actifs à la MÊME adresse, on considère qu'il
    # s'agit d'une société de domiciliation (siège social / boîte aux lettres)
    # et non d'un local d'exploitation. Calibré sur 40 garages parisiens réels :
    # adresses ordinaires 3-134, domiciliations 778-44589 (cf. issue #68).
    # ⚠️ Dépend de la densité urbaine — à réévaluer hors grande ville.
    domiciliation_seuil: int = 300

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
