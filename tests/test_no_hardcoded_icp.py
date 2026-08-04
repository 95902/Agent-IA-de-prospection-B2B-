"""Garde-fou anti-hardcodage ICP (issue #4, livrable #2 — règle #3 CLAUDE.md).

Détecte les valeurs métier ICP codées en dur dans le code Python de
production : codes NAF ou mots-clés sectoriels placés comme **littéraux
string** dans le code (éléments de liste, valeurs de retour, valeurs de
dict). Échoue s'il en trouve en dehors de la whitelist.

Approche AST (et non regex brute) pour éviter les faux positifs :
- un code NAF dans un message d'erreur (`"ex. 4520Z"`) est dans une string
  libre qui n'est pas un littéral pur utilisé comme donnée — on cible les
  `ast.Constant` string dont la valeur *entière* est un code NAF ou un
  mot-clé sectoriel, ce qui exclut les phrases d'exemple ;
- un mot sectoriel dans un nom de clé de seed (`'garages'`) n'est pas
  flaggué car ce n'est pas une donnée de ciblage mais un identifiant.

Limitations assumées (documentées) : le garde-fou ne détecte pas les
hardcodages construits dynamiquement (concaténation, f-string, variable
externe). C'est un garde-fou d'alerte, pas une preuve formelle — il rend
une régression de hardcodage *visible* pour les patterns les plus directs.

Whitelist (valeurs ICP métier légitimes) :
- `config/icp_seed_example.py` — seed pilote, donnée de test explicite
- `tests/` — self-référence (les fixtures de test contiennent des NAF)
- `_bmad/`, `_bmad-output/`, `node_modules`, `.venv`, `docs`, etc.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# Code NAF français : 4 chiffres + 1 lettre majuscule (valeur entière).
_NAF_RE = re.compile(r"^\d{4}[A-Z]$")

# Mots-clés sectoriels typiques d'un hardcodage ICP. Inclut les mots-clés
# positifs/négatifs du seed garages pour qu'une copie en dur dans la logique
# de production soit détectée. Match sur la valeur entière du littéral.
_SECTOR_KEYWORDS = {
    "garage", "garages", "concessionnaire", "concessionnaires",
    # Mots-clés positifs/négatifs du seed pilote (issue #4) :
    "réparation", "multi-marques", "atelier",
    "concession", "groupe", "centrale",
}

# Répertoires exclus du scan.
_EXCLUDE_DIRS = {
    "_bmad", "_bmad-output", "node_modules", ".venv", "venv", ".git",
    "__pycache__", ".pytest_cache", "docs", "tests",
}
# Fichiers exclus (chemins relatifs complets depuis la racine du repo).
_EXCLUDE_FILES = {Path("config", "icp_seed_example.py")}


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if any(part in _EXCLUDE_DIRS for part in path.parts):
            continue
        if rel in _EXCLUDE_FILES:
            continue
        yield path


def _scan(root: Path) -> list[tuple[Path, int, str, str]]:
    """Retourne (fichier, ligne, valeur, raison) pour chaque valeur métier
    ICP trouvée comme littéral string entier dans le code.

    Inspecte tout `ast.Constant` string (élément de liste, valeur de
    retour, valeur de dict, argument de fonction…) dont la valeur entière
    est un code NAF ou un mot-clé sectoriel.
    """
    hits: list[tuple[Path, int, str, str]] = []
    for path in _iter_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            # Un fichier non parsable n'est pas silencieusement ignoré : on
            # le signale pour qu'un humain vérifie qu'il ne cache pas du
            # hardcodage (ex. fichier généré/tronqué).
            hits.append((path, 0, "<syntax error>", "fichier non parsable"))
            continue
        for sub in ast.walk(tree):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                value = sub.value.strip()
                if _NAF_RE.match(value):
                    hits.append((path, sub.lineno, value, "code NAF"))
                elif value.lower() in _SECTOR_KEYWORDS:
                    hits.append((path, sub.lineno, value, "mot-clé sectoriel"))
    return hits


def test_no_hardcoded_icp_values():
    """Aucun code NAF ni mot-clé sectoriel en dur comme littéral string
    entier dans le code Python de production (hors whitelist)."""
    root = Path(__file__).resolve().parent.parent
    hits = _scan(root)
    if hits:
        formatted = "\n".join(
            f"  {p.relative_to(root)}:{lineno} → {raison} '{value}'"
            for p, lineno, value, raison in hits
        )
        pytest.fail(
            "Valeurs métier ICP codées en dur détectées dans le code Python "
            f"(hors whitelist) — hardcodage ICP (règle #3) :\n{formatted}\n"
            "Les valeurs ICP doivent vivre en base (criteres_ciblage) ou "
            "dans config/icp_seed_example.py (donnée de test), pas dans la "
            "logique de production."
        )