# Lancer DOCKER
 docker run --name pg-prospection -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=prospection -p 5433:5432 -d postgres:16

# Modifier ton env posgress en local
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/prospection" 

# Lancer le schéma d'initialisation SQL avec DOCKER
docker exec -i pg-prospection psql -U postgres -d prospection < docker/postgres/init/01_schema.sql  

# Lancer les scripts PYTHON
python scripts/provision_pilot.py
python tests/test_non_hardcoded.py

# Vérifier que l'ICP est enregistré dans la base de donnée
docker exec -it pg-prospection psql -U postgres -d prospection -c "SELECT nom, codes_naf, departements, effectif_min, effectif_max FROM criteres_ciblage;"