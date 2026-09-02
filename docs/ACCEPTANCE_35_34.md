# Relevé d'acceptance — #35 (1ʳᵉ campagne 500) + #34 (cron campagnes)

> Clôture de **#35** (première campagne réelle de 500 prospects) et de **#34** (cron campagnes
> automatiques — **configuré, volontairement désactivé**). **Mesuré, pas déclaré.**

## #35 — Première campagne réelle (500 prospects, pilote)

**Run pilote exécuté le 2026-09-01** — `CAMPAGNE_ID = b3d7b46e-110f-49e8-adbc-aaed7f9faa9c`,
ICP hôtels indépendants (NAF 5510Z/5520Z, Paris + Hauts-de-Seine), OSM `tourism=hotel` activé.

### Transparence — incident + reprise
Le 1ᵉʳ passage a tourné avec une **clé Anthropic expirée** → les scorings ont basculé en repli
règles-only *sans erreur pipeline*. Détecté par inspection du log (pas par le pipeline), clé
corrigée, puis **re-score en place des 500** (Claude seul, 0 Tavily) : **499/500 scorings LLM
réels**. Cet incident a produit le garde-fou préflight (#128) et le constat « fusionné ≠ actif ».

### Résultat mesuré
| Métrique | Valeur |
|---|---|
| Prospects collectés | **500** |
| Scorings Claude réels | **499 / 500** |
| Qualifiés (score_final ≥ 60) | **72 — 14,4 %** |
| Couverture contact (OSM on) | tél 15,8 % · email 14,4 % · site 31,4 % |
| **Actionnables (qualifié ET joignable)** | **~55 = 11 %** |

### Preuves
- **Compteurs campagne** (BDD prod) : `collectes = 500`, `qualifies = 72`.
- **LangSmith** — projet **`prospection-b2b`** (endpoint EU) trace chaque `score_llm_claude` :
  confirme des scorings **réels** (latence ~2 s, `end` verts), pas le repli dégradé.
- **Livrable** : CSV des **72 qualifiés** (contacts + scores + justification Claude), **remis au
  porteur hors-repo**. 🔒 **RGPD** : le CSV contient des PII d'entreprises réelles (nom, SIRET,
  tél/email) → **non committé** dans ce dépôt public. Métriques agrégées uniquement ci-dessus.

### Périmètre & suite
- **Client = placeholder** (validation produit, décision D5 : pas de société externe). #35 est clos
  comme **jalon « 1ʳᵉ campagne de 500 exécutée + mesurée »** ; une campagne **client commercial** réel
  reste un travail futur (Phase 2).
- L'investigation de suivi (recompute + tests secteur/taille) a montré que **le goulot du rendement
  actionnable est la JOIGNABILITÉ, pas le scoring** — et que **cibler des établissements établis
  (effectif ≥ 10) ~double l'actionnable** (19,3 %). Détail : `docs/ACCEPTANCE_39.md` + filtre taille
  `scripts`/`sirene_agent.py` (#130).

## #34 — Cron campagnes automatiques (lundi 6h)

**Configuré, volontairement DÉSACTIVÉ.** La configuration a été livrée via PR **#127** (vérifiée sur `main`) :
- `deploy/cron/prospection-campagne.cron.disabled` — la ligne cron (lundi 6h,
  `run_campagne.sh <id> 500`) **en commentaire = inerte**, prête à activer.
- `docs/RUNBOOK_35_34_SEPT1.md` — runbook d'activation (décommenter + `crontab`) + logrotate validé.

🔴 **Volontairement non activé** : un cron campagne consomme des crédits (INSEE + Tavily + Claude) à
chaque run. Il ne doit être activé qu'avec un **ICP validé**, un `--limit` borné et un **feu vert crédits
explicite** — décision métier, pas une tâche de configuration. La **configuration (#34) est donc livrée** ;
l'activation reste gatée (et désormais protégée par le préflight #128).

## Portée

- **Document uniquement**, base `main`, PR autonome. **`Closes #35` et `Closes #34` au merge** (décision équipe).
- #34 est clos comme **« cron configuré + documenté »** ; son **activation** reste une décision crédits séparée.
- *(Pour mémoire : #36 Airtable est déjà clos via PR #122 — hors périmètre de ce relevé.)*
