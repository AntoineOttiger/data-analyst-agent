# -*- coding: utf-8 -*-
"""`call_model` — appel LLM isolé derrière une fonction (DESIGN §4, SCOPE §5).

Niveau « B-pragmatique » : on digère le format Mistral/LangChain et on rend un
vocabulaire à NOUS (`Décision`, `AppelOutil`). Le vocabulaire LangChain
(`AIMessage`, `ToolMessage`) reste confiné au graphe ; il ne franchit jamais la
frontière de ce module — `call_model` ne rend qu'une `Décision`.

Isoler l'appel ici permet de changer de provider et de diagnostiquer
« agent vs modèle » sans toucher au graphe.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from langchain_core.messages import BaseMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_mistralai import ChatMistralAI

# Mistral free tier ≈ 1 req/s : throttle proactif partagé pour éviter les 429.
_LIMITEUR = InMemoryRateLimiter(
    requests_per_second=float(os.environ.get("MISTRAL_RPS", "0.5")),
    check_every_n_seconds=0.1,
    max_bucket_size=1,
)

# LangChain confiné : on ré-exporte un alias neutre pour le typage du graphe.
Message = BaseMessage

MODÈLE_DÉFAUT = os.environ.get("MISTRAL_MODEL", "mistral-small-2603")


@dataclass
class ToolSpec:
    """Description d'un outil, indépendante du provider (JSON Schema des args)."""

    nom: str
    description: str
    paramètres: dict  # JSON Schema (type=object, properties, required)


@dataclass
class AppelOutil:
    nom: str
    args: dict
    id: str


@dataclass
class Décision:
    """Ce que rend `call_model` — vocabulaire à nous, pas LangChain."""

    appels: list[AppelOutil] = field(default_factory=list)  # vide si le modèle a fini
    texte: str | None = None                                # présent si réponse directe


def _outil_openai(spec: ToolSpec) -> dict:
    """Format function-calling attendu par `bind_tools` (schéma OpenAI)."""
    return {
        "type": "function",
        "function": {
            "name": spec.nom,
            "description": spec.description,
            "parameters": spec.paramètres,
        },
    }


@lru_cache(maxsize=4)
def _llm(modèle: str, temperature: float):
    # La clé vient de l'environnement (MISTRAL_API_KEY), chargée depuis .env par
    # l'appelant (eval.run). max_retries : robustesse réseau (SCOPE §5, retries).
    return ChatMistralAI(
        model=modèle, temperature=temperature, max_retries=6, rate_limiter=_LIMITEUR
    )


def call_model(
    messages: list[Message],
    tools: list[ToolSpec],
    *,
    modèle: str = MODÈLE_DÉFAUT,
    temperature: float = 0.0,
) -> Décision:
    """Un tour de dialogue avec le LLM. Rend une `Décision` neutre.

    - `appels` non vide → le modèle veut appeler des outils ;
    - `texte` non None → réponse directe sans outil (rare : le protocole impose
      de finir par `submit_answer`).
    """
    llm = _llm(modèle, temperature).bind_tools([_outil_openai(t) for t in tools])
    ai = llm.invoke(messages)

    appels = [
        AppelOutil(nom=tc["name"], args=tc.get("args") or {}, id=tc.get("id") or "")
        for tc in getattr(ai, "tool_calls", []) or []
    ]
    texte = None if appels else (ai.content if isinstance(ai.content, str) else str(ai.content))
    return Décision(appels=appels, texte=texte)
