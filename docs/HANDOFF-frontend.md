# Handoff — Implémentation frontend (data-analyst-agent)

**Date :** 2026-07-18
**Repo :** `c:\Users\Antoine\Documents\prog\python\data-analyst-agent` (branche `main`)
**Statut :** Grilling terminé, compréhension partagée atteinte. **Aucun code écrit.** En attente : le prochain agent implémente dans l'ordre ci-dessous.

---

## Contexte

Le **backend est complet et fonctionnel** (`db`, `model`, `agent`, `eval`). Interface publique : `ask(question, historique=None) -> Réponse` dans [src/data_analyst_agent/agent/graph.py](src/data_analyst_agent/agent/graph.py). Ni `frontend/` ni `src/data_analyst_agent/api/` n'existent — DESIGN §9 les réserve.

L'utilisateur veut maintenant construire le frontend. Une session `/grilling` a parcouru tout l'arbre de décision. Toutes les décisions sont prises.

**Lire d'abord :** [docs/SCOPE.md](docs/SCOPE.md) et [docs/DESIGN.md](docs/DESIGN.md) (notamment §1 règle de dépendance, §3 types, §9 couture GUI). Ne PAS dupliquer ici — ces docs font autorité.

---

## Décisions verrouillées (ne pas re-litiger)

| # | Décision | Choix |
|---|---|---|
| 1 | Ambition | Démo portfolio soignée (**B**), « qui donne complexe ». DB **figée sur `chinook.db`** (pas de risque multi-SGBD maintenant) |
| 2 | Interaction | **Streaming** des étapes ReAct via nouvelle interface **`ask_stream()` dans le module `agent/`** (PAS dans `api/` — la règle de dépendance DESIGN §1/§9 interdit à `api`/GUI de toucher `agent/graph`) |
| 3 | Événements | Granularité **moyenne**. `@dataclass Événement` typé **maison** (vocabulaire à nous, pas d'objets LangChain sur la frontière). Genres : `outil_appelé` (nom+args), `résultat_outil` (SQL + succès/échec/timeout), `hypothèse`, `final` (porte la `Réponse` projetée) |
| 4 | API | **FastAPI**. `POST /ask` en **SSE** (`text/event-stream`) + `GET /health`. `StreamingResponse` sur un générateur qui itère `ask_stream()`. Pydantic en entrée seulement (`{question: str}`) ; sérialisation manuelle en sortie (nos dataclasses = notre vocabulaire, pas de modèles Pydantic dupliqués) |
| 5 | Contrat JSON | **Traduit en ascii/anglais DANS `api/`** (rôle de traduction de protocole, pendant HTTP de `agent/tools.py`). Mapping : `données`→`rows`, `prose`→`answer`, `hypothèses`→`assumptions`, `statut`→`status`, `sql`→`sql`. Le Python reste français |
| 6 | Stack front | **React + Vite** |
| 7 | Service | **Dev** : serveur Vite (5173) proxifie `/api/*` → FastAPI (8000). **Prod/démo** : `vite build` → `frontend/dist/` servi par FastAPI en `StaticFiles` = **un seul process, une commande**. README documente les deux modes |
| 8 | Rendu final | Markdown (prose, via `react-markdown`) + **tableau plafonné à 200 lignes affichées** (bandeau « affichage limité à 200 sur N » si `données` dépasse — cohérent SCOPE §3) + SQL colorisé en **accordéon** (toutes les requêtes) + hypothèses en **callout** + **badge de statut** (`ok`/`échec`/`budget_dépassé` ; un `échec` sur cas « impossible » est un succès, le montrer dignement). **PAS de graphiques** (B, pas C ; auto-charting = échec silencieux) |
| 9 | Langage front | **TypeScript**. Modéliser le contrat SSE en **union discriminée** (`type Événement = OutilAppelé \| RésultatOutil \| Hypothèse \| Final`) → `switch` exhaustif sur `event.type` |
| 10 | Visuel | **« Agent console » sombre**, layout **deux zones** : panneau raisonnement en direct (le flux ReAct qui défile) ↔ panneau résultat. Accents monospace sur le technique, coloration SQL sur fond sombre |
| 11 | Architecture | **`ask_stream()` = primitive**, `ask()` réécrit comme **drain-to-final** (consomme le flux, renvoie la `Réponse` du `final`). Source de vérité unique : l'UI et l'éval empruntent le même chemin. Cohérent avec la philosophie repo (`State ⊃ Réponse`, « A = cas particulier de B ») |

**Défauts assumés (l'utilisateur n'a pas objecté) :** `npm`, `react-markdown`, petite lib de coloration SQL (Shiki ou highlight.js), `frontend/` à la racine (hors `src/`, par DESIGN §9).

---

## Ordre de construction

1. **`agent/`** : extraire `ask_stream()` (primitive) + définir `Événement`. Réécrire `ask()` en drain-to-final. **Vérifier que l'éval (25 cas) passe toujours vert** (`python -m eval.run` ou équivalent — vérifier l'entrée dans [src/eval/run.py](src/eval/run.py)). Exposer `ask_stream` + `Événement` dans `agent/__init__.py` (aujourd'hui n'expose que `ask`).
2. **`src/data_analyst_agent/api/`** : FastAPI, fonctions de traduction ascii, endpoint SSE, `StaticFiles`. Ajouter `fastapi`, `uvicorn`, `sse-starlette` (ou SSE manuel) aux deps de [pyproject.toml](pyproject.toml).
3. **`frontend/`** : scaffold Vite React-TS, câblage `EventSource`/fetch-stream vers `/api/ask`, dispatch typé des événements.
4. **Composants** : flux de raisonnement + panneau résultat, habillage « agent console » sombre.
5. **Build prod** servi par FastAPI + README (deux modes de lancement).

---

## Pièges connus / points de vigilance

- **Frontière de dépendance** (DESIGN §1) : `api/` et `frontend/` ne parlent QU'À `agent` (`ask`/`ask_stream`/`Réponse`/`Événement`) — jamais à `agent/graph`, `agent/tools`. `ask_stream()` doit vivre dans `agent/`, pas dans `api/`.
- **LangChain confiné** : les objets LangChain (`AIMessage`, `ToolMessage`) ne doivent PAS fuir dans les `Événement`. Traduire vers le vocabulaire maison au moment du `.stream()`, comme `graph.py` le fait déjà pour `Décision`.
- **Streaming LangGraph** : `graph.compile().stream(...)` existe ; mapper ses updates de nœud vers nos `Événement`. Le nœud `outils` accumule `sql_exécuté` et `dernier_résultat` — c'est la source des événements `résultat_outil`.
- **Accents dans les clés JSON** : NE PAS laisser fuir sur le fil ; la traduction ascii se fait dans `api/` (décision 5).
- **Latence** : `ask()` peut prendre 10–30 s (jusqu'à `BUDGET=10` appels modèle à ~1 req/s). Le streaming transforme l'attente en spectacle — c'est le point.
- **Throttle** : le repo a déjà un throttle anti-429 (~0.5 rps, cf. commit `1aaa04e`). Le streaming ne doit pas le contourner.

---

## Suggested skills

- **`graphify`** — pour toute question sur le codebase existant. Le repo a `graphify-out/graph.json` ; lancer `graphify query "<question>"` avant de grep. (Voir [CLAUDE.md](CLAUDE.md) règles graphify. Après modif de code : `graphify update .`.)
- **`claude-api`** — NON pertinent ici : le provider LLM est **Mistral** (`langchain-mistralai`), pas Anthropic. La règle de skip s'applique (provider tiers nommé).
- **`verify`** — après avoir câblé la couture end-to-end, exécuter le flux réel (question → SSE → rendu) et l'observer, pas seulement les tests.
- **`code-review`** ou **`simplify`** — avant commit des changements non triviaux.

**IMPORTANT (workflow utilisateur) :** l'utilisateur a demandé le grilling AVANT d'implémenter. Il valide les décisions puis fait implémenter. La compréhension partagée est **déjà confirmée** — le prochain agent peut implémenter directement dans l'ordre ci-dessus, mais devrait re-confirmer brièvement s'il dévie d'une décision.
