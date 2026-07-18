# -*- coding: utf-8 -*-
"""Module `agent` — interface étroite (DESIGN §1, décision 11).

Expose la primitive de streaming `ask_stream` (trace ReAct en direct), sa forme
drain-to-final `ask`, et le vocabulaire d'événements (`Événement` + variantes).
Tout le reste (graphe, nœuds, outils, prompt, State) reste caché : importer un
sous-module depuis l'extérieur signale une frontière violée.
"""

from .events import Événement, Final, Hypothèse, OutilAppelé, RésultatOutil
from .graph import ask, ask_stream

__all__ = [
    "ask",
    "ask_stream",
    "Événement",
    "OutilAppelé",
    "RésultatOutil",
    "Hypothèse",
    "Final",
]
