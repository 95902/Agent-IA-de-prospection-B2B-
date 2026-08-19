"""Test de structure — issue #11 (arborescence projet Python).

Valide les critères d'acceptance de #11 :
1. `python main.py --help` fonctionne.
2. Tous les modules inter-modules s'importent (pas d'ImportError) — y compris
   les stubs qui ne chargent leurs dépendances qu'au runtime.
3. Les stubs métiers lèvent NotImplementedError (et non une autre erreur
   d'import) — preuve que l'arborescence est cohérente.

Ce test NE dépend pas des services Docker (PG/Qdrant/Ollama) : on n'appelle
pas les fonctions, on vérifie juste que la structure s'importe.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Modules qui doivent s'importer sans erreur. Les modules métier en stub
# lèvent NotImplementedError à l'appel, pas à l'import.
IMPORTABLE_MODULES = [
    "config",
    "config.settings",
    "config.icp_seed_example",
    "agents",
    "agents.sirene_agent",
    "agents.enrichissement_agent",
    "agents.nettoyage_agent",
    "agents.scoring_agent",
    "graph",
    "graph.state",
    "graph.workflow",
    "models",
    "models.prospect",
    "models.score",
    "utils",
    "utils.db",
    "utils.embeddings",
    "utils.bloctel",
    "utils.dropcontact",
    "utils.airtable_sync",
    "utils.logger",
    "scripts",
    "scripts.smoke_test",
    "scripts.init_icp",
    "scripts.rapport_hebdo",
]


@pytest.mark.parametrize("module", IMPORTABLE_MODULES)
def test_module_imports(module: str) -> None:
    """AC #3 : tous les imports inter-modules se résolvent (pas d'ImportError)."""
    importlib.import_module(module)


def test_main_help_runs() -> None:
    """AC #1 : `python main.py --help` fonctionne (même en stub)."""
    # argparse sort l'aide sur stdout et termine avec SystemExit(0).
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, f"main.py --help a échoué :\n{result.stderr}"
    assert "prospection" in result.stdout.lower()
    # CLI à flags plats (#29) : les 3 modes doivent apparaître dans l'aide.
    assert "--campagne-id" in result.stdout
    assert "--list-campagnes" in result.stdout
    assert "--dry-run" in result.stdout


def test_main_no_command_errors() -> None:
    """`python main.py` sans aucun mode → usage error (exit 2)."""
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=_REPO_ROOT,
    )
    # main() appelle parser.error(...) quand ni --campagne-id, ni --depts/--naf,
    # ni --list-campagnes → argparse sort avec code 2 (usage error).
    assert result.returncode == 2
    assert "usage:" in result.stderr.lower() or "usage:" in result.stdout.lower()


def test_etat_agent_is_typeddict() -> None:
    """L'état partagé du graphe est bien un TypedDict (graph/state.py)."""
    from graph.state import EtatAgent

    # TypedDict conserve __annotations__.
    assert hasattr(EtatAgent, "__annotations__")
    assert "client_id" in EtatAgent.__annotations__


def test_icp_seed_example_has_expected_shape() -> None:
    """config/icp_seed_example.py expose un dictionnaire ICP bien formé (exemple).

    NB : issue #4 (déjà sur main) a remplacé le stub `ICP_SEED_EXAMPLE` par
    `ICP_SEEDS` (dict de dicts, un par secteur pilote). On valide le contrat
    du seed « garages ».
    """
    from config.icp_seed_example import ICP_SEEDS

    assert "garages" in ICP_SEEDS
    seed = ICP_SEEDS["garages"]
    expected_keys = {
        "nom", "description_icp", "codes_naf", "departements",
        "effectif_min", "effectif_max", "anciennete_min_ans",
        "exiger_site_web", "exiger_email",
        "mots_cles_positifs", "mots_cles_negatifs",
    }
    assert expected_keys.issubset(seed.keys())


def test_prompt_templates_exist() -> None:
    """Les templates Jinja du scorer sont présents."""
    from pathlib import Path

    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    assert (prompts_dir / "scorer_system.txt.j2").is_file()
    assert (prompts_dir / "scorer_user.txt.j2").is_file()


def test_run_campagne_script_is_lf() -> None:
    """CLAUDE.md / .gitattributes : run_campagne.sh doit avoir des fins de ligne LF."""
    from pathlib import Path

    script = _REPO_ROOT / "scripts" / "run_campagne.sh"
    content = script.read_bytes()
    # Aucun CR (0x0D) — ni CRLF ni CR seul (Mac classique / sed Windows mal exécuté),
    # les deux cassant l'entrypoint bash Docker (cf. piège CLAUDE.md / .gitattributes).
    assert b"\r" not in content, "run_campagne.sh contient des CR (piège docker)."