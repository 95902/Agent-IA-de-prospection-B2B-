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
    # Défaut Haiku 4.5 : classification bornée bon marché (cible < 0,003 €/prospect).
    # Configurable (règle #6) ; l'audit qualité #32 ré-arbitre Haiku vs Sonnet sur
    # données réelles. ⚠️ Le code de #25 doit rester agnostique du modèle : Haiku 4.5
    # REFUSE output_config.effort mais ACCEPTE temperature ; Sonnet 5 fait l'inverse
    # (effort OK, temperature/top_p → 400). Ne fixer aucun des deux → défauts + sortie
    # structurée (output_config.format), valide sur les deux.
    anthropic_api_key: str = ""
    claude_scoring_model: str = "claude-haiku-4-5"

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

    # ---------- Budget crédits opposition commerciale (#19/#74) ----------
    # Plafond de SIREN interrogés chez Pappers pour l'opposition commerciale
    # (1 crédit chacun). Knob de COÛT, pas une valeur métier (règle #3). None =
    # vérifier tous les survivants du nettoyage (peut coûter cher sur une grosse
    # campagne — poser un budget en prod, cf. suivi de coûts #23).
    opposition_budget_credits: int | None = None

    # ---------- LangSmith (traces + coûts LLM — #30) ----------
    # Observabilité optionnelle, DÉSACTIVÉE par défaut. Convention LANGCHAIN_*
    # (cf. .env.example) — acceptée par le SDK langsmith. Le traçage effectif des
    # appels Claude est câblé à l'assemblage du graphe (#28) ; ici, seulement la
    # config, propagée dans l'environnement par utils/tracing.configure_tracing().
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "prospection-b2b"
    langchain_endpoint: str = ""  # vide = endpoint LangSmith cloud par défaut

    # ---------- Rapport hebdo (email Brevo — #38) ----------
    # Envoi INERTE par défaut : sans clé Brevo NI destinataire, le rapport se
    # génère et s'imprime, mais n'est JAMAIS envoyé (pas d'email sortant sans
    # config explicite). Brevo API v3 (header `api-key`).
    brevo_api_key: str = ""
    rapport_email_from: str = ""   # expéditeur vérifié côté Brevo
    rapport_email_to: str = ""     # destinataire(s), séparés par des virgules
    # Coûts unitaires ESTIMÉS pour le KPI coût/qualifié (#23) — approximations,
    # pas une facturation. Knobs de coût, ajustables sans toucher au code.
    cout_claude_par_prospect_eur: float = 0.002
    cout_tavily_par_prospect_eur: float = 0.0   # quota gratuit 1000/mois

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
