"""`Réponse` — le vocabulaire public partagé (DESIGN §3).

Placée à la racine du package (pas dans `agent/`) : c'est le contrat entre
`agent` (producteur) et l'appelant / la future GUI (consommateur). Neutre, elle
ne couple pas la GUI aux entrailles de l'agent. Le `State` interne du graphe est
un sur-ensemble de `Réponse` ; `ask()` projette l'un vers l'autre.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Statut = Literal["ok", "échec", "budget_dépassé"]


@dataclass
class Réponse:
    prose: str                              # réponse en langage naturel
    données: list[dict] | None = None       # lignes brutes de la requête finale (GUI)
    sql: list[str] = field(default_factory=list)          # TOUTES les requêtes (audit) — rempli par le code
    hypothèses: list[str] = field(default_factory=list)   # interprétations retenues
    statut: Statut = "ok"
