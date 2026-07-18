# -*- coding: utf-8 -*-
"""Lancement : `python -m data_analyst_agent.api` (sert l'API + le front si build présent).

Charge le `.env` (clé Mistral) AVANT que l'agent ne construise le modèle, comme
le fait `eval.run`.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()  # MISTRAL_API_KEY depuis .env avant tout appel modèle
    import uvicorn

    uvicorn.run(
        "data_analyst_agent.api:app",
        host=os.environ.get("API_HOST", "127.0.0.1"),
        port=int(os.environ.get("API_PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
