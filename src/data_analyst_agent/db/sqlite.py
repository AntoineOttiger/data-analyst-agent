"""Implémentation SQLite du protocole `Database` (DESIGN §2, SCOPE §6).

Trois défenses mécaniques qui ne dépendent jamais du LLM :
  1. connexion read-only au niveau moteur (`file:...?mode=ro`) → écriture
     physiquement impossible ;
  2. `fetchmany(cap+1)` → on borne ce qu'on LIT, sans réécrire le SQL de l'agent
     (un LIMIT injecté fausserait les agrégats / GROUP BY) ;
  3. timeout d'exécution via `connection.interrupt()` depuis un timer.

Frontière d'erreurs (DESIGN §5) : SQL invalide et timeout → valeur `Échec`.
Vraie panne (fichier absent, disque plein) → exception qui remonte et crashe.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from .result import Result, Échec

CHEMIN_DÉFAUT = Path("database/chinook.db")
TIMEOUT_DÉFAUT_S = 5.0


class SQLiteDatabase:
    """`Database` sur un fichier SQLite ouvert en lecture seule."""

    def __init__(self, chemin: Path, timeout_s: float = TIMEOUT_DÉFAUT_S) -> None:
        self._chemin = chemin
        self._timeout_s = timeout_s
        # mode=ro : le moteur refuse toute écriture. uri=True active file:.
        # Fichier absent → OperationalError ici = vraie panne, elle remonte.
        uri = f"file:{chemin.as_posix()}?mode=ro"
        self._cx = sqlite3.connect(uri, uri=True, check_same_thread=False)

    @property
    def dialecte(self) -> str:
        return "sqlite"

    def list_tables(self) -> list[str]:
        cur = self._cx.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        return [ligne[0] for ligne in cur.fetchall()]

    def get_schema(self, table: str) -> str:
        """DDL de la table (le CREATE TABLE d'origine). Paramétré → pas
        d'injection par le nom de table."""
        cur = self._cx.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        )
        ligne = cur.fetchone()
        if ligne is None or ligne[0] is None:
            return f"-- table inconnue : {table!r}"
        return str(ligne[0])

    def run_query(self, sql: str, cap: int = 10_000) -> Result | Échec:
        # Timer qui interrompt la requête si elle dépasse le budget temps.
        # `interrupt()` fait lever OperationalError("interrupted") par sqlite.
        timed_out = threading.Event()

        def _interrompre() -> None:
            timed_out.set()
            self._cx.interrupt()

        minuteur = threading.Timer(self._timeout_s, _interrompre)
        minuteur.start()
        try:
            cur = self._cx.execute(sql)
            # cap+1 : on lit une ligne de trop pour DÉTECTER la troncature
            # sans COUNT(*) séparé (qui réécrirait du SQL — SCOPE §6).
            lues = cur.fetchmany(cap + 1)
        except sqlite3.OperationalError as e:
            genre = "timeout" if timed_out.is_set() else "sql_invalide"
            return Échec(message=str(e), genre=genre)
        except sqlite3.DatabaseError as e:
            # SQL malformé, mauvais type, etc. — événement normal, pas panne.
            return Échec(message=str(e), genre="sql_invalide")
        finally:
            minuteur.cancel()

        tronqué = len(lues) > cap
        lignes = lues[:cap]
        colonnes = [d[0] for d in cur.description] if cur.description else []
        return Result(
            colonnes=colonnes,
            lignes=lignes,
            tronqué=tronqué,
            lignes_lues=len(lignes),
        )


def connect_sqlite(
    chemin: Path | str = CHEMIN_DÉFAUT, timeout_s: float = TIMEOUT_DÉFAUT_S
) -> SQLiteDatabase:
    """Ouvre Chinook (par défaut) en lecture seule. `chemin` en paramètre, jamais
    en dur → couture Postgres (SCOPE §1)."""
    return SQLiteDatabase(Path(chemin), timeout_s=timeout_s)
