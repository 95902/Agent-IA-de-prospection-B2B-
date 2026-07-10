# LEGAL.md — Obligations légales & conformité (générique, tous secteurs)

> ⚠️ Ce fichier est CRITIQUE. Ne jamais bypasser ces règles.
> Le non-respect de Bloctel expose à une amende jusqu'à 75 000€.
> Ces obligations s'appliquent à **tout client**, quel que soit son secteur cible.

## Bloctel — Liste d'opposition au démarchage téléphonique

### Obligation légale

Tout professionnel effectuant de la prospection téléphonique commerciale
en France **doit vérifier** les numéros contre la liste Bloctel avant appel.

**Base légale :** Article L223-1 et suivants du Code de la consommation.
**Amende :** Jusqu'à 75 000€ par infraction constatée.
**Exception B2B :** La vérification Bloctel s'applique aussi aux professionnels
(quel que soit leur secteur) — le B2B n'exonère pas de l'obligation.

### Règles d'implémentation

```python
# RÈGLE 1 : Vérification AVANT tout appel, SANS EXCEPTION
# Aucun numéro ne doit apparaître dans file_appel sans bloctel_ok = TRUE

# RÈGLE 2 : Trois états possibles
bloctel_ok = True   # ✅ Numéro peut être appelé
bloctel_ok = False  # ❌ INTERDIT d'appeler — exclure de file_appel
bloctel_ok = None   # ⏳ Non vérifié — NE PAS appeler non plus

# RÈGLE 3 : La vue file_appel filtre automatiquement
# WHERE bloctel_ok = TRUE  ← cette condition est non négociable

# RÈGLE 4 : Si API Bloctel indisponible
# → LOG warning critique + NE PAS appeler les numéros non vérifiés
# → NE PAS fallback vers "appel quand même"

# RÈGLE 5 : Re-vérification périodique OBLIGATOIRE
# Un numéro vérifié il y a plus de 30 jours doit être re-vérifié avant
# tout nouvel appel. bloctel_verifie_le (colonne prospects) doit être
# recalculé ; si absent ou > 30 jours → bloctel_ok repasse à NULL et le
# prospect sort de file_appel jusqu'à re-vérification.
# → Job cron dédié, PAS une vérification "au moment de l'appel" seulement.
```

### Compte Bloctel professionnel

```
URL inscription : https://www.bloctel.gouv.fr/
Délai ouverture : 3 à 5 jours ouvrés
Format numéros  : E.164 (+33XXXXXXXXX)
Batch max       : 10 000 numéros par requête
Fréquence       : Vérification obligatoire tous les 30 jours max
```

### Implémentation utils/bloctel.py

```python
async def verifier_batch(numeros: list[str]) -> dict[str, bool]:
    """
    Vérifie une liste de numéros contre la liste Bloctel.
    
    Returns:
        dict: {"+33612345678": True, "+33123456789": False, ...}
        True = peut être appelé
        False = sur liste noire, INTERDIT d'appeler
    """
    # Format E.164 obligatoire
    # Batch de max 10 000 numéros
    # Retry sur timeout (max 3 tentatives)
    # En cas d'erreur API : retourner None pour chaque numéro
    # Logger le résultat : X vérifiés, Y sur liste noire
```

---

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
[ ] Compte Bloctel professionnel ouvert et actif
[ ] Test API Bloctel avec 10 numéros factices
[ ] Vue file_appel vérifiée : WHERE bloctel_ok = TRUE
[ ] Job de re-vérification Bloctel (30 jours) déployé et testé
[ ] Job de purge RGPD automatique (6 mois / 3 ans / 1 an / 3 mois) déployé et testé
[ ] Mention RGPD documentée et accessible
[ ] Email DPO configuré
[ ] Politique de conservation des données rédigée
[ ] Script d'appel avec mention d'opposition validé (texte paramétré par client, pas figé)
[ ] Aucune source de données illégale dans le pipeline
[ ] Dropcontact configuré avec conditions d'usage respectées
[ ] Exclusions (mots_cles_negatifs) configurées par client — aucune liste codée en dur
```
