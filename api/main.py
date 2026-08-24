"""API HTTP de lecture (#116) — expose les données du pipeline au front React.

Lecture seule (MVP de l'intégration front↔back). Réutilise le pool asyncpg de
`utils/db`. Le pool est créé dans le `lifespan` (donc sur la loop uvicorn) : c'est
le point qui évite le piège classique « asyncpg pool attached to a different loop »
quand on branche un code async CLI derrière un serveur ASGI.

Lancer :
    uvicorn api.main:app --host 127.0.0.1 --port 8000
(en prod : lié 127.0.0.1, accès par tunnel SSH — cf. DEPLOY.md, comme Metabase #37.)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    CampagneCreatedOut, CampagneDTO, KPIsDTO, NoteIn, OutcomeIn,
    ProspectDetailDTO, ProspectPage, ProspectRowDTO,
)
from utils import db

# Coûts unitaires estimés pour le KPI coût (approximation, pas une facturation).
# NB : dupliqué avec settings du rapport #38 ; à unifier quand #38 sera sur main.
_COUT_CLAUDE_EUR = 0.002
_COUT_TAVILY_EUR = 0.0

# Statuts autorisés pour le filtre (garde l'entrée utilisateur).
_STATUTS = {"nouveau", "qualifie", "en_attente_appel", "appele", "rdv",
            "refus", "absent", "invalide"}

_ROW_COLS = ("id", "nom_entreprise", "ville", "departement", "code_naf",
             "score_final", "statut", "telephone", "email", "site_web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée le pool sur CETTE event-loop (celle d'uvicorn) — pas à l'import.
    await db.get_pg_pool()
    yield
    await db.close()


app = FastAPI(title="Prospection B2B — API de lecture", version="0.1.0", lifespan=lifespan)

# CORS : lecture seule, instance liée à 127.0.0.1 (accès tunnel). Origines
# permissives en MVP ; à restreindre à l'origine du front en prod exposée.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"],
)

# Statuts autorisés en écriture (résultat d'appel).
_OUTCOME_STATUTS = {
    "nouveau", "qualifie", "en_attente_appel", "appele", "rdv",
    "refus", "absent", "invalide",
}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/campagnes", response_model=list[CampagneDTO])
async def list_campagnes():
    pool = await db.get_pg_pool()
    rows = await pool.fetch(
        "SELECT id, nom, statut, prospects_collectes, prospects_qualifies "
        "FROM campagnes ORDER BY nom"
    )
    return [dict(r) for r in rows]


@app.get("/api/campagnes/{campagne_id}", response_model=CampagneDTO)
async def get_campagne(campagne_id: UUID):
    pool = await db.get_pg_pool()
    row = await pool.fetchrow(
        "SELECT id, nom, statut, prospects_collectes, prospects_qualifies "
        "FROM campagnes WHERE id = $1", campagne_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return dict(row)


@app.get("/api/prospects", response_model=ProspectPage)
async def list_prospects(
    campagne_id: UUID | None = None,
    statut: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """File d'appel paginée, triée par score décroissant."""
    if statut is not None and statut not in _STATUTS:
        raise HTTPException(status_code=422, detail=f"statut invalide : {statut}")

    conds: list[str] = []
    params: list[object] = []
    if campagne_id is not None:
        params.append(campagne_id)
        conds.append(f"campagne_id = ${len(params)}")
    if statut is not None:
        params.append(statut)
        conds.append(f"statut = ${len(params)}")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    pool = await db.get_pg_pool()
    total = await pool.fetchval(f"SELECT count(*) FROM prospects {where}", *params)
    rows = await pool.fetch(
        f"SELECT {', '.join(_ROW_COLS)} FROM prospects {where} "
        f"ORDER BY score_final DESC, created_at ASC "
        f"LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}",
        *params, limit, offset,
    )
    return ProspectPage(
        total=total, limit=limit, offset=offset,
        items=[ProspectRowDTO(**dict(r)) for r in rows],
    )


@app.get("/api/prospects/{prospect_id}", response_model=ProspectDetailDTO)
async def get_prospect(prospect_id: UUID):
    pool = await db.get_pg_pool()
    row = await pool.fetchrow(
        """
        SELECT p.id, p.nom_entreprise, p.ville, p.departement, p.code_naf,
               p.score_final, p.statut, p.telephone, p.email, p.site_web,
               p.nom_dirigeant, p.libelle_naf, p.telephone_2, p.effectif,
               p.adresse, p.code_postal, p.date_creation,
               p.score_regles, p.score_llm, p.score_embedding,
               s.justification_llm
        FROM prospects p
        LEFT JOIN LATERAL (
            SELECT justification_llm FROM scores
            WHERE prospect_id = p.id ORDER BY scored_at DESC LIMIT 1
        ) s ON TRUE
        WHERE p.id = $1
        """,
        prospect_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectDetailDTO(**dict(row))


@app.get("/api/kpis", response_model=KPIsDTO)
async def kpis(campagne_id: UUID | None = None, since_days: int = Query(7, ge=1)):
    """KPIs agrégés (PRD §6) — sur une campagne ou une fenêtre glissante."""
    if campagne_id is not None:
        where, params = "campagne_id = $1", [campagne_id]
        portee = f"campagne {campagne_id}"
    else:
        where, params = "created_at >= NOW() - make_interval(days => $1::int)", [since_days]
        portee = f"{since_days} derniers jours"

    pool = await db.get_pg_pool()
    r = await pool.fetchrow(
        f"""
        SELECT count(*) AS collectes,
          count(*) FILTER (WHERE statut = 'qualifie') AS qualifies,
          count(*) FILTER (WHERE telephone IS NOT NULL AND telephone <> '') AS avec_tel,
          count(*) FILTER (WHERE email IS NOT NULL AND email <> '') AS avec_email,
          avg(score_final) FILTER (WHERE statut = 'qualifie') AS smq
        FROM prospects WHERE {where}
        """,
        *params,
    )
    n = r["collectes"] or 0
    pct = lambda x: round(100.0 * (x or 0) / n, 1) if n else 0.0
    return KPIsDTO(
        portee=portee, collectes=n, qualifies=r["qualifies"] or 0,
        taux_tel=pct(r["avec_tel"]), taux_email=pct(r["avec_email"]),
        pct_qualifies=pct(r["qualifies"]),
        score_moy_qualifies=(round(r["smq"], 1) if r["smq"] is not None else None),
        cout_estime_eur=round(n * (_COUT_CLAUDE_EUR + _COUT_TAVILY_EUR), 3),
    )


# --- Écriture (#116 A) -----------------------------------------------------
@app.post("/api/prospects/{prospect_id}/outcome")
async def set_outcome(prospect_id: UUID, body: OutcomeIn):
    """Résultat d'appel : met à jour le statut du prospect (rdv/refus/absent…)."""
    if body.statut not in _OUTCOME_STATUTS:
        raise HTTPException(status_code=422, detail=f"statut invalide : {body.statut}")
    pool = await db.get_pg_pool()
    row = await pool.fetchrow(
        "UPDATE prospects SET statut = $2, updated_at = NOW() "
        "WHERE id = $1 RETURNING id, statut",
        prospect_id, body.statut,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return {"id": str(row["id"]), "statut": row["statut"]}


@app.post("/api/prospects/{prospect_id}/note")
async def set_note(prospect_id: UUID, body: NoteIn):
    """Enregistre une note libre sur le prospect."""
    pool = await db.get_pg_pool()
    row = await pool.fetchrow(
        "UPDATE prospects SET notes = $2, updated_at = NOW() WHERE id = $1 RETURNING id",
        prospect_id, body.note,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return {"id": str(row["id"]), "ok": True}


@app.post("/api/campagnes", response_model=CampagneCreatedOut, status_code=201)
async def create_campagne(payload: dict = Body(...)):
    """Crée une campagne — CONFIG SEULEMENT (0 appel API, 0 run, gate crédits).

    Réutilise le normaliseur ICP de seed_icp. Ne génère PAS l'embedding (init_icp)
    et ne lance PAS le pipeline : la campagne naît en 'brouillon'. Le lancement
    reste une action séparée et explicite.
    """
    from utils.icp_payload import normalize
    try:
        p = normalize(payload)
    except (SystemExit, Exception) as exc:  # ValidationError + garde-fous seed
        raise HTTPException(status_code=422, detail=f"ICP invalide : {exc}")

    client = p.to_client_row()
    crit = p.to_criteres_row()
    description = p.description_icp or p.nom

    pool = await db.get_pg_pool()
    async with pool.acquire() as conn, conn.transaction():
        client_id = await conn.fetchval(
            """
            INSERT INTO clients (nom_entreprise, secteur, produit_vendu,
                zone_intervention, contact_nom, contact_email, contact_telephone)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id;
            """,
            client["nom_entreprise"], client["secteur"], client["produit_vendu"],
            client["zone_intervention"], client["contact_nom"],
            client["contact_email"], client["contact_telephone"],
        )
        critere_id = await conn.fetchval(
            """
            INSERT INTO criteres_ciblage (client_id, nom, description_icp,
                codes_naf, departements, effectif_min, effectif_max,
                anciennete_min_ans, exiger_site_web, exiger_email,
                mots_cles_positifs, mots_cles_negatifs)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING id;
            """,
            client_id, crit["nom"], crit["description_icp"], crit["codes_naf"],
            crit["departements"], crit["effectif_min"], crit["effectif_max"],
            crit["anciennete_min_ans"], crit["exiger_site_web"],
            crit["exiger_email"], crit["mots_cles_positifs"],
            crit["mots_cles_negatifs"],
        )
        icp_id = await conn.fetchval(
            "INSERT INTO icp_profiles (client_id, critere_id, nom, description) "
            "VALUES ($1,$2,$3,$4) RETURNING id;",
            client_id, critere_id, p.nom, description,
        )
        campagne_id = await conn.fetchval(
            "INSERT INTO campagnes (client_id, critere_id, icp_profile_id, nom) "
            "VALUES ($1,$2,$3,$4) RETURNING id;",
            client_id, critere_id, icp_id, p.nom,
        )
    return CampagneCreatedOut(
        client_id=client_id, critere_id=critere_id, icp_profile_id=icp_id,
        campagne_id=campagne_id, nom=p.nom,
    )
