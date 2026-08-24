"""Entrypoint ASGI de production : sert le front buildé (dist/) ET l'API sur une
seule origine (same-origin), pour l'exposer derrière un unique gate/tunnel.

Compose l'app FastAPI de `api.main` (endpoints /api/*) et y monte le build Vite
(dist/) avec un fallback SPA. Lancer avec :

    uvicorn deploy.serve:app --host 127.0.0.1 --port 8000

Prérequis :
  - `api/` présent (fusionner la PR #119 d'abord — voir docs/DEPLOY_FRONT_NGROK.md) ;
  - le front buildé et déposé dans `dist/` à la racine du repo.
"""
from __future__ import annotations

import os

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.main import app  # compose l'app existante ; dépend de la PR #119

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIST = os.path.join(_ROOT, "dist")

# Sert les assets hashés du build (JS/CSS) si présents.
if os.path.isdir(os.path.join(_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def _serve_spa(full_path: str):
    """Sert un fichier du build s'il existe, sinon index.html (routing SPA).

    Déclaré APRÈS les routes /api de `api.main` : FastAPI matche les routes
    spécifiques d'abord, donc ce catch-all ne capte que ce que l'API n'a pas servi.
    """
    candidate = os.path.join(_DIST, full_path)
    if full_path and os.path.isfile(candidate):
        return FileResponse(candidate)
    return FileResponse(os.path.join(_DIST, "index.html"))
