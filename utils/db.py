"""Couche d'accès aux données : PostgreSQL (asyncpg) + Qdrant (issue #9).

Tout est async (règle #8). Deux singletons paresseux — pool PG et client
Qdrant — réutilisés par tous les nodes du graphe (#28) et les scripts.

Collections Qdrant (768 dims, cosine, HNSW m=16) : voir `docs/qdrant_schema.md`.
Schéma PostgreSQL de référence : `docker/postgres/init/01_schema.sql`.
"""
from __future__ import annotations

import json

import asyncpg
from qdrant_client import AsyncQdrantClient, models

from config.settings import get_settings
from utils.embeddings import EMBEDDING_DIM

# --- Qdrant -----------------------------------------------------------------
COLLECTION_PROSPECTS = "prospects_embeddings"
COLLECTION_ICP = "icp_profiles"
_HNSW_M = 16
_HNSW_EF_CONSTRUCT = 100

# Champs payload à indexer (keyword) — cf. docs/qdrant_schema.md. Sans index,
# un filtre (ex. `departement` dans search_similar_prospects) fait un scan
# séquentiel lent, et Qdrant dégrade silencieusement au lieu d'échouer.
_PAYLOAD_INDEXES = {
    COLLECTION_PROSPECTS: ("campagne_id", "code_naf", "departement"),
    COLLECTION_ICP: ("client_id", "critere_id"),
}

# Colonnes de `prospects` autorisées à l'upsert (whitelist anti-injection :
# on ne construit jamais de SQL à partir de clés arbitraires du dict).
_PROSPECT_COLUMNS = (
    "campagne_id", "source_id", "siret", "siren", "nom_entreprise",
    "nom_dirigeant", "code_naf", "libelle_naf", "telephone", "telephone_2",
    "email", "site_web", "adresse", "code_postal", "ville", "departement",
    "latitude", "longitude", "effectif", "effectif_code", "effectif_estime",
    "date_creation", "chiffre_affaire", "statut", "bloctel_ok",
    "bloctel_verifie_le", "doublon", "qdrant_point_id", "notes", "raw_data",
)

_pg_pool: asyncpg.Pool | None = None
_qdrant: AsyncQdrantClient | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Encode/décode automatiquement les colonnes JSON/JSONB en dict Python."""
    for typename in ("json", "jsonb"):
        await conn.set_type_codec(
            typename, encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )


async def get_pg_pool() -> asyncpg.Pool:
    """Pool asyncpg singleton (créé au premier appel)."""
    global _pg_pool
    if _pg_pool is None:
        settings = get_settings()
        _pg_pool = await asyncpg.create_pool(
            dsn=settings.postgres_dsn,
            min_size=1,
            max_size=10,
            init=_init_connection,
        )
    return _pg_pool


def get_qdrant() -> AsyncQdrantClient:
    """Client Qdrant async singleton (gRPC — port dédié `QDRANT_GRPC_PORT`)."""
    global _qdrant
    if _qdrant is None:
        settings = get_settings()
        _qdrant = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            grpc_port=settings.qdrant_grpc_port,
            prefer_grpc=True,
            api_key=settings.qdrant_api_key,
            https=False,
        )
    return _qdrant


async def close() -> None:
    """Ferme le pool PG et le client Qdrant (tests, arrêt de l'appli)."""
    global _pg_pool, _qdrant
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None
    if _qdrant is not None:
        await _qdrant.close()
        _qdrant = None


async def ensure_collections() -> None:
    """Crée les 2 collections Qdrant + leurs index payload si absentes.

    Idempotent : si la collection existe déjà, on ne touche à rien (les index
    sont créés en même temps que la collection, donc pas de re-création).
    """
    client = get_qdrant()
    vectors = models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)
    hnsw = models.HnswConfigDiff(m=_HNSW_M, ef_construct=_HNSW_EF_CONSTRUCT)
    for name in (COLLECTION_PROSPECTS, COLLECTION_ICP):
        if await client.collection_exists(name):
            continue
        await client.create_collection(
            collection_name=name, vectors_config=vectors, hnsw_config=hnsw
        )
        for field in _PAYLOAD_INDEXES[name]:
            await client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )


async def upsert_prospect(data: dict) -> str:
    """Insère ou met à jour un prospect. Retourne son UUID (str).

    Conflit sur `(campagne_id, siret)` — un même SIRET peut exister dans
    plusieurs campagnes mais pas deux fois dans la même (cf. contrainte UNIQUE
    du schéma). `campagne_id` et `nom_entreprise` (NOT NULL) sont requis.
    """
    if "campagne_id" not in data or not data.get("nom_entreprise"):
        raise ValueError(
            "upsert_prospect requiert au minimum 'campagne_id' et 'nom_entreprise'."
        )

    cols = [c for c in _PROSPECT_COLUMNS if c in data]
    placeholders = [f"${i + 1}" for i in range(len(cols))]
    values = [data[c] for c in cols]
    updates = ", ".join(
        f"{c} = EXCLUDED.{c}" for c in cols if c not in ("campagne_id", "siret")
    )
    query = f"""
        INSERT INTO prospects ({", ".join(cols)})
        VALUES ({", ".join(placeholders)})
        ON CONFLICT (campagne_id, siret)
        DO UPDATE SET {updates}, updated_at = NOW()
        RETURNING id;
    """
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)
    return str(row["id"])


async def save_score(prospect_id: str, score_data: dict) -> None:
    """Historise un scoring (table `scores`) et met à jour les scores courants
    du prospect, dans une même transaction."""
    pool = await get_pg_pool()
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO scores (prospect_id, score_regles, score_llm,
                score_embedding, score_final, justification_llm,
                prompt_version, modele_llm, details)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            """,
            prospect_id,
            score_data.get("score_regles"),
            score_data.get("score_llm"),
            score_data.get("score_embedding"),
            score_data.get("score_final"),
            score_data.get("justification_llm"),
            score_data.get("prompt_version"),
            score_data.get("modele_llm"),
            score_data.get("details", {}),
        )
        await conn.execute(
            """
            UPDATE prospects SET
                score_regles    = COALESCE($2, score_regles),
                score_llm       = COALESCE($3, score_llm),
                score_embedding = COALESCE($4, score_embedding),
                score_final     = COALESCE($5, score_final)
            WHERE id = $1;
            """,
            prospect_id,
            score_data.get("score_regles"),
            score_data.get("score_llm"),
            score_data.get("score_embedding"),
            score_data.get("score_final"),
        )


async def get_file_appel(limit: int = 100) -> list[dict]:
    """Retourne la file d'appel (vue `file_appel` : Bloctel OK < 30 j, hors
    opposition RGPD, triée par score) — cf. schéma."""
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM file_appel LIMIT $1;", limit)
    return [dict(r) for r in rows]


async def upsert_prospect_embedding(
    prospect_id: str, embedding: list[float], payload: dict
) -> None:
    """Insère/met à jour le vecteur d'un prospect dans Qdrant (id = UUID PG)."""
    client = get_qdrant()
    await client.upsert(
        collection_name=COLLECTION_PROSPECTS,
        points=[
            models.PointStruct(id=prospect_id, vector=embedding, payload=payload)
        ],
    )


async def search_similar_prospects(
    query_embedding: list[float],
    top_k: int = 10,
    departement: str | None = None,
) -> list[dict]:
    """Recherche les prospects les plus proches, filtrable par département."""
    client = get_qdrant()
    query_filter = None
    if departement:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="departement", match=models.MatchValue(value=departement)
                )
            ]
        )
    result = await client.query_points(
        collection_name=COLLECTION_PROSPECTS,
        query=query_embedding,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [
        {"id": p.id, "score": p.score, "payload": p.payload} for p in result.points
    ]


async def get_icp_embedding(icp_id: str) -> list[float] | None:
    """Récupère le vecteur ICP d'un client (collection `icp_profiles`).

    Retourne None si le point n'existe pas encore (ICP non initialisé, #12).
    """
    client = get_qdrant()
    points = await client.retrieve(
        collection_name=COLLECTION_ICP, ids=[icp_id], with_vectors=True
    )
    if not points:
        return None
    return points[0].vector
