"""Types de retour du module `db` — internes à db (DESIGN §3).

`Result` et `Échec` sont des VALEURS, pas des exceptions : un SQL invalide ou un
timeout est un événement normal de la boucle ReAct (le signal d'auto-correction),
pas une panne. Les vraies pannes (fichier absent, connexion morte) remontent en
exception depuis `sqlite.py` (DESIGN §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Result:
    """Un SUCCÈS de requête.

    `lignes` est brut (`list[tuple]`) : forme naturelle du curseur, gère les
    colonnes homonymes. La conversion en `list[dict]` est une projection de
    l'agent, pas une responsabilité de db (DESIGN §3).
    """

    colonnes: list[str]          # noms, dans l'ordre
    lignes: list[tuple]          # jusqu'à `cap` lues, brutes
    tronqué: bool                # a-t-on arrêté de lire avant la fin ?
    lignes_lues: int             # commodité (== len(lignes))


@dataclass
class Échec:
    """SQL invalide OU timeout dépassé — une valeur rendue par `run_query`.

    `message` est le message brut du moteur, tel quel : c'est le signal
    d'auto-correction passé au LLM sans traduction (ne pas perdre de signal).
    """

    message: str
    genre: Literal["sql_invalide", "timeout"]
