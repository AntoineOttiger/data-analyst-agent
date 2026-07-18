# -*- coding: utf-8 -*-
"""Enrobage HTTP de `ask_stream()` (DESIGN §9, décision 4).

Frontière de dépendance (DESIGN §1) : cette couche ne parle QU'À `agent`
(`ask_stream` / `Événement` / `Réponse`), jamais à `agent.graph` ni `agent.tools`.
Elle ajoute UNE responsabilité : le transport HTTP + la traduction de protocole
ascii (déléguée à `translate.py`).

Endpoints :
- `POST /api/ask`   → SSE (`text/event-stream`) : un `data:` JSON par événement.
- `GET  /api/health`→ sonde de vie.
- `/`               → `frontend/dist/` en StaticFiles si le build existe (mode démo :
                      un seul process sert l'API et le front — décision 7).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..agent import ask_stream
from .translate import événement_en_dict

# frontend/dist à la racine du repo : ce fichier est à src/data_analyst_agent/api/app.py
# → remonter de 4 niveaux (api → data_analyst_agent → src → racine).
_RACINE = Path(__file__).resolve().parents[3]
_DIST = _RACINE / "frontend" / "dist"


class QuestionEntrée(BaseModel):
    """Pydantic en ENTRÉE seulement (décision 4). Le seul champ du fil montant."""

    question: str


def _sse(objet: dict) -> str:
    """Sérialise un objet en un événement SSE (`data: <json>\\n\\n`).

    `ensure_ascii=False` : le JSON peut contenir des accents dans les VALEURS
    (la prose française) — l'encodage UTF-8 de la réponse HTTP les porte. Seules
    les CLÉS sont ascii, garanti par la couche de traduction."""
    return "data: " + json.dumps(objet, ensure_ascii=False) + "\n\n"


def _flux_sse(question: str) -> Iterator[str]:
    """Générateur SSE : itère `ask_stream()` et traduit chaque événement.

    Générateur SYNCHRONE : FastAPI l'exécute dans un threadpool, ce qui n'entrave
    pas la boucle d'événements pendant les attentes du throttle/LLM."""
    for évén in ask_stream(question):
        yield _sse(événement_en_dict(évén))


def créer_app() -> FastAPI:
    app = FastAPI(title="data-analyst-agent", docs_url="/api/docs", openapi_url="/api/openapi.json")

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/ask")
    def ask_endpoint(entrée: QuestionEntrée) -> StreamingResponse:
        return StreamingResponse(
            _flux_sse(entrée.question),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # désactive le buffering d'un éventuel proxy
            },
        )

    # Monté EN DERNIER : catch-all du front, ne masque pas /api/*. Absent en dev
    # (le front tourne sous Vite:5173 qui proxifie /api → :8000, décision 7).
    if _DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")

    return app


app = créer_app()
