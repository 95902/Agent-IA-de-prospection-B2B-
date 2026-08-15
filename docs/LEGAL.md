# LEGAL.md — Obligations légales & conformité (générique, tous secteurs)

> ⚠️ Ce fichier est CRITIQUE. Ne jamais bypasser ces règles.
> Ces obligations s'appliquent à **tout client**, quel que soit son secteur cible.

## RGPD — Traitement des données prospects

### Base légale

**"Intérêt légitime B2B"** (Article 6(1)(f) RGPD)

La collecte et le traitement de données de contact de professionnels
(dirigeants d'entreprises ciblées par l'ICP du client) à des fins de
prospection commerciale B2B est autorisée sous réserve :

1. Que l'activité du prospect soit en lien avec le produit proposé ✅
   (secteur cible du client → produit/service vendu, cohérence documentée
   dans `criteres_ciblage.description_icp`)
2. Que les données soient collectées depuis des sources légales ✅
   (Sirene INSEE, annuaires professionnels publics)
3. Que le professionnel puisse exercer son droit d'opposition ✅
   (à mentionner lors de chaque appel)

### Sources de données autorisées

```
✅ Sirene INSEE        — API officielle, données publiques
✅ Pages Jaunes        — Annuaire professionnel public
✅ Pappers             — Données INPI publiques
✅ Site web entreprise — Information publique
✅ Dropcontact         — Email généré algorithmiquement (RGPD certifié)

❌ Réseaux sociaux personnels (Facebook, Instagram perso)
❌ Bases de données achetées sans provenance traçable
❌ Scraping de sites sans autorisation explicite
❌ Données sensibles (santé, opinions politiques, etc.)
```

### Droits des personnes — à implémenter

```python
# À mentionner lors de chaque appel commercial :
MENTION_RGPD = """
Vos coordonnées proviennent de sources publiques.
Vous pouvez vous opposer à tout traitement de vos données
en nous le signalant par email à [email DPO].
"""

# Droit d'opposition → marquer le prospect
# prospects.statut = 'invalide'
# prospects.notes = 'Opposition RGPD - {date}'
# Ne plus jamais contacter ce SIRET
```

### Durée de conservation

```sql
-- Prospects qualifiés non convertis : 3 ans maximum
-- Prospects invalides : supprimer après 6 mois
-- Historique appels : 1 an
-- Logs système : 3 mois
```

**Ces durées doivent être appliquées par un job automatique**, pas par une purge manuelle. Voir `scripts/purge_rgpd.py` (issue #36, Sprint 4) : cron quotidien qui supprime/anonymise selon ces règles, journalise chaque suppression (nombre de lignes, motif) pour l'audit.

### Dropcontact — conformité email

Dropcontact génère les emails professionnels algorithmiquement
(prénom.nom@entreprise.fr) sans base de données de contact.
Ce service est certifié RGPD et hébergé en Europe.

```python
# Condition d'appel Dropcontact
# Seulement si : email = None ET nom_dirigeant != None ET site_web != None
# Permet de limiter les coûts (24€/mois pour ~1000 enrichissements)
```

---

## Obligations lors des appels

### Script d'introduction obligatoire

```
"Bonjour, je suis [Prénom] de [Entreprise].
Je vous contacte au sujet de [produit_vendu du client — jamais "assurance"
codé en dur, ce texte vient de clients.produit_vendu].

[Si interlocuteur demande d'où vient le numéro :]
'Vos coordonnées sont issues du registre public des entreprises.'

[Si demande d'opposition :]
'Je comprends tout à fait. Je note votre demande et vous ne
serez plus jamais recontacté par notre société.'
→ Mettre à jour statut = 'invalide' + note RGPD dans la BDD
```

### Agent vocal (Phase 2 — Retell AI)

```
⚠️ Loi française : un agent vocal IA DOIT se présenter comme IA
dès le début de l'appel. Ne pas faire passer un bot pour un humain.

Formulation obligatoire :
"Bonjour, je suis un assistant IA de [Entreprise]..."
```

---

## Checklist légale avant mise en production

```
[ ] Job de purge RGPD automatique (6 mois / 3 ans / 1 an / 3 mois) déployé et testé
[ ] Mention RGPD documentée et accessible
[ ] Email DPO configuré
[ ] Politique de conservation des données rédigée
[ ] Script d'appel avec mention d'opposition validé (texte paramétré par client, pas figé)
[ ] Aucune source de données illégale dans le pipeline
[ ] Dropcontact configuré avec conditions d'usage respectées
[ ] Exclusions (mots_cles_negatifs) configurées par client — aucune liste codée en dur
```
