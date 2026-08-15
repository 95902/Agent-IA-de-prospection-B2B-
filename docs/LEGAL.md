# LEGAL.md — Obligations légales & conformité (générique, tous secteurs)

> ⚠️ Ce fichier est CRITIQUE. Ne jamais bypasser ces règles.
> Ces obligations s'appliquent à **tout client**, quel que soit son secteur cible.

## ⚠️ MAJ 11 août 2026 — fin de Bloctel (loi n° 2025-594)

La **loi n° 2025-594 du 30 juin 2025** (art. 13, réécrivant l'art. L223-1 du
Code de la consommation) **supprime Bloctel** à compter du **11 août 2026** et
bascule le démarchage téléphonique **B2C** d'un régime d'opposition (opt-out,
Bloctel) vers un régime de **consentement préalable (opt-in)**.

| | Régime au 11 août 2026 |
|---|---|
| **B2C** (consommateur) | **Opt-in.** Appeler sans consentement préalable, libre, spécifique, éclairé et univoque est **interdit**. La preuve du consentement incombe au professionnel. Amende administrative **jusqu'à 375 000 € (personne morale)**. |
| **B2B** (notre cible) | **Inchangé.** Démarcher une personne morale ou un professionnel sur sa **ligne professionnelle**, pour une offre **en lien avec son activité**, reste possible **sans consentement préalable**, sur la base de l'**intérêt légitime** (RGPD art. 6.1.f). |
| **⚠️ Zone grise** | Un **auto-entrepreneur** ou une **ligne mobile personnelle** peut relever du régime consommateur. En cas de doute sur la nature de la ligne, **traiter comme B2C** (opt-in requis avant appel). |

**Conséquence produit :** Bloctel **n'est plus** le mécanisme de conformité.
Le code conserve encore les colonnes `bloctel_*` et `utils/bloctel.py` par
inertie ; leur retrait est un chantier de schéma distinct (issues #20/#40
supprimées par l'équipe le 14 août 2026). **Ne fonder aucune nouvelle logique
d'appel sur Bloctel.** L'appel reste de toute façon en **Phase 2** — le produit
V1 est **email-first**.

## Opposition commerciale — le vrai garde-fou B2B (art. R123-232 c. com.)

Une entreprise peut **s'opposer formellement à l'utilisation commerciale de ses
données** (art. R123-232 du code de commerce), choix exprimé au **Guichet Unique**
lors de l'immatriculation ou via le **RNE**. C'est un **opt-out enregistré**, pas
une zone grise : démarcher une entreprise opposée est précisément ce que ce droit
interdit. **C'est ce filtre — et non Bloctel — qui protège désormais la
prospection B2B.**

- **Mesuré** sur 35 entreprises réelles (Paris, août 2026) : **49 % opposées**,
  et **87 % pour les SIREN récents** (Guichet Unique depuis 2023). Le taux
  augmentera mécaniquement à mesure que le stock d'entreprises se renouvelle.
- **Implémenté** par `utils/opposition_commerciale.py` (#74). Principe **fermé
  par défaut** : ne pas savoir n'est pas une autorisation. Un prospect
  non vérifié n'est **pas** contactable.
- **Règle d'usage** : appeler `peut_etre_contacte()` **avant** tout envoi vers
  un enrichisseur tiers ou toute file de contact. Ne **jamais** utiliser
  `not est_oppose()` — cette expression laisserait passer les non-vérifiés.
- **Source** : seul **Pappers** expose ce champ (`/entreprise`, **1 crédit par
  entreprise**). `statut_diffusion` (Sirene / annuaire-entreprises) est un autre
  concept et ne le renseigne pas.
- **Traçabilité** : valeur + date de vérification conservées dans
  `raw_data['opposition_commerciale']`, pour justifier une exclusion — ou une
  non-exclusion — en cas de contrôle.

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
   (opposition commerciale R123-232 respectée en amont + mention lors de
   chaque contact)

### Sources de données autorisées

```
✅ Sirene INSEE        — API officielle, données publiques
✅ Pages Jaunes        — Annuaire professionnel public
✅ Pappers             — Données INPI publiques (+ opposition commerciale)
✅ OpenStreetMap       — Données ouvertes (ODbL), contacts publics
✅ Site web entreprise — Information publique
✅ Dropcontact         — Email généré algorithmiquement (RGPD certifié)

❌ Réseaux sociaux personnels (Facebook, Instagram perso)
❌ Bases de données achetées sans provenance traçable
❌ Scraping de sources authentifiées (LinkedIn, etc.) — NO-GO structurel
❌ Données sensibles (santé, opinions politiques, etc.)
```

### Droits des personnes — à implémenter

```python
# À mentionner lors de chaque contact commercial :
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

**Ces durées doivent être appliquées par un job automatique**, pas par une purge manuelle. Voir `scripts/purge_rgpd.py` (issue #41, Sprint 4) : cron quotidien qui supprime/anonymise selon ces règles, journalise chaque suppression (nombre de lignes, motif) pour l'audit.

### Dropcontact — conformité email

Dropcontact génère les emails professionnels algorithmiquement
(prénom.nom@entreprise.fr) sans base de données de contact.
Ce service est certifié RGPD et hébergé en Europe.

```python
# Condition d'appel Dropcontact (limiter les coûts — ~79 €/mois selon volume,
# facturation à la réussite)
# Seulement si : email = None ET nom_dirigeant != None
# ET peut_etre_contacte(prospect) == True   (opposition commerciale vérifiée)
```

---

## Obligations lors des appels (Phase 2)

> ⚠️ **Phase 2 uniquement.** Le produit V1 est **email-first** ; aucune
> fonctionnalité d'appel n'est activée tant que la V1 n'a pas de client payant.
> Avant d'activer l'appel, réconcilier le régime loi 2025-594 (opt-in B2C vs
> intérêt légitime B2B, cas auto-entrepreneur/ligne perso — voir en tête de
> fichier).

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
[ ] Filtre opposition commerciale (R123-232) actif AVANT tout enrichissement
    tiers et toute file de contact — peut_etre_contacte(), fermé par défaut
[ ] Job de purge RGPD automatique (6 mois / 3 ans / 1 an / 3 mois) déployé et testé
[ ] Mention RGPD documentée et accessible
[ ] Email DPO configuré
[ ] Politique de conservation des données rédigée
[ ] Aucune source de données illégale dans le pipeline (pas de source authentifiée)
[ ] Dropcontact configuré avec conditions d'usage respectées
[ ] Exclusions (mots_cles_negatifs) configurées par client — aucune liste codée en dur

# --- Uniquement si activation de l'appel (Phase 2) ---
[ ] Régime loi 2025-594 réconcilié (opt-in B2C / intérêt légitime B2B)
[ ] Cas ligne mobile personnelle / auto-entrepreneur traité (traité comme B2C si doute)
[ ] Consentement B2C collecté, horodaté et prouvable si appel de consommateurs
[ ] Script d'appel avec mention d'opposition validé (texte paramétré par client, pas figé)
```
