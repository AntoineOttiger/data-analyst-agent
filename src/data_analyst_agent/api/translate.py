# -*- coding: utf-8 -*-
"""Traduction de protocole : vocabulaire FR maison → JSON ascii/anglais (DESIGN décision 5).

`api/` joue le rôle de traduction du protocole HTTP, pendant de `agent/tools.py`
côté LLM. Le Python reste en français (`Réponse.données`, `Événement`) ; c'est ICI,
à la frontière du fil, que les accents disparaissent des clés et que le vocabulaire
passe en anglais. Aucun modèle Pydantic de sortie : nos dataclasses sont notre
vocabulaire, on sérialise à la main.

Mapping (décision 5) : données→rows, prose→answer, hypothèses→assumptions,
statut→status, sql→sql.
"""

from __future__ import annotations

from typing import Any

from ..agent import Final, Hypothèse, OutilAppelé, RésultatOutil
from ..response import Réponse

# statut de Réponse (FR) → status ascii du contrat HTTP.
_STATUT_RÉPONSE = {"ok": "ok", "échec": "error", "budget_dépassé": "budget_exceeded"}
# statut d'un RésultatOutil (FR) → status ascii.
_STATUT_OUTIL = {"succès": "success", "échec": "error", "timeout": "timeout"}


def réponse_en_dict(rép: Réponse) -> dict[str, Any]:
    """Projette une `Réponse` FR vers le contrat JSON ascii/anglais."""
    return {
        "answer": rép.prose,
        "rows": rép.données,  # list[dict] | None — clés = noms de colonnes SQL (déjà ascii)
        "sql": list(rép.sql),
        "assumptions": list(rép.hypothèses),
        "status": _STATUT_RÉPONSE.get(rép.statut, "budget_exceeded"),
    }


def événement_en_dict(évén: Any) -> dict[str, Any]:
    """Traduit un `Événement` maison en objet JSON ascii pour le fil SSE.

    Le champ `type` porte le discriminant ascii (`tool_call` / `tool_result` /
    `assumption` / `final`) : le front en fait un `switch` exhaustif (décision 9).
    """
    match évén:
        case OutilAppelé():
            return {"type": "tool_call", "name": évén.nom, "args": évén.args}
        case RésultatOutil():
            return {
                "type": "tool_result",
                "sql": évén.sql,
                "status": _STATUT_OUTIL.get(évén.statut, "error"),
                "row_count": évén.lignes,
                "message": évén.message,
            }
        case Hypothèse():
            return {"type": "assumption", "text": évén.texte}
        case Final():
            return {"type": "final", **réponse_en_dict(évén.réponse)}
    # Défensif : un genre d'événement inconnu ne doit pas casser le flux.
    return {"type": "unknown"}
