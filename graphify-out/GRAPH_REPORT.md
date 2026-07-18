# Graph Report - data-analyst-agent  (2026-07-18)

## Corpus Check
- 48 files · ~16,412 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 316 nodes · 477 edges · 24 communities (18 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c631d339`
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
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 17 edges
2. `Database` - 15 edges
3. `ask_stream()` - 14 edges
4. `State` - 12 edges
5. `Les 11 décisions` - 12 edges
6. `Result` - 11 edges
7. `Échec` - 11 edges
8. `SQLiteDatabase` - 11 edges
9. `call_model()` - 11 edges
10. `Réponse` - 11 edges

## Surprising Connections (you probably didn't know these)
- `ask_stream()` --references--> `Événement`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → frontend/src/events.ts
- `_flux_agent()` --references--> `Événement`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → frontend/src/events.ts
- `_flux_outils()` --references--> `Événement`  [EXTRACTED]
  src/data_analyst_agent/agent/graph.py → frontend/src/events.ts
- `State` --uses--> `ExécOutil`  [INFERRED]
  src/data_analyst_agent/agent/graph.py → src/data_analyst_agent/agent/tools.py
- `lancer()` --calls--> `ask()`  [INFERRED]
  src/eval/run.py → src/data_analyst_agent/agent/graph.py

## Import Cycles
- None detected.

## Communities (24 total, 6 thin omitted)

### Community 3 - "Community 3"
Cohesion: 0.33
Nodes (9): call_model(), Décision, _llm(), _outil_openai(), Description d'un outil, indépendante du provider (JSON Schema des args)., Ce que rend `call_model` — vocabulaire à nous, pas LangChain., Format function-calling attendu par `bind_tools` (schéma OpenAI)., Un tour de dialogue avec le LLM. Rend une `Décision` neutre.      - `appels` non (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (35): construire_agent(), _faire_nœud_outils(), Compile le graphe pour une connexion donnée + le prompt (fixe pour la     connex, extraire_submit(), ExécOutil, exécuter(), _lignes_dicts(), Extrait les champs sémantiques d'un appel submit_answer (données exclue :     re (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (25): 10. Dialecte inconnu, 11. Langue & état, 1. Source de données, 2. Nature de l'agent, 3. Type de retour, 4. Évaluation — golden set D'ABORD, 5. Framework, 6. Sécurité (défense mécanique, ne dépend jamais du LLM) (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (18): 10. Ordre de construction (raffine SCOPE §« Ordre de construction »), 1. Les 4 modules et la règle de dépendance, 2. Arborescence, 3. Types partagés et internes, 4. Frontières délicates (les décisions qui empêchent le spaghetti), 5. Stratégie d'erreurs (« define errors out of existence »), 6. Topologie du graphe (`agent/graph.py`), 7. Assemblage du prompt (`agent/prompt.py`, `agent/dialects/`) (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (20): CasÉval, lancer(), main(), rapport(), True si tous les paliers atteignent leur seuil., _verdict(), agréger(), _cellules() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (28): Final, Hypothèse, OutilAppelé, Le modèle a décidé d'appeler un outil (émis avant l'exécution)., Retour d'un `run_query` exécuté : SQL tenté + issue (DESIGN §5)., Une interprétation retenue par le modèle en cas d'ambiguïté., Dernier événement : porte la `Réponse` publique (drain-to-final)., RésultatOutil (+20 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (17): 1. Le type de retour est le tien, 1. Plus de code au démarrage, 2. Courbe d'apprentissage LangGraph, 2. Le refus de répondre (palier 5) devient possible, 3. La double troncature (50 lignes → LLM, 10 000 → `données`), 3. On réécrit des choses déjà résolues, 4. Debugging transparent, 4. Surface de bug plus grande (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.22
Nodes (8): Ce qui a été construit (ordre du DESIGN §10), Ce qui n'a **pas** été testé, Configuration mise en place, Décisions prises en autonomie (à valider), Les 2 échecs résiduels (sous le seuil de tolérance, non bloquants), Pour relancer toi-même, Rapport d'implémentation — data-analyst-agent, Verdict

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (19): DataTable(), PASTILLE, ReasoningPanel(), ResultPanel(), Sql(), LIBELLÉS, StatusBadge(), demanderFlux() (+11 more)

### Community 16 - "Community 16"
Cohesion: 0.10
Nodes (20): dependencies, highlight.js, react, react-dom, react-markdown, description, devDependencies, @types/react (+12 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (14): Any, créer_app(), _flux_sse(), QuestionEntrée, Pydantic en ENTRÉE seulement (décision 4). Le seul champ du fil montant., Sérialise un objet en un événement SSE (`data: <json>\\n\\n`).      `ensure_asci, Générateur SSE : itère `ask_stream()` et traduit chaque événement.      Générate, _sse() (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, emitDeclarationOnly, module, moduleResolution, outDir, skipLibCheck (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (6): Contexte, Décisions verrouillées (ne pas re-litiger), Handoff — Implémentation frontend (data-analyst-agent), Ordre de construction, Pièges connus / points de vigilance, Suggested skills

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (3): construire_prompt_système(), _fiche_dialecte(), Sélectionne la fiche du dialecte, repli sur ansi.md si absente (SCOPE §10).

## Knowledge Gaps
- **120 isolated node(s):** `block-dangerous-git.sh script`, `name`, `private`, `version`, `type` (+115 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Événement` connect `Community 15` to `Community 9`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `ask_stream()` connect `Community 9` to `Community 18`, `Community 15`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `Database` connect `Community 5` to `Community 9`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Database` (e.g. with `Result` and `Échec`) actually correct?**
  _`Database` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `State` (e.g. with `Final` and `Hypothèse`) actually correct?**
  _`State` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `block-dangerous-git.sh script`, `name`, `private` to the rest of the system?**
  _164 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._