# -*- coding: utf-8 -*-
"""Les 4 outils = adaptateurs fins LLM → db (DESIGN §4).

Ce ne sont PAS un module : ils parlent le vocabulaire de l'agent (schéma JSON,
dispatch, sérialisation texte pour le prompt, troncature à ~50 lignes pour le
LLM), pas celui de la base. Le jour de la GUI, on les ignore et la GUI appelle
`db.run_query` en direct.

Frontière d'erreurs (DESIGN §5) : `run_query` rend `Result | Échec` ; on
sérialise via un `match`, SANS try/except de contrôle de flux. Le message brut
du moteur passe tel quel au LLM (signal d'auto-correction).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..db import Database, Result, Échec
from ..model import AppelOutil, ToolSpec

LIGNES_POUR_LLM = 50   # ce que le LLM VOIT (raisonnement) ; la GUI aura jusqu'au cap db

# ── noms canoniques des outils ──────────────────────────────────────────────
LIST_TABLES = "list_tables"
GET_SCHEMA = "get_schema"
RUN_QUERY = "run_query"
SUBMIT_ANSWER = "submit_answer"

# ── spécifications (function-calling), indépendantes du provider ────────────
SPECS: list[ToolSpec] = [
    ToolSpec(LIST_TABLES, "Liste les tables de la base. Aucun argument.",
             {"type": "object", "properties": {}, "required": []}),
    ToolSpec(GET_SCHEMA, "Donne le schéma (DDL) d'une table nommée.",
             {"type": "object",
              "properties": {"table": {"type": "string", "description": "nom exact de la table"}},
              "required": ["table"]}),
    ToolSpec(RUN_QUERY, "Exécute une requête SQL SELECT en lecture seule et renvoie les lignes.",
             {"type": "object",
              "properties": {"sql": {"type": "string", "description": "une requête SELECT"}},
              "required": ["sql"]}),
    ToolSpec(SUBMIT_ANSWER,
             "Termine et rends la réponse finale. À appeler une seule fois, quand tu as "
             "assez d'informations. `données` n'est PAS à fournir : le code la remplit "
             "depuis ta dernière requête.",
             {"type": "object",
              "properties": {
                  "prose": {"type": "string", "description": "réponse en langage naturel, dans la langue de la question"},
                  "statut": {"type": "string", "enum": ["ok", "échec"],
                             "description": "'ok' si tu réponds ; 'échec' si la question est impossible avec ce schéma"},
                  "hypothèses": {"type": "array", "items": {"type": "string"},
                                 "description": "interprétations retenues en cas d'ambiguïté (sinon liste vide)"},
              },
              "required": ["prose", "statut"]}),
]


@dataclass
class ExécOutil:
    """Résultat d'exécution d'un outil non terminal, pour le nœud `outils`.

    Porte aussi de quoi produire un événement de streaming (`RésultatOutil`) :
    `nom` de l'outil, `statut` humain, `lignes` lues, `message` d'erreur brut.
    """

    texte: str                     # sérialisation pour le ToolMessage (ce que voit le LLM)
    nom: str = ""                  # nom de l'outil appelé (pour le streaming)
    sql: str | None = None         # rempli si run_query → accumulé dans State.sql_exécuté
    résultat: list[dict] | None = None  # rempli si run_query réussit → dernier_résultat (GUI)
    statut: str = "succès"         # "succès" | "échec" | "timeout" (pour le streaming)
    lignes: int | None = None      # nb de lignes lues si succès (pour le streaming)
    message: str | None = None     # message brut du moteur si échec/timeout (pour le streaming)


# ── sérialisation d'un Result pour le LLM (tronquée) ────────────────────────
def _lignes_dicts(res: Result) -> list[dict]:
    """Result.lignes (list[tuple]) → list[dict], forme attendue par la GUI."""
    return [dict(zip(res.colonnes, ligne)) for ligne in res.lignes]


def _sérialiser_result(res: Result) -> str:
    entête = " | ".join(res.colonnes)
    vues = res.lignes[:LIGNES_POUR_LLM]
    corps = "\n".join(" | ".join("" if v is None else str(v) for v in ligne) for ligne in vues)
    notes = []
    if len(res.lignes) > LIGNES_POUR_LLM:
        notes.append(f"(affichage limité à {LIGNES_POUR_LLM} lignes)")
    if res.tronqué:
        notes.append(f"(calcul complet ; lecture bornée à {res.lignes_lues} lignes, il en reste)")
    pied = ("\n" + " ".join(notes)) if notes else ""
    return f"{res.lignes_lues} ligne(s).\n{entête}\n{corps}{pied}"


def _sérialiser_échec(éch: Échec) -> str:
    return f"ERREUR ({éch.genre}) : {éch.message}"


# ── dispatch d'un outil non terminal ────────────────────────────────────────
def exécuter(db: Database, appel: AppelOutil) -> ExécOutil:
    """Exécute list_tables / get_schema / run_query. submit_answer n'arrive
    jamais ici (intercepté au routeur)."""
    if appel.nom == LIST_TABLES:
        tables = db.list_tables()
        return ExécOutil(texte="Tables : " + ", ".join(tables), nom=LIST_TABLES)

    if appel.nom == GET_SCHEMA:
        table = str(appel.args.get("table", ""))
        return ExécOutil(texte=db.get_schema(table), nom=GET_SCHEMA)

    if appel.nom == RUN_QUERY:
        sql = str(appel.args.get("sql", ""))
        issue = db.run_query(sql)
        match issue:                       # frontière d'erreurs : valeur, pas exception
            case Result() as res:
                return ExécOutil(texte=_sérialiser_result(res), nom=RUN_QUERY, sql=sql,
                                 résultat=_lignes_dicts(res), statut="succès",
                                 lignes=res.lignes_lues)
            case Échec() as éch:
                statut = "timeout" if éch.genre == "timeout" else "échec"
                return ExécOutil(texte=_sérialiser_échec(éch), nom=RUN_QUERY, sql=sql,
                                 statut=statut, message=éch.message)

    return ExécOutil(texte=f"ERREUR : outil inconnu {appel.nom!r}",
                     nom=appel.nom, statut="échec")


def extraire_submit(appel: AppelOutil) -> dict:
    """Extrait les champs sémantiques d'un appel submit_answer (données exclue :
    remplie par le code depuis le dernier résultat)."""
    args = appel.args or {}
    statut = args.get("statut", "ok")
    if statut not in ("ok", "échec"):
        statut = "ok"
    hyp = args.get("hypothèses") or []
    if not isinstance(hyp, list):
        hyp = [str(hyp)]
    return {
        "prose": str(args.get("prose", "")),
        "statut": statut,
        "hypothèses": [str(h) for h in hyp],
    }
