-- ============================================================
--  SCHÉMA AGENT PROSPECTION B2B — PostgreSQL 16
--  Exécuté automatiquement au premier démarrage du container
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- recherche full-text rapide

-- ============================================================
--  CLIENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS clients (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    nom_entreprise      TEXT NOT NULL,
    secteur             TEXT NOT NULL,
    produit_vendu       TEXT NOT NULL,
    zone_intervention   TEXT NOT NULL,
    contact_nom         TEXT,
    contact_email       TEXT UNIQUE,
    contact_telephone   TEXT,
    statut              TEXT NOT NULL DEFAULT 'essai'
                        CHECK (statut IN ('essai','actif','suspendu','inactif')),
    meta                JSONB NOT NULL DEFAULT '{}'::JSONB
);

-- ============================================================
--  CRITÈRES DE CIBLAGE (ICP configurable par client — règle #3)
-- ============================================================
CREATE TABLE IF NOT EXISTS criteres_ciblage (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    nom                 TEXT NOT NULL,
    description_icp     TEXT,
    codes_naf           TEXT[] NOT NULL DEFAULT '{}',
    departements        TEXT[] NOT NULL DEFAULT '{}',
    effectif_min        INTEGER NOT NULL DEFAULT 1  CHECK (effectif_min >= 0),
    effectif_max        INTEGER NOT NULL DEFAULT 500,
    anciennete_min_ans  INTEGER NOT NULL DEFAULT 0  CHECK (anciennete_min_ans >= 0),
    exiger_site_web     BOOLEAN NOT NULL DEFAULT FALSE,
    exiger_email        BOOLEAN NOT NULL DEFAULT FALSE,
    mots_cles_positifs  TEXT[] NOT NULL DEFAULT '{}',
    mots_cles_negatifs  TEXT[] NOT NULL DEFAULT '{}',
    -- Tags OSM/Overpass (ex. 'tourism=hotel') pour la pré-passe d'enrichissement
    -- gratuite (#69). Lu par init_campagne + modèle CriteresCiblage — la colonne
    -- manquait au schéma, ce qui faisait échouer init_campagne en mode campagne.
    osm_tags            TEXT[] NOT NULL DEFAULT '{}',
    actif               BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (effectif_max >= effectif_min)
);

CREATE INDEX IF NOT EXISTS idx_criteres_client ON criteres_ciblage(client_id) WHERE actif = TRUE;

-- ============================================================
--  PROFILS ICP (référence pour le scoring embeddings)
-- ============================================================
CREATE TABLE IF NOT EXISTS icp_profiles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    critere_id          UUID REFERENCES criteres_ciblage(id) ON DELETE SET NULL,
    nom                 TEXT NOT NULL,
    description         TEXT NOT NULL,
    qdrant_point_id     UUID,          -- ID du vecteur dans Qdrant
    embedding_version   TEXT,          -- ex: 'nomic-embed-text-v2' — permet la ré-indexation
    actif               BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_icp_client ON icp_profiles(client_id) WHERE actif = TRUE;

-- ============================================================
--  SOURCES
-- ============================================================
CREATE TABLE IF NOT EXISTS sources (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom                 TEXT NOT NULL UNIQUE,
    type                TEXT NOT NULL
                        CHECK (type IN ('api_officielle','scraping','enrichissement','manuel')),
    url                 TEXT,
    derniere_collecte   TIMESTAMPTZ,
    nb_prospects        INTEGER NOT NULL DEFAULT 0
);

-- Sources initiales. L'issue #7 liste 5 entrées (sirene_insee, tavily,
-- pages_jaunes, dropcontact, manuel) ; 'pappers' est ajouté car listé comme
-- source légale dans CLAUDE.md (règle #2). INSERT ... ON CONFLICT DO NOTHING
-- garantit l'idempotence.
INSERT INTO sources (nom, type, url) VALUES
    ('sirene_insee', 'api_officielle', 'https://api.insee.fr/entreprises/sirene/V3.11'),
    ('tavily',       'scraping',       'https://api.tavily.com'),
    ('pappers',      'api_officielle', 'https://api.pappers.fr'),
    ('pages_jaunes', 'scraping',       'https://www.pagesjaunes.fr'),
    ('dropcontact',  'enrichissement', 'https://api.dropcontact.com'),
    ('manuel',       'manuel',         NULL)
ON CONFLICT (nom) DO NOTHING;

-- ============================================================
--  CAMPAGNES
-- ============================================================
CREATE TABLE IF NOT EXISTS campagnes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    critere_id          UUID NOT NULL REFERENCES criteres_ciblage(id),
    icp_profile_id      UUID REFERENCES icp_profiles(id),
    nom                 TEXT NOT NULL,
    statut              TEXT NOT NULL DEFAULT 'brouillon'
                        CHECK (statut IN ('brouillon','en_cours','terminee','annulee')),
    date_lancement      TIMESTAMPTZ,
    max_prospects       INTEGER NOT NULL DEFAULT 500 CHECK (max_prospects > 0),
    -- KPIs temps réel
    prospects_collectes INTEGER NOT NULL DEFAULT 0,
    prospects_qualifies INTEGER NOT NULL DEFAULT 0,
    appels_passes       INTEGER NOT NULL DEFAULT 0,
    rdv_obtenus         INTEGER NOT NULL DEFAULT 0,
    -- La somme des poids doit valoir 1.0 — validée côté Pydantic (règle #7)
    config_scoring      JSONB NOT NULL DEFAULT
                        '{"poids_regles":0.35,"poids_llm":0.45,"poids_embedding":0.20}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_campagnes_client ON campagnes(client_id);
CREATE INDEX IF NOT EXISTS idx_campagnes_statut ON campagnes(statut) WHERE statut = 'en_cours';

-- ============================================================
--  PROSPECTS
-- ============================================================
CREATE TABLE IF NOT EXISTS prospects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    campagne_id         UUID NOT NULL REFERENCES campagnes(id) ON DELETE CASCADE,
    source_id           UUID REFERENCES sources(id),

    -- Identité entreprise
    siret               VARCHAR(14) CHECK (siret ~ '^\d{14}$'),
    siren               VARCHAR(9)  CHECK (siren ~ '^\d{9}$'),
    nom_entreprise      TEXT NOT NULL,
    nom_dirigeant       TEXT,
    code_naf            VARCHAR(6),    -- format INSEE avec point : '62.01Z'
    libelle_naf         TEXT,

    -- Contact
    telephone           TEXT,
    telephone_2         TEXT,
    email               TEXT,
    site_web            TEXT,

    -- Adresse
    adresse             TEXT,
    code_postal         VARCHAR(5),
    ville               TEXT,
    departement         VARCHAR(3),
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,

    -- Infos business
    effectif            TEXT,          -- libellé INSEE : '10 à 19 salariés'
    effectif_code       VARCHAR(2),    -- tranche INSEE (00,01,02,03,11,12,21,22,31,32,41,42,51,52,53)
    effectif_estime     INTEGER,       -- borne basse numérique — permet le filtrage effectif_min/max
    date_creation       DATE,
    chiffre_affaire     TEXT,

    -- Scoring (valeurs courantes — historique dans table scores)
    score_final         INTEGER NOT NULL DEFAULT 0 CHECK (score_final BETWEEN 0 AND 100),
    score_regles        INTEGER NOT NULL DEFAULT 0 CHECK (score_regles BETWEEN 0 AND 100),
    score_llm           INTEGER NOT NULL DEFAULT 0 CHECK (score_llm BETWEEN 0 AND 100),
    score_embedding     REAL    NOT NULL DEFAULT 0 CHECK (score_embedding BETWEEN 0 AND 1),

    -- Statut pipeline
    statut              TEXT NOT NULL DEFAULT 'nouveau'
                        CHECK (statut IN ('nouveau','qualifie','en_attente_appel',
                                          'appele','rdv','refus','absent','invalide')),
    -- Bloctel : NULL = jamais vérifié ou vérification expirée (règle #1 : 30 jours max)
    bloctel_ok          BOOLEAN,
    bloctel_verifie_le  TIMESTAMPTZ,
    doublon             BOOLEAN NOT NULL DEFAULT FALSE,
    qdrant_point_id     UUID,           -- ID du vecteur dans Qdrant

    -- Debug
    notes               TEXT,
    raw_data            JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Un même SIRET peut exister dans plusieurs campagnes (multi-clients),
    -- mais pas deux fois dans la même campagne
    UNIQUE (campagne_id, siret)
);

-- ============================================================
--  HISTORIQUE SCORES
-- ============================================================
CREATE TABLE IF NOT EXISTS scores (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scored_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prospect_id         UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    score_regles        INTEGER CHECK (score_regles BETWEEN 0 AND 100),
    score_llm           INTEGER CHECK (score_llm BETWEEN 0 AND 100),
    score_embedding     REAL    CHECK (score_embedding BETWEEN 0 AND 1),
    score_final         INTEGER CHECK (score_final BETWEEN 0 AND 100),
    justification_llm   TEXT,
    prompt_version      TEXT,
    modele_llm          TEXT,           -- modèle Claude utilisé (traçabilité coûts/qualité)
    details             JSONB NOT NULL DEFAULT '{}'::JSONB
);

-- ============================================================
--  HISTORIQUE VÉRIFICATIONS BLOCTEL (audit légal — règle #1)
-- ============================================================
CREATE TABLE IF NOT EXISTS bloctel_verifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    verifie_le          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prospect_id         UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    telephone           TEXT NOT NULL,
    resultat            BOOLEAN NOT NULL,   -- TRUE = appelable (non inscrit Bloctel)
    reference_bloctel   TEXT                -- référence retournée par l'API (preuve)
);

CREATE INDEX IF NOT EXISTS idx_bloctel_prospect ON bloctel_verifications(prospect_id, verifie_le DESC);

-- ============================================================
--  OPPOSITIONS RGPD (droit d'opposition — ne plus jamais contacter)
-- ============================================================
CREATE TABLE IF NOT EXISTS oppositions_rgpd (
    siret               VARCHAR(14) PRIMARY KEY,
    telephone           TEXT,
    email               TEXT,
    date_opposition     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    motif               TEXT
);

-- ============================================================
--  JOURNAL PURGE RGPD (audit des suppressions automatiques — règle #9)
-- ============================================================
CREATE TABLE IF NOT EXISTS purge_rgpd_log (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    purge_le            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    table_cible         TEXT NOT NULL,
    nb_lignes           INTEGER NOT NULL,
    motif               TEXT NOT NULL   -- ex: 'prospects invalides > 6 mois'
);

-- ============================================================
--  APPELS (préparé pour la phase 2 vocal)
-- ============================================================
CREATE TABLE IF NOT EXISTS appels (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prospect_id         UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    date_appel          TIMESTAMPTZ,
    duree_secondes      INTEGER CHECK (duree_secondes >= 0),
    statut              TEXT NOT NULL DEFAULT 'planifie'
                        CHECK (statut IN ('planifie','en_cours','termine',
                                          'echec','absent','rappel')),
    transcript          TEXT,
    resume_llm          TEXT,
    rdv_pris            BOOLEAN NOT NULL DEFAULT FALSE,
    rdv_datetime        TIMESTAMPTZ,
    notes_commercial    TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}'::JSONB
);

-- ============================================================
--  INDEX
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_prospects_statut       ON prospects(statut);
CREATE INDEX IF NOT EXISTS idx_prospects_score        ON prospects(score_final DESC);
CREATE INDEX IF NOT EXISTS idx_prospects_dept         ON prospects(departement);
CREATE INDEX IF NOT EXISTS idx_prospects_naf          ON prospects(code_naf);
CREATE INDEX IF NOT EXISTS idx_prospects_campagne     ON prospects(campagne_id);
CREATE INDEX IF NOT EXISTS idx_prospects_siren        ON prospects(siren);
CREATE INDEX IF NOT EXISTS idx_prospects_nom_trgm     ON prospects USING gin(nom_entreprise gin_trgm_ops);
-- Index partiel : prospects appelables (Bloctel OK) — accélère la vue file_appel (règle #1)
CREATE INDEX IF NOT EXISTS idx_prospects_bloctel      ON prospects(campagne_id, score_final DESC)
    WHERE bloctel_ok = TRUE;
-- Index pour le job de re-vérification Bloctel 30 jours (issue #40) :
-- sélectionne les prospects appelables dont la vérification expire
CREATE INDEX IF NOT EXISTS idx_prospects_bloctel_verif ON prospects(bloctel_verifie_le)
    WHERE bloctel_ok = TRUE OR bloctel_ok IS NULL;
-- Index partiel qui couvre exactement la vue file_appel (tri inclus)
CREATE INDEX IF NOT EXISTS idx_prospects_file_appel   ON prospects(campagne_id, score_final DESC, created_at ASC)
    WHERE statut = 'qualifie' AND bloctel_ok = TRUE AND doublon = FALSE AND telephone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scores_prospect        ON scores(prospect_id, scored_at DESC);
CREATE INDEX IF NOT EXISTS idx_appels_prospect        ON appels(prospect_id, date_appel DESC);

-- ============================================================
--  TRIGGER updated_at automatique
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- CREATE TRIGGER n'est pas idempotent en PostgreSQL (pas de IF NOT EXISTS) ;
-- on DROP IF EXISTS avant chaque CREATE pour permettre une ré-exécution
-- du script sur une base déjà initialisée (AC #7).
DROP TRIGGER IF EXISTS trg_clients_updated_at    ON clients;
DROP TRIGGER IF EXISTS trg_criteres_updated_at   ON criteres_ciblage;
DROP TRIGGER IF EXISTS trg_campagnes_updated_at  ON campagnes;
DROP TRIGGER IF EXISTS trg_prospects_updated_at  ON prospects;

CREATE TRIGGER trg_clients_updated_at    BEFORE UPDATE ON clients          FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_criteres_updated_at   BEFORE UPDATE ON criteres_ciblage FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_campagnes_updated_at  BEFORE UPDATE ON campagnes        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_prospects_updated_at  BEFORE UPDATE ON prospects        FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
--  NOTES D'IDEMPOTENCE
-- ============================================================
--  Ce script peut être ré-exécuté sur une base déjà initialisée sans erreur
--  (AC #7) grâce à :
--   - CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS
--   - INSERT ... ON CONFLICT DO NOTHING (sources)
--   - CREATE OR REPLACE FUNCTION / VIEW
--   - DROP TRIGGER IF EXISTS + CREATE TRIGGER (ci-dessus)
--  En contexte Docker, /docker-entrypoint-initdb.d ne s'exécute de toute
--  façon qu'au 1er démarrage d'un volume vierge.

-- ============================================================
--  VUE — file d'appel (prospects prêts à appeler)
--  Règle #1 : Bloctel OK ET vérifié il y a moins de 30 jours,
--  et jamais un SIRET sous opposition RGPD.
-- ============================================================
CREATE OR REPLACE VIEW file_appel AS
SELECT
    p.id, p.nom_entreprise, p.nom_dirigeant,
    p.telephone, p.email, p.ville, p.departement,
    p.code_naf, p.effectif, p.score_final, p.statut,
    p.bloctel_verifie_le,
    c.nom AS campagne_nom,
    cl.nom_entreprise AS client_nom
FROM prospects p
JOIN campagnes c  ON c.id = p.campagne_id
JOIN clients  cl  ON cl.id = c.client_id
WHERE
    p.statut = 'qualifie'
    AND p.bloctel_ok = TRUE
    AND p.bloctel_verifie_le > NOW() - INTERVAL '30 days'
    AND p.telephone IS NOT NULL
    AND p.doublon = FALSE
    AND NOT EXISTS (SELECT 1 FROM oppositions_rgpd o WHERE o.siret = p.siret)
ORDER BY p.score_final DESC, p.created_at ASC;
