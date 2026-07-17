"""Protocole `Database` — l'interface étroite du module db (DESIGN §1).

Une couche d'accès fine : quatre capacités pures (lister, décrire, exécuter,
exposer le dialecte). SQLite en est la première implémentation ; le protocole
prépare la bascule Postgres / autre SGBD (SCOPE §1) sans que l'agent ne change.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .result import Result, Échec


@runtime_checkable
class Database(Protocol):
    """Capacité pure de lecture. Ne parle jamais le langage du LLM (pas de
    troncature-pour-prompt, pas de fiches de dialecte : ça vit dans l'agent)."""

    @property
    def dialecte(self) -> str:
        """Identité du SGBD (ex. ``"sqlite"``). Seule fuite dialecte hors de db :
        la correspondance dialecte→fiche vit dans l'agent (DESIGN §4)."""
        ...

    def list_tables(self) -> list[str]:
        """Noms des tables utilisateur, hors tables système."""
        ...

    def get_schema(self, table: str) -> str:
        """DDL / description d'une table, découverte au runtime (aucun schéma
        codé en dur — SCOPE §8)."""
        ...

    def run_query(self, sql: str, cap: int = 10_000) -> Result | Échec:
        """Exécute un SELECT. Lit au plus `cap` lignes (borne de sécurité, pas
        de réécriture du SQL — SCOPE §6). Rend `Result` (succès) ou `Échec`
        (SQL invalide / timeout) — jamais d'exception pour ces deux cas."""
        ...
