# PRD — Agent IA de Prospection B2B (Multi-secteurs)

## 1. Vision produit

Permettre à n'importe quelle entreprise B2B de prospecter, à grande échelle et sans équipe commerciale dédiée, les entreprises correspondant à son profil client idéal (ICP) — quel que soit le secteur cible. L'agent collecte, enrichit, qualifie et priorise automatiquement les prospects selon l'ICP propre à chaque client — le commercial n'a plus qu'à appeler dans l'ordre de la file.

**Exemples d'usage** : un courtier en assurance ciblant des garages automobiles, un éditeur SaaS RH ciblant des PME industrielles, une agence de recrutement ciblant des cabinets comptables. Le produit ne présuppose aucun secteur — l'ICP est une configuration, pas du code.

## 2. Problème résolu

Un commercial humain appelle 30 à 50 prospects par jour, sans tri de qualité. Il perd 60% de son temps sur des numéros invalides, des grands groupes hors cible ou des prospects qui ne correspondent pas à l'ICP. Le taux de conversion appels → RDV est de 1.5 à 4%, quel que soit le secteur.

**Avec l'agent :** 500 prospects collectés et scorés automatiquement chaque lundi matin, selon l'ICP défini par le client. Le commercial appelle uniquement les prospects qualifiés (score ≥ 60), dans l'ordre décroissant de score. Volume × Qualité, pour n'importe quel secteur cible.

## 3. Utilisateurs cibles

| Persona | Rôle | Besoin principal |
|---|---|---|
| **Le client B2B** | Propriétaire / dirigeant / responsable commercial | Configurer son ICP (secteur cible, codes NAF, zone, effectif), voir les KPIs, lancer des campagnes |
| **Le commercial** | Téléprospecteur | File d'appel triée, fiche prospect claire |
| **L'admin tech** | Dev / ops | Monitoring pipeline, logs, coûts API |

## 4. User stories prioritaires

### Client B2B
- En tant que client, je veux définir mon ICP (description texte, codes NAF, départements, effectif cible, mots-clés positifs/négatifs) pour que l'agent sache quelles entreprises cibler dans mon secteur.
- En tant que client, je veux configurer une campagne (zone, codes NAF, effectif cible) pour définir quelles entreprises prospecter, indépendamment du secteur d'activité.
- En tant que client, je veux voir un dashboard avec le nombre de prospects qualifiés, le score moyen et le taux d'enrichissement.
- En tant que client, je veux recevoir un rapport hebdomadaire par email avec les métriques de la semaine.

### Commercial
- En tant que commercial, je veux une file d'appel triée par score pour appeler les meilleurs prospects en premier.
- En tant que commercial, je veux voir sur chaque fiche : le nom du dirigeant, le téléphone direct, la justification IA du score (basée sur l'ICP du client), et les signaux positifs/négatifs.
- En tant que commercial, je veux marquer un appel comme "RDV obtenu", "Refus" ou "Absent" en un clic.

### Admin tech
- En tant qu'admin, je veux un smoke test automatique pour vérifier que la stack Docker démarre correctement.
- En tant qu'admin, je veux des logs structurés (Loguru) avec métriques de chaque étape du pipeline.
- En tant qu'admin, je veux voir le coût de chaque run (tokens Claude, requêtes Tavily) dans LangSmith, par client.

## 5. Périmètre MVP (9 semaines)

### IN SCOPE
- Collecte Sirene INSEE (codes NAF **configurables par client/campagne**, aucun code sectoriel figé)
- Enrichissement contacts (téléphone + email) via Tavily + Crawl4AI
- Scoring hybride 3 couches (règles génériques + Claude + embeddings), calibré sur l'ICP du client, pas sur un secteur
- File d'appel PostgreSQL (vue `file_appel`)
- Sync Airtable (CRM équipe commerciale)
- Déploiement VPS OVH Docker
- CLI Python (main.py) paramétré par `client_id` / `campagne_id`

### OUT OF SCOPE MVP
- Agent vocal automatisé (Phase 2 — Retell AI)
- Pipeline mailing automatique (Phase 2 — Brevo)
- Interface web SaaS self-service pour créer un ICP (Phase 2 — MVP = configuration en base via script/admin)
- XGBoost supervisé (Phase 3 — après 200+ appels labelisés, par client)

## 6. KPIs de succès MVP

| Métrique | Cible |
|---|---|
| Prospects collectés / semaine (par client) | ≥ 500 |
| Taux enrichissement téléphone | ≥ 40% |
| Taux enrichissement email | ≥ 20% |
| % prospects qualifiés (score ≥ 60) | ≥ 30% |
| Score moyen des qualifiés | ≥ 65/100 |
| Accord humain/score IA | ≥ 75% |
| Coût / prospect qualifié | ≤ 0.15€ |
| Durée pipeline 500 prospects | ≤ 45 min |
| Taux appels → RDV | ≥ 2% (vs 1.5% sans outil) |

## 7. Contraintes non fonctionnelles

- **Performance** : pipeline 500 prospects en moins de 45 minutes sur CPU OVH
- **Fiabilité** : fallback si Claude API down (scoring règles uniquement)
- **RGPD** : base légale "intérêt légitime B2B" documentée, purge automatique selon la politique de rétention, Dropcontact RGPD EU
- **Coût** : moins de 90€/mois par client actif en phase MVP
- **Scalabilité** : PostgreSQL + Qdrant supportent jusqu'à 100k prospects par client sans migration
- **Généricité** : aucune constante métier (secteur, NAF, marque à exclure) codée en dur — tout passe par la configuration ICP du client

## 8. Roadmap phases

```
Phase 1 — MVP (9 sem.)   : Collecte + Scoring + File d'appel + VPS, multi-secteurs dès le départ
Phase 2 (mois 3-4)       : Agent vocal Retell AI + Mailing Brevo + Cal.com
Phase 3 (mois 5-6)       : XGBoost supervisé par client + Interface web self-service ICP
Phase 4 (mois 7+)        : SaaS complet + facturation + onboarding multi-clients
```

## 9. Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Quota Tavily épuisé | Moyenne | Fort | Fallback DuckDuckGo natif |
| Claude API down | Faible | Moyen | Fallback scoring règles uniquement |
| Taux enrichissement < 40% | Moyenne | Moyen | Ajouter Pappers API Phase 2 |
| VPS CPU insuffisant | Faible | Fort | Upgrade OVH ou migration Hetzner |
| ICP mal calibré par un client (barème générique inadapté à son secteur) | Moyenne | Moyen | Audit qualité scores (issue #27) + ajustement des poids par campagne |
