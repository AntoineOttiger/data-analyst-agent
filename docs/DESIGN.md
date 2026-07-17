# System Design — data-analyst-agent

> Pendant système de [SCOPE.md](./SCOPE.md). Le scope fixe **quoi** (le fonctionnel, 11
> décisions) ; ce document fixe **comment c'est découpé** : les gros blocs modulaires,
> leurs interfaces étroites, et les règles de dépendance entre eux.
>
> Préceptes directeurs (Ousterhout) tenus tout du long :
> - **Modules profonds, interfaces simples** : grosse machinerie dedans, peu de surface
>   dehors.
> - **Interactions simples entre gros blocs** : dépendances unidirectionnelles, pas de
>   spaghetti, pas de cycle.
> - **Stratégique, pas tactique** : on prend tôt les décisions coûteuses à inverser, on
>   repousse celles qui dépendent d'infos qu'on n'a pas encore.

---

## 1. Les 4 modules et la règle de dépendance

Quatre blocs, dépendances **unidirectionnelles**, aucun cycle :

```
                eval ─────► agent ─────► db
                              └────────► model

        tout le monde peut importer  ►  response  (vocabulaire partagé, neutre)
```

| Module | Interface (étroite) | Ce qu'il cache (profondeur) |
|---|---|---|
| **`db`** | `list_tables()`, `get_schema(table)`, `run_query(sql, cap) -> Result \| Échec`, `dialecte` | connexion read-only, `fetchmany`/cap, timeout, identité du dialecte, SQLite→Postgres |
| **`agent`** | `ask(question, historique=None) -> Réponse` | le graphe entier : nœuds, arêtes, boucle ReAct, budget, dispatch d'outils, construction du prompt, injection de la fiche dialecte, troncature-pour-LLM |
| **`model`** | `call_model(messages, tools) -> Décision` | provider (Mistral), format function-calling, retries |
| **`eval`** | lance le golden set contre `ask`, produit un rapport ventilé par palier | chargement des cas, comparaison sur résultat, scoring par palier |

**Interdits (à vérifier en revue par les imports) :**
- `db` ou `model` qui importe `agent` → **cycle**.
- La future GUI qui importe `agent/graph` ou `agent/tools` → elle ne parle qu'à `ask()` /
  `Réponse` (ou à l'`api/`).
- Chaque `__init__.py` n'expose que l'interface étroite ; importer *dans* un sous-module
  au lieu du package est le signal visible d'une frontière violée.

---

## 2. Arborescence

```
data-analyst-agent/               # racine du repo
    database/                     # ASSETS (données), hors du package Python
        chinook.db                # SQLite, premier banc d'essai (SCOPE §1) — COMMITÉ
    src/
        data_analyst_agent/       # le cœur livrable
            __init__.py
            response.py           # la Réponse publique (5 champs) — vocabulaire partagé
            db/
                __init__.py       # expose : Database, Result, Échec, connect_sqlite()
                base.py           # protocole Database (list_tables, get_schema, run_query, dialecte)
                sqlite.py         # implémentation SQLite (read-only, fetchmany, timeout)
                result.py         # Result, Échec
            model/
                __init__.py       # expose : call_model, Décision, AppelOutil, Message, ToolSpec
                mistral.py        # digère le format provider (B-pragmatique)
            agent/
                __init__.py       # expose : ask(question, historique=None) -> Réponse
                graph.py          # State, nœuds, route(), construction du StateGraph
                tools.py          # les 4 adaptateurs LLM → db
                prompt.py         # construire_prompt_système()
                dialects/
                    sqlite.md
                    postgres.md
                    ansi.md       # repli générique (SCOPE §10)
            api/                  # RÉSERVÉ — enrobage HTTP de ask() (voir §9). Pas construit maintenant.
        eval/
            __init__.py
            golden_set.py         # les ~25 CasÉval (données figées)
            scorer.py             # comparaison ensembliste + tolérance float, rapport par palier
            run.py                # point d'entrée : lance l'éval, rapport par palier
    frontend/                     # RÉSERVÉ — GUI web (voir §9). Pas construit maintenant.
    docs/
        SCOPE.md
        DESIGN.md
        langgraph-graph-explicite-vs-helpers.md
    pyproject.toml
```

**Choix de layout — pourquoi :**
- **`src/`** : standard Python moderne, **coûteux à inverser** donc pris tôt. Empêche
  l'import accidentel depuis le cwd (force `pip install -e .` → on teste ce qu'on livre),
  sépare le livrable des assets/docs, lisible pour un relecteur.
- **`database/` hors du package** : c'est de la donnée, pas du code importable.
  `connect_sqlite(path)` reçoit `database/chinook.db` en paramètre (défaut), jamais en dur
  → couture Postgres (SCOPE §1). **`chinook.db` est commité** : le golden set figé (§8) n'a
  de sens que contre cette base précise ; un `clone` doit pouvoir lancer l'éval sans étape
  de téléchargement. Petit (~1 Mo), fixe, socle de la reproductibilité.
- **`response.py` à la racine du package**, pas dans `agent/` : `Réponse` est le
  vocabulaire partagé entre `agent` (producteur) et l'appelant/GUI (consommateur). La
  laisser neutre évite de coupler la GUI aux entrailles de l'agent.
- Noms de **fichiers en anglais**, **types du domaine en français** (`Réponse`,
  `données`, `hypothèses`) : le domaine reste en français là où on lit le code, sans
  friction d'outillage sur les chemins.

---

## 3. Types partagés et internes

### Public (franchit la frontière du module) — `response.py`
```python
@dataclass
class Réponse:
    prose: str
    données: list[dict] | None
    sql: list[str]                 # rempli par le code, jamais par le LLM
    hypothèses: list[str]
    statut: Literal["ok", "échec", "budget_dépassé"]
```

### Interne à `db` — `db/result.py`
```python
@dataclass
class Result:                      # un SUCCÈS de requête
    colonnes: list[str]            # noms, dans l'ordre
    lignes: list[tuple]            # jusqu'à cap lues (défaut 10 000), brutes
    tronqué: bool                  # a-t-on arrêté de lire avant la fin ?
    lignes_lues: int               # commodité (len(lignes))

@dataclass
class Échec:                       # SQL invalide OU timeout dépassé — une VALEUR, pas une exception
    message: str                   # message brut du moteur, tel quel (signal d'auto-correction)
    genre: Literal["sql_invalide", "timeout"]
```
- **Pas de « total vrai »** : `fetchmany` s'arrête sans savoir combien il reste. On lit une
  ligne de plus (cap+1) et on la jette pour détecter `tronqué`. Un `COUNT(*)` séparé
  réécrirait du SQL → interdit (SCOPE §6). Message honnête : « au moins N, tronqué ».
  Les agrégats de l'agent (`GROUP BY`/`COUNT`) rendent peu de lignes → `tronqué=False`,
  total exact car issu du SQL de l'agent.
- **`lignes: list[tuple]` brut** (pas `list[dict]`) : forme naturelle du curseur, gère les
  colonnes homonymes. La conversion en `list[dict]` pour `Réponse.données` est une
  projection *de l'agent*, pas une responsabilité de `db`.

### Interne à `model` — `model/`
```python
@dataclass
class AppelOutil:
    nom: str
    args: dict
    id: str

@dataclass
class Décision:                    # ce que rend call_model — vocabulaire à NOUS, pas LangChain
    appels: list[AppelOutil]       # vide si le modèle a fini
    texte: str | None              # présent si réponse directe sans outil
```

### Interne à `agent` — `agent/graph.py`
```python
class State(TypedDict):            # circule dans le graphe, JAMAIS exporté
    question: str
    historique: list[Message]      # messages (LangChain confiné ici, réduit par add_messages)
    tours: int                     # compteur de budget
    sql_exécuté: list[str]         # accumulé par l'adaptateur run_query → Réponse.sql
    # champs de sortie, écrits par submit_answer :
    prose: str
    données: list[dict] | None
    hypothèses: list[str]
    statut: Literal["ok", "échec", "budget_dépassé"]
```

**`State` ⊃ `Réponse`.** La mémoire de travail (historique, `tours`) ne franchit jamais la
frontière : `ask()` **projette** le `State` final vers les 5 champs de `Réponse`. La couture
GUI/audit reste propre.

---

## 4. Frontières délicates (les décisions qui empêchent le spaghetti)

### Les 4 outils ne sont pas un module — ce sont des adaptateurs fins (`agent/tools.py`)
Un **outil LLM** (schéma JSON + dispatch + sérialisation texte pour le prompt) parle le
vocabulaire de l'agent, pas de la base. Le mettre dans `db` y injecterait une politique
d'agent (troncature à ~50 lignes pour le LLM) et casserait la réutilisabilité par la GUI
(qui veut jusqu'à 10 000 lignes structurées, pas « showing 50 »).

- **Capacité pure** → module profond `db` (`run_query`, cap 10 000, read-only, timeout).
- **Traduction de protocole** → fichier fin `agent/tools.py` : parse les args du LLM,
  appelle `db.run_query`, tronque à ~50 lignes + sérialise pour le prompt, **accumule le
  SQL exécuté dans `State.sql_exécuté`**.

*Test de la frontière* : le jour de la GUI, on ignore `agent/tools.py` et la GUI appelle
`db.run_query` en direct. `db` est intact.

### `db` expose son dialecte, il ne connaît pas les fiches
`db.dialecte -> str` (ex. `"sqlite"`) est **la seule fuite dialecte** hors de `db`. La
correspondance dialecte→fiche et le repli ANSI vivent dans `agent` (vocabulaire prompt).
`db` ne parle jamais le langage du LLM.

### `call_model` niveau B-pragmatique
`call_model(messages, tools) -> Décision` digère le format Mistral/LangChain → assure
l'**indépendance vis-à-vis du provider** (SCOPE §5). Le vocabulaire LangChain (`AIMessage`,
`ToolNode`, `add_messages`) reste **confiné au `State` interne** — on garde les helpers
LangGraph — mais ne franchit jamais la frontière : `Réponse` n'en porte aucune trace.
On ne cherche PAS l'indépendance vis-à-vis de LangGraph lui-même (socle assumé, SCOPE §5).

---

## 5. Stratégie d'erreurs (« define errors out of existence »)

Deux familles, traitées à l'opposé :

| Famille | Exemples | Traitement | Pourquoi |
|---|---|---|---|
| **1. Événement normal** | SQL invalide (`no such table`), **timeout** | **valeur `Échec`** rendue par `run_query` | c'est le signal d'auto-correction de la boucle ReAct (SCOPE §9). L'adaptateur sérialise `Échec.message` en texte pour le LLM via un `match`, **sans `try/except`** de contrôle de flux. |
| **2. Panne réelle** | fichier DB absent, connexion morte, disque plein | **exception qui remonte** et crashe franchement | aucune auto-correction n'aide ; l'enterrer ferait tourner l'agent 10 tours contre une base morte. Une panne doit être bruyante. |

Le chemin nominal et le chemin d'échec-SQL ont la **même forme** (un retour à `match`),
pas un branchement exceptionnel. Le message brut du moteur passe **tel quel** au LLM (ne
pas traduire = ne pas perdre de signal). Le timeout est un `Échec` (« reformule »), pas un
fatal.

---

## 6. Topologie du graphe (`agent/graph.py`)

Forme canonique ReAct : **2 nœuds + 1 routeur**, toute la logique d'arrêt dans une seule
fonction.

```
  START ─► [agent] ─► route(state) ─┬─ "outils" ─► [outils] ─┐
                                    │                         │
                                    ├─ "fin" ──► END          │
                                    │                         │
                                    └─────────────────────────┘  (outils revient à agent)
```

- **Nœud `agent`** : `call_model(historique, tools)`, `tours += 1`, append la `Décision` à
  l'historique. Ne route rien — produit une décision.
- **Nœud `outils`** : exécute les `AppelOutil` (dispatch `tools.py`), append les retours,
  accumule `sql_exécuté`. Revient toujours à `agent`.
- **Routeur `route(state)`** (fonction, pas un nœud) — **seul lieu des conditions
  d'arrêt**, par priorité :
  1. le modèle a appelé `submit_answer` → écrit les 4 champs de sortie, **END** (porte de
     sortie unique, SCOPE §7) ;
  2. `tours >= budget` (~10) → force `statut="budget_dépassé"` + SQL déjà tenté, **END** ;
  3. sinon des `AppelOutil` restent → nœud **`outils`**.

- `submit_answer` est un outil au niveau LLM, mais **détecté au routeur** (pas de nœud
  `finalize` : une boîte qui n'écrit que 4 champs n'ajoute pas de profondeur).
- Budget dépassé = **sortie sèche**, on n'appelle jamais le modèle « une dernière fois pour
  conclure » (SCOPE §7 : pas d'invitation à halluciner).

---

## 7. Assemblage du prompt (`agent/prompt.py`, `agent/dialects/`)

- **Fiches de dialecte = données** (`.md`, une par SGBD), pas de `if dialecte == …` dans le
  code. Édition/diff/itération sans recompiler (SCOPE §9).
- **Un constructeur unique** — aucune f-string de prompt éparpillée dans les nœuds :
  ```python
  def construire_prompt_système(dialecte: str, langue_indice: str | None) -> str:
      #   1. rôle + protocole ReAct (explore via outils, puis submit_answer)
      #   2. fiche de dialecte (sélectionnée via db.dialecte, repli ansi.md si absente)
      #   3. règle "SELECT only" (présente mais JAMAIS comptée comme défense, SCOPE §6)
      #   4. consigne de langue (réponds dans la langue de la question, SCOPE §11)
  ```
- **Construit une fois** à la création de l'agent (le dialecte est fixe pour une
  connexion), pas à chaque `ask()`.
- **Consigne de langue explicite** (ligne dédiée) : gratuit, et verrouille un comportement
  que le golden set FR/Chinook-EN teste (SCOPE §11) — ne pas dépendre de l'émergence.

---

## 8. Harnais d'éval (`eval/`)

- **Golden set = données déclaratives figées** (`golden_set.py`), séparées du scoring :
  ```python
  @dataclass
  class CasÉval:
      id: str
      palier: int                       # 1..5
      question: str                     # en FR
      statut_attendu: Literal["ok", "échec"]
      résultat_attendu: object | None   # vérité terrain FIGÉE (autorité = vérif humaine)
      sql_référence: str | None         # PROVENANCE : comment la valeur figée fut obtenue — non exécuté par le scorer
      note: str                         # pourquoi ce cas existe (le piège, l'ambiguïté)
  ```
- **Comparaison sur le RÉSULTAT, jamais sur le SQL** (SCOPE §4) :
  - **paliers 1–4** : `Réponse.données` (ou scalaire) vs `résultat_attendu`, **ensembliste
    et ordre-insensible** par défaut (ordre exigé seulement si la question trie, « top 5 ») ;
    **`math.isclose`** sur les floats (agrégats, montants), exact sinon.
  - **palier 5** (impossible) : succès ⟺ `statut == "échec"`. Aucune donnée comparée —
    refuser *est* la bonne réponse.
- **Vérité terrain figée** (choix assumé) : le scorer ne touche la base **que via l'agent**,
  jamais via un SQL de référence parallèle → déterminisme total. `sql_référence` reste une
  trace vérifiable à la main. Contrepartie acceptée : si Chinook changeait, les valeurs
  dériveraient en silence — nul en pratique (Chinook est fixe et commité).
- **Rapport ventilé par palier** (`run.py`) : « palier 4 : 2/5 » dit tout, « 20/25 » ne dit
  rien. Le palier 4 (piège sémantique) est *le* différenciateur (SCOPE §4).

---

## 9. Anticipation de la GUI (couture, pas béton)

La couture qui rend la GUI possible **est déjà faite** — ce sont les *interfaces*, pas des
dossiers vides :
- `ask(question, historique=None) -> Réponse` : fonction (presque) pure, posable derrière
  n'importe quelle interface ;
- `Réponse.données` séparé de `Réponse.prose` : la GUI fait tableaux/graphiques ;
- `Réponse.sql` : trace d'audit affichable ;
- `db` réutilisable en direct (adaptateurs LLM isolés dans `agent/tools.py`).

**Décision GUI web (anticipée, construite plus tard) :**
- **`frontend/`** à la racine (JS/web, hors `src/` car pas du Python) — dossier **réservé,
  pas créé maintenant**.
- **`src/data_analyst_agent/api/`** : couche qui enrobe `ask()` en HTTP pour le front —
  **réservée, pas construite maintenant**. C'est le point de contact `frontend/` ↔ cœur.

Principe : on **réserve la place** (documentée ici) sans **couler le béton** (dossiers
vides). L'anticipation vit dans les interfaces déjà verrouillées.

---

## 10. Ordre de construction (raffine SCOPE §« Ordre de construction »)

1. **`src/` + `pyproject.toml`** (`pip install -e .`), `database/chinook.db` commité.
2. **Module `db`** : `base.py` (protocole), `sqlite.py` (read-only, `fetchmany`, timeout),
   `result.py` (`Result`/`Échec`), `dialecte`.
3. **Module `eval`** : golden set (~25 `CasÉval` FR gradués, valeurs figées + vérif
   humaine) + `scorer.py` + `run.py`. **Avant** la boucle agentique (SCOPE §4).
4. **Module `model`** : `call_model` → `Décision` (B-pragmatique).
5. **Module `agent`** : `graph.py` (State, 2 nœuds, `route`, budget, `submit_answer`),
   `tools.py`, `prompt.py`, `dialects/` (+ repli `ansi.md`).
6. **Itération mesurée** contre le golden set (rapport par palier).

**Hors scope de cette phase** (rappel SCOPE) : `frontend/`, `api/`, conversationnel
multi-tours, transpilation SQL, validation par allowlist, RAG, écriture en base.
