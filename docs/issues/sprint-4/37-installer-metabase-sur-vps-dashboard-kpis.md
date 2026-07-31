# #37 — Installer Metabase sur VPS (dashboard KPIs)

> Issue GitHub : https://github.com/95902/Agent-IA-de-prospection-B2B-/issues/37
> État : 🟢 Ouverte
> Sprint : Sprint 4 — Production
> Labels : `monitoring`, `sprint-4`, `metabase`

---

**Sprint :** Sprint 4 — Production (Sem. 7-8)
**Points :** 2 pts
**Labels :** monitoring, metabase, sprint-4

## Objectif
Donner au client B2B (persona PRD) un dashboard KPIs sans dépendance à un accès SQL direct, hébergé sur le même VPS (profil `monitoring` du docker-compose, #6).

## Déploiement
- [ ] Service `metabase` activé (`docker compose --profile monitoring up -d`, port 3000)
- [ ] Connexion Metabase → PostgreSQL configurée (lecture seule recommandée)

## 6 questions/dashboards à construire
- [ ] Répartition des prospects par statut (nouveau / qualifié / appelé / RDV / refus / invalide)
- [ ] Score moyen par département
- [ ] Taux d'enrichissement (téléphone / email) par campagne
- [ ] Évolution du nombre de prospects collectés dans le temps
- [ ] Top 10 des prospects par score
- [ ] KPIs de campagne (prospects collectés, qualifiés, appels passés, RDV obtenus) — cf. cibles PRD section 6

## Critères d'acceptance
- [ ] Les 6 questions sont accessibles depuis un dashboard Metabase unique
- [ ] Les chiffres affichés correspondent à ceux obtenus par requête SQL directe (vérification croisée)


