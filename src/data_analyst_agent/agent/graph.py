# -*- coding: utf-8 -*-
"""Le graphe ReAct : State, 2 nœuds, routeur, budget, ask() (DESIGN §3, §6).

Forme canonique : nœuds `agent` et `outils`, plus la fonction `route` où vivent
TOUTES les conditions d'arrêt. Le `State` interne ⊃ `Réponse` publique ; il ne
franchit jamais la frontière — `ask()` le projette vers les 5 champs de `Réponse`.
Le vocabulaire LangChain (AIMessage, ToolMessage, add_messages) reste confiné ici.
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from ..db import Database, connect_sqlite
from ..model import AppelOutil, Message, call_model
from ..response import Réponse
from .prompt import construire_prompt_système
from .tools import SPECS, SUBMIT_ANSWER, exécuter, extraire_submit

BUDGET = 10  # nb max d'appels au modèle avant sortie forcée (SCOPE §7)


class State(TypedDict):
    """Circule dans le graphe, JAMAIS exporté. ⊃ Réponse (DESIGN §3)."""

    question: str
    historique: Annotated[list[Message], add_messages]  # LangChain confiné
    tours: int                                           # compteur de budget
    sql_exécuté: Annotated[list[str], operator.add]      # accumulé par le nœud outils
    dernier_résultat: Optional[list[dict]]               # dernier run_query réussi → données
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
        for tc in appels:
            if tc["name"] == SUBMIT_ANSWER:
                continue  # terminal, traité au routeur
            appel = AppelOutil(nom=tc["name"], args=tc.get("args") or {}, id=tc.get("id") or "")
            ex = exécuter(db, appel)
            messages.append(ToolMessage(content=ex.texte, tool_call_id=appel.id))
            if ex.sql:
                sqls.append(ex.sql)
            if ex.résultat is not None:
                dernier_res = ex.résultat
        updates: dict = {"historique": messages}
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


def ask(question: str, historique: Optional[list[Message]] = None) -> Réponse:
    """Interface publique du module agent. Fonction (presque) pure : pose une
    question, rend une `Réponse`. `historique` préparé pour le conversationnel
    (sans état pour l'instant — SCOPE §11)."""
    graphe, prompt = _agent_par_défaut()
    messages: list[Message] = [SystemMessage(content=prompt)]
    if historique:
        messages.extend(historique)
    messages.append(HumanMessage(content=question))

    état0: State = {
        "question": question,
        "historique": messages,
        "tours": 0,
        "sql_exécuté": [],
        "dernier_résultat": None,
        "prose": "",
        "données": None,
        "hypothèses": [],
        "statut": "",
    }
    final = graphe.invoke(état0, config={"recursion_limit": 4 * BUDGET})
    return _projeter(final)  # type: ignore[arg-type]
