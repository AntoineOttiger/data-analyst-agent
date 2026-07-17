# -*- coding: utf-8 -*-
"""Module `agent` — n'expose que `ask` (DESIGN §1).

Tout le reste (graphe, nœuds, outils, prompt, State) est caché : importer un
sous-module depuis l'extérieur signale une frontière violée.
"""

from .graph import ask

__all__ = ["ask"]
