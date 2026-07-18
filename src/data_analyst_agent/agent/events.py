# -*- coding: utf-8 -*-
"""`Événement` — le vocabulaire de streaming, à NOUS (pas LangChain).

`ask_stream()` produit une suite d'`Événement` : la trace ReAct en direct, plus
un `Final` qui porte la `Réponse` publique projetée. Union discriminée par le
champ `type` : un consommateur fait un `match`/`switch` exhaustif dessus.

Ces objets franchissent la frontière du module `agent` (comme `Réponse`) ; les
objets LangChain (`AIMessage`, `ToolMessage`) n'y apparaissent JAMAIS — le graphe
les traduit vers ce vocabulaire au moment du `.stream()` (DESIGN §4, § « LangChain
confiné »). La traduction en ascii/anglais pour le fil HTTP se fait dans `api/`,
pas ici : le Python reste en français.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union

from ..response import Réponse


@dataclass
class OutilAppelé:
    """Le modèle a décidé d'appeler un outil (émis avant l'exécution)."""

    nom: str
    args: dict = field(default_factory=dict)
    type: Literal["outil_appelé"] = "outil_appelé"


@dataclass
class RésultatOutil:
    """Retour d'un `run_query` exécuté : SQL tenté + issue (DESIGN §5)."""

    sql: str
    statut: Literal["succès", "échec", "timeout"] = "succès"
    lignes: int | None = None      # nb de lignes lues si succès
    message: str | None = None     # message brut du moteur si échec/timeout
    type: Literal["résultat_outil"] = "résultat_outil"


@dataclass
class Hypothèse:
    """Une interprétation retenue par le modèle en cas d'ambiguïté."""

    texte: str
    type: Literal["hypothèse"] = "hypothèse"


@dataclass
class Final:
    """Dernier événement : porte la `Réponse` publique (drain-to-final)."""

    réponse: Réponse
    type: Literal["final"] = "final"


# Union discriminée par `type` (miroir de la côté TS du front, DESIGN décision 9).
Événement = Union[OutilAppelé, RésultatOutil, Hypothèse, Final]
