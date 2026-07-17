# Graph Report - data-analyst-agent  (2026-07-17)

## Corpus Check
- 26 files · ~10,760 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 171 nodes · 271 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1aaa04ee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]

## God Nodes (most connected - your core abstractions)
1. `Database` - 15 edges
2. `Les 11 décisions` - 12 edges
3. `Result` - 11 edges
4. `Échec` - 11 edges
5. `SQLiteDatabase` - 11 edges
6. `call_model()` - 11 edges
7. `System Design — data-analyst-agent` - 11 edges
8. `exécuter()` - 10 edges
9. `Résultat` - 10 edges
10. `ask()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `lancer()` --calls--> `ask()`  [INFERRED]
  src/eval/run.py → src/data_analyst_agent/agent/graph.py
- `Résultat` --uses--> `Réponse`  [INFERRED]
  src/eval/scorer.py → src/data_analyst_agent/response.py
- `_nœud_agent()` --calls--> `call_model()`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → src/data_analyst_agent/model/mistral.py
- `_faire_nœud_outils()` --calls--> `exécuter()`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → src/data_analyst_agent/agent/tools.py
- `_faire_nœud_outils()` --references--> `Database`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → src/data_analyst_agent/db/base.py

## Import Cycles
- None detected.

## Communities (14 total, 6 thin omitted)

### Community 3 - "Community 3"
Cohesion: 0.28
Nodes (11): Message, AppelOutil, call_model(), Décision, _llm(), _outil_openai(), Description d'un outil, indépendante du provider (JSON Schema des args)., Ce que rend `call_model` — vocabulaire à nous, pas LangChain. (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (26): ExécOutil, exécuter(), _lignes_dicts(), Résultat d'exécution d'un outil non terminal, pour le nœud `outils`., Result.lignes (list[tuple]) → list[dict], forme attendue par la GUI., Exécute list_tables / get_schema / run_query. submit_answer n'arrive     jamais, _sérialiser_result(), _sérialiser_échec() (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (17): 10. Dialecte inconnu, 11. Langue & état, 1. Source de données, 2. Nature de l'agent, 3. Type de retour, 4. Évaluation — golden set D'ABORD, 5. Framework, 6. Sécurité (défense mécanique, ne dépend jamais du LLM) (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (18): 10. Ordre de construction (raffine SCOPE §« Ordre de construction »), 1. Les 4 modules et la règle de dépendance, 2. Arborescence, 3. Types partagés et internes, 4. Frontières délicates (les décisions qui empêchent le spaghetti), 5. Stratégie d'erreurs (« define errors out of existence »), 6. Topologie du graphe (`agent/graph.py`), 7. Assemblage du prompt (`agent/prompt.py`, `agent/dialects/`) (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (20): CasÉval, lancer(), main(), rapport(), True si tous les paliers atteignent leur seuil., _verdict(), agréger(), _cellules() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (23): _agent_par_défaut(), ask(), construire_agent(), _faire_nœud_outils(), _nœud_agent(), _projeter(), Compile le graphe pour une connexion donnée + le prompt (fixe pour la     connex, Projette le State final vers les 5 champs publics de Réponse. (+15 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (17): 1. Le type de retour est le tien, 1. Plus de code au démarrage, 2. Courbe d'apprentissage LangGraph, 2. Le refus de répondre (palier 5) devient possible, 3. La double troncature (50 lignes → LLM, 10 000 → `données`), 3. On réécrit des choses déjà résolues, 4. Debugging transparent, 4. Surface de bug plus grande (+9 more)

## Knowledge Gaps
- **50 isolated node(s):** `block-dangerous-git.sh script`, `data-analyst-agent`, `graphify`, `1. Les 4 modules et la règle de dépendance`, `2. Arborescence` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Database` connect `Community 5` to `Community 9`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `Réponse` connect `Community 9` to `Community 8`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `connect_sqlite()` connect `Community 9` to `Community 5`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Database` (e.g. with `Result` and `Échec`) actually correct?**
  _`Database` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Result` (e.g. with `Database` and `SQLiteDatabase`) actually correct?**
  _`Result` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Échec` (e.g. with `Database` and `SQLiteDatabase`) actually correct?**
  _`Échec` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SQLiteDatabase` (e.g. with `Result` and `Échec`) actually correct?**
  _`SQLiteDatabase` has 2 INFERRED edges - model-reasoned connections that need verification._