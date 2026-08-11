-- ============================================================
--  FIXTURES DE TEST — node init_campagne (issue #16)
-- ============================================================
--  Client pilote GÉNÉRIQUE + critères de ciblage + campagne de test.
--  Noms neutres — AUCUN secteur codé en dur (règle #3 CLAUDE.md) :
--  on ne code ni « garage », ni code NAF métier, ni mot-clé sectoriel
--  dans ces fixtures. Les valeurs ci-dessous sont arbitraires et
--  représentent un ICP de test universel.
--
--  Usage :
--    psql -d prospection_b2b -f tests/fixtures/init_campagne_test_data.sql
--  Idempotent : utilise ON CONFLICT DO NOTHING sur des UUIDs fixes.
-- ============================================================

-- UUIDs fixes pour reproductibilité des tests d'intégration (#16).
-- Client pilote générique « Prospecte SARL ».
-- NB : ces UUIDs sont volontairement stables pour que les tests
-- d'intégration puissent y faire référence sans magic strings.
INSERT INTO clients (
    id, nom_entreprise, secteur, produit_vendu, zone_intervention,
    contact_nom, contact_email, statut
) VALUES (
    '11111111-1111-4111-8111-111111111111',
    'Prospecte SARL',           -- nom neutre, non sectoriel
    'conseil',                  -- secteur du CLIENT (pas de la cible)
    'accompagnement commercial',
    'France',
    'Alice Pilote',
    'alice.pilote@example.test',
    'essai'
)
ON CONFLICT (id) DO NOTHING;

-- Critères de ciblage GÉNÉRIQUES de ce client (ICP de test).
-- Aucune valeur métier sectorielle : codes NAF et mots-clés
-- sont des placeholders neutres pour valider le chargement.
INSERT INTO criteres_ciblage (
    id, client_id, nom, description_icp,
    codes_naf, departements,
    effectif_min, effectif_max, anciennete_min_ans,
    exiger_site_web, exiger_email,
    mots_cles_positifs, mots_cles_negatifs,
    actif
) VALUES (
    '22222222-2222-4222-8222-222222222222',
    '11111111-1111-4111-8111-111111111111',
    'Cible test pilote',                       -- nom neutre
    'Profil cible de test pour validation du pipeline',
    ARRAY['6201Z', '6202Z'],                   -- NAF placeholders (programmation)
    ARRAY['75', '92'],
    3, 50, 2,
    TRUE, FALSE,
    ARRAY['qualite', 'service'],               -- mots-clés positifs neutres
    ARRAY['exclusion1', 'exclusion2'],         -- mots-clés négatifs neutres
    TRUE
)
ON CONFLICT (id) DO NOTHING;

-- Profil ICP associé (pour le lien qdrant_point_id).
INSERT INTO icp_profiles (
    id, client_id, critere_id, nom, description,
    qdrant_point_id, embedding_version, actif
) VALUES (
    '33333333-3333-4333-8333-333333333333',
    '11111111-1111-4111-8111-111111111111',
    '22222222-2222-4222-8222-222222222222',
    'ICP test pilote',
    'Description ICP de test pour validation init_campagne',
    '33333333-3333-4333-8333-333333333333',   -- = icp_profile.id (idempotence #12)
    'nomic-embed-text',
    TRUE
)
ON CONFLICT (id) DO NOTHING;

-- Campagne de test rattachée au critère ci-dessus.
INSERT INTO campagnes (
    id, client_id, critere_id, icp_profile_id,
    nom, statut, max_prospects, config_scoring
) VALUES (
    '44444444-4444-4444-8444-444444444444',
    '11111111-1111-4111-8111-111111111111',
    '22222222-2222-4222-8222-222222222222',
    '33333333-3333-4333-8333-333333333333',
    'Campagne test pilote',
    'brouillon',
    100,
    '{"poids_regles":0.35,"poids_llm":0.45,"poids_embedding":0.20}'::JSONB
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================
--  Nettoyage (optionnel — pour rejouer proprement) :
--    DELETE FROM campagnes    WHERE id = '44444444-4444-4444-8444-444444444444';
--    DELETE FROM icp_profiles WHERE id = '33333333-3333-4333-8333-333333333333';
--    DELETE FROM criteres_ciblage WHERE id = '22222222-2222-4222-8222-222222222222';
--    DELETE FROM clients WHERE id = '11111111-1111-4111-8111-111111111111';
-- ============================================================