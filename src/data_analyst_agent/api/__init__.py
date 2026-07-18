# -*- coding: utf-8 -*-
"""Module `api` — enrobage HTTP de `agent.ask_stream` (DESIGN §9).

N'expose que l'app FastAPI. Ne parle qu'au package `agent`, jamais à ses
sous-modules (frontière de dépendance, DESIGN §1).
"""

from .app import app, créer_app

__all__ = ["app", "créer_app"]
