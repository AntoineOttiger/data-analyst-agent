# -*- coding: utf-8 -*-
"""Le graphe ReAct : State, 2 nœuds, routeur, budget, ask() (DESIGN §3, §6).

Forme canonique : nœuds `agent` et `outils`, plus la fonction `route` où vivent
TOUTES les conditions d'arrêt. Le `State` interne ⊃ `Réponse` publique ; il ne
franchit jamais la frontière — `ask()` le projette vers les 5 champs de `Réponse`.
Le vocabulaire LangChain (AIMessage, ToolMessage, add_messages) reste confiné ici.
"""

from __future__ import annotations

import operator
from typing import Annotated, Iterator, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from ..db import Database, connect_sqlite
from ..model import AppelOutil, Message, call_model
from ..response import Réponse
from .events import Événement, Final, Hypothèse, OutilAppelé, RésultatOutil
from .prompt import construire_prompt_système
from .tools import SPECS, SUBMIT_ANSWER, ExécOutil, exécuter, extraire_submit

BUDGET = 10  # nb max d'appels au modèle avant sortie forcée (SCOPE §7)


class State(TypedDict):
    """Circule dans le graphe, JAMAIS exporté. ⊃ Réponse (DESIGN §3)."""

    question: str
    historique: Annotated[list[Message], add_messages]  # LangChain confiné
    tours: int                                           # compteur de budget
    sql_exécuté: Annotated[list[str], operator.add]      # accumulé par le nœud outils
    dernier_résultat: Optional[list[dict]]               # dernier run_query réussi → données
    exéc_outils: list[ExécOutil]                         # transitoire : source des événements de streaming
    # champs de sortie, écrits par submit_answer (via le nœud agent) :
    prose: str
    données: Optional[list[dict]]
    hypothèses: list[str]
    statut: str


# ── nœud agent : produit une décision, n'exécute rien ───────────────────────
def _nœud_agent(state: State) -> dict:
    # Budget épuisé → sortie sèche, on NE rappelle PAS le modèle (SCOPE §7 : pas
    # d'invitation à halluciner une conclusion).
    if state["tours"] >= BUDGET:
        return {"statut": "budget_dépassé"}

    décision = call_model(state["historique"], SPECS)
    # Reconstruire l'AIMessage LangChain à partir de la Décision neutre
    # (LangChain ne franchit pas la frontière de `model`, il est rebâti ici).
    appels_lc = [{"name": a.nom, "args": a.args, "id": a.id} for a in décision.appels]
    ai = AIMessage(content=décision.texte or "", tool_calls=appels_lc)
    updates: dict = {"historique": [ai], "tours": state["tours"] + 1}

    # submit_answer détecté → écrire les champs sémantiques ; `données` vient du
    # code (dernier résultat), pas du LLM (résolution DESIGN §3 vs §7).
    submit = next((a for a in décision.appels if a.nom == SUBMIT_ANSWER), None)
    if submit is not None:
        updates.update(extraire_submit(submit))
        updates["données"] = state.get("dernier_résultat")
    return updates


# ── nœud outils : exécute les appels non terminaux, revient à agent ─────────
def _faire_nœud_outils(db: Database):
    def _nœud_outils(state: State) -> dict:
        dernier = state["historique"][-1]
        appels = getattr(dernier, "tool_calls", None) or []
        messages: list[ToolMessage] = []
        sqls: list[str] = []
        dernier_res: Optional[list[dict]] = None
        exécs: list[ExécOutil] = []
        for tc in appels:
            if tc["name"] == SUBMIT_ANSWER:
                continue  # terminal, traité au routeur
            appel = AppelOutil(nom=tc["name"], args=tc.get("args") or {}, id=tc.get("id") or "")
            ex = exécuter(db, appel)
            exécs.append(ex)
            messages.append(ToolMessage(content=ex.texte, tool_call_id=appel.id))
            if ex.sql:
                sqls.append(ex.sql)
            if ex.résultat is not None:
                dernier_res = ex.résultat
        # exéc_outils est remplacé (pas accumulé) : c'est le delta de CE passage,
        # lu par ask_stream pour émettre les RésultatOutil. Ignoré par ask().
        updates: dict = {"historique": messages, "exéc_outils": exécs}
        if sqls:
            updates["sql_exécuté"] = sqls  # reducer operator.add → accumulation
        if dernier_res is not None:
            updates["dernier_résultat"] = dernier_res
        return updates

    return _nœud_outils


# ── routeur : SEUL lieu des conditions d'arrêt, par priorité (DESIGN §6) ─────
def route(state: State) -> Literal["outils", "agent", "fin"]:
    if state.get("statut"):                    # submit_answer ou budget → fini
        return "fin"
    dernier = state["historique"][-1] if state["historique"] else None
    appels = getattr(dernier, "tool_calls", None) or []
    if appels:                                 # des outils à exécuter
        return "outils"
    return "agent"                             # texte nu sans outil → on relance (budget borne)


def construire_agent(db: Database):
    """Compile le graphe pour une connexion donnée + le prompt (fixe pour la
    connexion, construit une fois — DESIGN §7)."""
    prompt = construire_prompt_système(db.dialecte)
    g = StateGraph(State)
    g.add_node("agent", _nœud_agent)
    g.add_node("outils", _faire_nœud_outils(db))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, {"outils": "outils", "agent": "agent", "fin": END})
    g.add_edge("outils", "agent")
    return g.compile(), prompt


_CACHE: Optional[tuple] = None  # (graphe compilé, prompt) pour la connexion par défaut


def _agent_par_défaut():
    global _CACHE
    if _CACHE is None:
        _CACHE = construire_agent(connect_sqlite())
    return _CACHE


def _projeter(final: State) -> Réponse:
    """Projette le State final vers les 5 champs publics de Réponse."""
    statut = final.get("statut") or "budget_dépassé"
    if statut not in ("ok", "échec", "budget_dépassé"):
        statut = "budget_dépassé"
    return Réponse(
        prose=final.get("prose", ""),
        données=final.get("données"),
        sql=final.get("sql_exécuté", []),
        hypothèses=final.get("hypothèses", []),
        statut=statut,  # type: ignore[arg-type]
    )


def _état_initial(question: str, historique: Optional[list[Message]], prompt: str) -> State:
    messages: list[Message] = [SystemMessage(content=prompt)]
    if historique:
        messages.extend(historique)
    messages.append(HumanMessage(content=question))
    return {
        "question": question,
        "historique": messages,
        "tours": 0,
        "sql_exécuté": [],
        "dernier_résultat": None,
        "exéc_outils": [],
        "prose": "",
        "données": None,
        "hypothèses": [],
        "statut": "",
    }


def _flux_agent(update: dict) -> Iterator[Événement]:
    """Traduit un update du nœud `agent` en événements (outils appelés, hypothèses)."""
    for msg in update.get("historique") or []:
        for tc in getattr(msg, "tool_calls", None) or []:
            if tc["name"] != SUBMIT_ANSWER:
                yield OutilAppelé(nom=tc["name"], args=tc.get("args") or {})
    # submit_answer détecté → l'update porte les hypothèses retenues.
    for h in update.get("hypothèses") or []:
        yield Hypothèse(texte=str(h))


def _flux_outils(update: dict) -> Iterator[Événement]:
    """Traduit un update du nœud `outils` : un RésultatOutil par run_query exécuté."""
    for ex in update.get("exéc_outils") or []:
        if ex.sql is not None:  # seul run_query porte du SQL (DESIGN décision 3)
            yield RésultatOutil(sql=ex.sql, statut=ex.statut,  # type: ignore[arg-type]
                                lignes=ex.lignes, message=ex.message)


def ask_stream(
    question: str, historique: Optional[list[Message]] = None
) -> Iterator[Événement]:
    """Primitive publique du module agent : diffuse la trace ReAct en direct.

    Émet des `Événement` maison (`OutilAppelé`, `RésultatOutil`, `Hypothèse`) au
    fil de la boucle, puis un `Final` portant la `Réponse` projetée. Source de
    vérité unique : `ask()` et l'UI empruntent ce même chemin (DESIGN décision 11).
    Les objets LangChain sont traduits ici et ne franchissent jamais la frontière.
    """
    graphe, prompt = _agent_par_défaut()
    état0 = _état_initial(question, historique, prompt)

    final_state: dict = dict(état0)
    # deux modes : `updates` porte le delta de chaque nœud (→ événements de trace),
    # `values` porte l'état complet accumulé (→ projection finale via _projeter).
    for mode, chunk in graphe.stream(
        état0, config={"recursion_limit": 4 * BUDGET},
        stream_mode=["updates", "values"],
    ):
        if mode == "values":
            final_state = chunk
            continue
        for nœud, update in chunk.items():
            if nœud == "agent":
                yield from _flux_agent(update)
            elif nœud == "outils":
                yield from _flux_outils(update)

    yield Final(réponse=_projeter(final_state))  # type: ignore[arg-type]


def ask(question: str, historique: Optional[list[Message]] = None) -> Réponse:
    """Interface publique du module agent. Fonction (presque) pure : pose une
    question, rend une `Réponse`. `historique` préparé pour le conversationnel
    (sans état pour l'instant — SCOPE §11).

    Réécrite en drain-to-final au-dessus de `ask_stream()` : elle consomme le flux
    et renvoie la `Réponse` du `Final`. Une seule source de vérité (DESIGN décision 11)."""
    réponse = Réponse(prose="", statut="budget_dépassé")
    for évén in ask_stream(question, historique):
        if isinstance(évén, Final):
            réponse = évén.réponse
    return réponse
