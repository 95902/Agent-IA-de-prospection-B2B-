"""Configuration pytest — projet « Agent IA de Prospection B2B ».

CLAUDE.md : les tests d'intégration (`@pytest.mark.integration`) tapent de
vraies APIs (INSEE, Tavily, Ollama…) — exclus des runs par défaut. On les
active explicitement avec `pytest -m integration`.
"""
from __future__ import annotations


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    config.addinivalue_line("markers", "integration: tape de vraies APIs (exclu du run par défaut).")


def pytest_collection_modifyitems(config, items) -> None:  # type: ignore[no-untyped-def]
    """Skip les tests marqués `integration` sauf si `-m integration` est passé.

    On match le marker EXACT, pas un substring : `pytest -m integration_db` ne
    doit pas dé-skipper les tests `@pytest.mark.integration` (et réciproquement,
    un test marqué `integration_db` ne doit pas être skippé par la logique
    `integration`). On utilise `item.get_closest_marker("integration")` plutôt
    que `"integration" in item.keywords`.
    """
    # Si le filtre `-m` sélectionne explicitement le marker `integration` exact,
    # on ne skippe pas. On ne fait pas un simple substring check sur l'expression
    # `-m` (qui pourrait contenir `integration_db`, `not integration`, etc.) — on
    # compare au nom de marker via l'API marker de pytest.
    if _filter_selects_integration(config):
        return

    import pytest

    skip_integration = pytest.mark.skip(reason="test d'intégration — lancer avec `pytest -m integration`.")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip_integration)


def _filter_selects_integration(config) -> bool:  # type: ignore[no-untyped-def]
    """True si l'option `-m` sélectionne explicitement le marker `integration`.

    On inspecte les tokens de l'expression `-m` pour le nom de marker exact
    `integration`, pour ne pas confondre avec `integration_db` ou `pre_integration`.
    Une expression comme `integration and not slow` ou `not integration` → True
    (l'utilisateur agit sciemment sur les tests d'intégration).
    """
    expr = config.getoption("-m") or ""
    if not expr:
        return False
    # Tokenisation simple : on regarde les mots de l'expression (hors opérateurs).
    operators = {"and", "or", "not", "(", ")", "True", "False"}
    tokens = {t for t in expr.replace("(", " ").replace(")", " ").split() if t not in operators}
    return "integration" in tokens