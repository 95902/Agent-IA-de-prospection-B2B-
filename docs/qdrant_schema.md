{
  "name": "icp_profiles",
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  },
  "payload_schema": {
    "client_id": "keyword",
    "critere_id": "keyword",
    "nom": "text"
  }
}

{
  "name": "prospects_embeddings",
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  },
  "payload_schema": {
    "prospect_id": "keyword",
    "campagne_id": "keyword",
    "code_naf": "keyword",
    "departement": "keyword"
  }
}