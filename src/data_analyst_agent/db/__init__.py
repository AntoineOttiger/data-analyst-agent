"""Module `db` — capacité pure de lecture SQL (DESIGN §1).

Interface étroite : n'expose que le protocole, les types de retour et la fabrique
de connexion. Importer `sqlite` directement depuis l'extérieur est le signal d'une
frontière violée.
"""

from .base import Database
from .result import Result, Échec
from .sqlite import SQLiteDatabase, connect_sqlite

__all__ = ["Database", "Result", "Échec", "SQLiteDatabase", "connect_sqlite"]
