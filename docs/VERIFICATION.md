# VERIFICATION.md — Méthode de vérification & de travail assisté par IA

> **Pourquoi ce document.** La vérification est ce qui permet de **déléguer davantage
> en confiance**. Plus les garde-fous ci-dessous sont systématiques, plus on peut confier
> de travail à un agent (ou à un·e coéquipier·e) sans risque de régression silencieuse.
> Ce fichier code les vérifications qui ont **fait leurs preuves sur ce projet** — chacune
> est née d'un incident ou d'un quasi-incident réel, pas d'une bonne intention abstraite.
>
> Il s'adresse **autant aux sessions Claude Code qu'aux humains** de l'équipe.

## Principe directeur : mesurer avant d'affirmer

Ne jamais écrire « c'est fait / c'est vert / c'est fusionné » sans l'avoir **vérifié par une
commande** dont on montre la sortie. Rapporter fidèlement : si un test échoue, le dire avec
la sortie ; si une étape a été sautée, le dire. Une affirmation non mesurée est une hypothèse.

---

## Les garde-fous (dans l'ordre d'une session)

### 1. Reconnaissance — ne rien supposer
`git fetch` + `gh pr list` + `gh issue list` en début de session. L'état réel prime sur la
mémoire, le plan, ou ce qu'« on croit » fusionné.

### 2. Base verte AVANT de construire
Établir une suite de tests **verte** sur la base fusionnée avant d'ajouter du code — sinon on
hérite du rouge d'autrui comme « sa » régression. Commande de référence (Windows / venv) :

```bash
PYTHONIOENCODING=utf-8 PYTHONPATH=. ./.venv/Scripts/python.exe -m pytest tests/ -q -m "not integration"
```

### 3. Le piège des PR empilées — vérifier le CONTENU, pas le badge
**Incident réel** : deux PR affichées « merged » ne sont jamais arrivées sur `main` (dont un
filtre **légal**), parce qu'empilées et fusionnées dans des branches mortes. Le badge ment.

Après toute fusion supposée :

```bash
git merge-base --is-ancestor <merge-commit> origin/main   # code 0 = vraiment ancêtre de main
git ls-tree origin/main -- <fichier>                       # le fichier est-il là ?
git grep <symbole> origin/main -- <fichier>                # le CONTENU est-il là ?
```

### 4. Réconciliation arithmétique des tests
`baseline + nouveaux = total attendu`. **Si ça ne tombe pas juste, enquêter** — ne pas se
contenter de « tout est vert ». Ce contrôle a détecté un **fichier de test écrasé** (2 tests
perdus en silence : un `Write` avait remplacé un fichier existant). Outils :

```bash
# compter par périmètre pour localiser l'écart
pytest tests/test_X.py -q ; pytest tests/ --ignore=tests/test_X.py -q
# diff des tests réellement collectés
pytest tests/ --collect-only -q | sort > a ; ... ; comm -23 a b
```

### 5. Grounding contre le vrai code (anti-dérive)
Réconcilier une doc / réutiliser une fonction ? **Lire le code réellement fusionné**, pas le
mémo ni la doc (qui dérivent). Vérifier qu'un symbole ou une signature **existe** avant de s'y
référer (`git grep … origin/main`). La doc `SCORING.md` avait dérivé du modèle Pydantic livré —
c'est la lecture du code qui l'a rattrapé, pas la confiance dans le pseudocode.

### 6. Dépendances & APIs externes
- Vérifier qu'un paquet est **installé dans le venv** avant de compter dessus (pas seulement
  déclaré dans `requirements.txt`) — un `from anthropic import …` en tête de module casse
  sinon **toute** la collecte de tests.
- **Ne jamais halluciner une API externe.** Vérifier la doc officielle / charger le skill
  avant d'écrire (ex. : `wrap_anthropic` n'étant pas confirmé par la doc LangSmith, on ne
  l'a pas utilisé). « Chercher quand on n'est pas sûr », pas inventer.

### 7. Discipline de fusion
- **Une PR = une base `main`** (défaut). Pas d'empilement sauf nécessité assumée.
- Fichiers **disjoints** entre PR → fusionnables dans n'importe quel ordre.
- Si empilement inévitable : **ordre de fusion en gras** en tête de description de chaque PR
  concernée, **et** vérification `ls-tree`/`merge-base` après chaque fusion (cf. §3).

### 8. Vérification post-Edit
Un `Edit` qui rapporte « succès » ne garantit pas qu'il a pris. Si le comportement surprend
(un test échoue « impossible »), **re-lire le fichier** — un edit a rapporté succès **sans
s'appliquer** cette session ; seule la relecture l'a révélé.

### 9. Tests : unitaires vs intégration
- **Unitaires** : réseau **mocké** (Ollama / Qdrant / Claude / PostgreSQL), aucun appel réel,
  aucune clé requise, pas de marqueur.
- **Intégration** : `@pytest.mark.integration`, opt-in, **exclus par défaut** (`-m "not
  integration"`). Ils tapent de vraies APIs / la vraie stack Docker.

---

## La boucle de travail (par item / PR)

```
1. Lire le vrai code de la base (grounding)          →  §5
2. Écrire le code + les tests
3. Lancer les tests (périmètre ciblé, puis total)    →  §2
4. Réconcilier l'arithmétique des tests              →  §4
5. Checkpoint : montrer le delta + les tests verts
6. PR brouillon, base main, description explicite     →  §7
```

Un item n'est « fait » qu'après l'étape 4, pas après l'étape 2.

---

## Handoff de session (préparer la suivante)

- Tenir à jour le mémo de reprise : **état de `main`, PR ouvertes + ordre de fusion,
  prochaine étape, pièges connus**. Une session fraîche doit pouvoir reprendre sans re-déduire.
- Convertir les dates relatives en absolues.
- Le plan complet vit dans `~/.claude/plans/` ; les faits durables dans la mémoire projet.
- **Ne jamais laisser une doc diverger du code sans le signaler** (agents.md).

---

## Commandes & pièges de référence (ce repo)

| Besoin | Commande / note |
|---|---|
| Tests (venv Windows) | `PYTHONIOENCODING=utf-8 PYTHONPATH=. ./.venv/Scripts/python.exe -m pytest tests/ -q -m "not integration"` |
| `gh` CLI | dans `C:\Program Files\GitHub CLI` (ajouter au PATH) |
| Stack locale | `docker compose --profile dev up -d` (pas de `make` garanti sous Windows) |
| pip | **ne pas** `pip install --upgrade pip` |
| Fins de ligne | `.gitattributes` force LF sur `*.sh` — ne pas réintroduire de CRLF (casse les entrypoints Docker) |

---

## L'échelle d'autonomie (adoption)

Chaque garde-fou ci-dessus est ce qui **autorise à monter d'un cran** dans la délégation :

1. **Assisté** — on vérifie chaque ligne produite.
2. **Supervisé** — on confie une fonction, on vérifie par des tests unitaires ciblés.
3. **Délégué par item** — on confie un item entier (une PR) ; la confiance repose sur
   *tests verts + réconciliation arithmétique + contenu vérifié sur `main`*, pas sur l'espoir.
4. **Délégué en parallèle** — plusieurs items disjoints en vol, chacun avec ses propres
   garde-fous et son ordre de fusion explicite.

La confiance se **gagne par la vérification**, jamais par défaut. Descendre d'un cran dès
qu'un garde-fou saute (un compte de tests qui ne tombe pas juste, un badge « merged » non
vérifié) — puis remonter une fois la cause comprise.
