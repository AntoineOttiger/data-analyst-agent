# Scope — data-analyst-agent

Agent autonome qui répond à des questions en langage naturel sur une base de données
en écrivant et exécutant lui-même du SQL (lecture seule).

**Périmètre de cette phase : le fonctionnel uniquement.** L'interface graphique est
anticipée dans l'architecture (coutures identifiées) mais pas construite maintenant.

---

## Vision

L'utilisateur pose une question en texte libre ; l'agent explore la base de façon
autonome (boucle ReAct) et renvoie une réponse structurée, avec ses hypothèses et la
trace des requêtes exécutées. **Objectif de généralité assumé : viser large dès le
départ** — l'agent doit fonctionner sur n'importe quelle base, pas sur un schéma
spécifique. Chinook (SQLite) est le premier banc d'essai, pas la cible.

---

## Les 11 décisions

### 1. Source de données
SQLite local, dataset connu (**Chinook**) comme banc d'essai. **Couche d'accès fine**
(`list_tables`, `get_schema`, `run_query` comme fonctions Python) dont SQLite est la
première implémentation ; bascule Postgres / autre SGBD prévue.

### 2. Nature de l'agent
Boucle **ReAct outillée** : l'agent décide quels outils appeler, dans quel ordre, quand
il a fini. **Autonomie totale avec hypothèses annoncées** — l'agent choisit une
interprétation en cas d'ambiguïté et l'annonce (`hypothèses`), il ne repose pas de
question. Interface = fonction `ask(question) -> Réponse`.

### 3. Type de retour
```python
@dataclass
class Réponse:
    prose: str                     # réponse en langage naturel
    données: list[dict] | None     # lignes brutes de la requête finale (pour la GUI)
    sql: list[str]                 # TOUTES les requêtes exécutées (audit) — rempli par le code
    hypothèses: list[str]          # interprétations retenues
    statut: Literal["ok", "échec", "budget_dépassé"]
```
**Double vue du résultat**, sans jamais réécrire le SQL (voir §6) :
- vers le **LLM** : ~50 lignes + total, pour raisonner sans noyer le contexte ;
- vers **`données`** : cap de sécurité large (~10 000), pour la GUI.
Toute troncature est **annoncée** (« calculé sur l'ensemble, affichage limité à N »).

### 4. Évaluation — golden set D'ABORD
Harnais d'éval écrit **avant** la boucle agentique. ~25 questions dont on connaît la
réponse, **comparaison sur le résultat** (jamais sur le SQL). Taille plafonnée par ce
qu'un humain peut vérifier sérieusement. Questions **graduées en 5 paliers** :
1. une table, un agrégat ; 2. jointure évidente ; 3. ambiguïté (teste que l'hypothèse est
annoncée) ; 4. **piège sémantique** (crédible mais faux — le vrai différenciateur) ;
5. **impossible** → la bonne réponse est `statut="échec"` (refuser = succès).
Le SQL de référence s'écrit contre le schéma, jamais depuis la sortie de l'agent.
**L'autorité vient de la vérification humaine, pas de l'auteur.**

### 5. Framework
**LangGraph au niveau graphe explicite** (on écrit nœuds + arêtes). **Interdit** : les
helpers « SQL agent en une fonction » type `create_sql_agent` (déprécié, renvoie une
string, empêche `statut="échec"` et la `Réponse` structurée). LangGraph apporte
l'orchestration, le multi-provider et le function-calling normalisé (→ indépendance vis-à-
vis du provider). Détail : [langgraph-graph-explicite-vs-helpers.md](./langgraph-graph-explicite-vs-helpers.md).
Modèle : **Mistral `mistral-small-2603`** (gratuit, ~1 Md tokens/mois, ~1 req/s,
contexte 256k, function-calling supporté). Appel du modèle isolé derrière une fonction
`call_model()` pour pouvoir changer de LLM / diagnostiquer « agent vs modèle ».

### 6. Sécurité (défense mécanique, ne dépend jamais du LLM)
- **Connexion read-only au niveau moteur** (`file:...?mode=ro`) — écriture physiquement
  impossible.
- **`fetchmany(N)` + timeout d'exécution** — la requête s'exécute complète et juste, on
  borne seulement ce qu'on lit et le temps. **Aucune réécriture du SQL de l'agent**
  (un `LIMIT` injecté fausserait les agrégats / `GROUP BY`).
- Prompt « SELECT only » présent mais **jamais compté comme défense**.
- Validation SQL (allowlist) **différée** jusqu'au passage Postgres.
- Injection de prompt **non traitée à part** : A + les bornes la rendent inoffensive.

### 7. Terminaison
Outil **`submit_answer(prose, données, statut, hypothèses)`** = **unique porte de
sortie** ; l'appeler termine la boucle. Le champ **`sql` est rempli par le code** à partir
des requêtes réellement exécutées (pas par l'agent). **Budget de tours borné** (~10) →
si dépassé, sortie forcée en `statut="budget_dépassé"` avec le SQL déjà tenté.
**On ne force jamais une conclusion** (pas d'invitation à halluciner).

**`State` interne ⊃ `Réponse` publique.** Ce qui circule dans le graphe est un `State`
(interne à `agent`, jamais exporté) qui contient la mémoire de travail — historique des
messages, compteur de tours, `sql_exécuté` accumulé par l'adaptateur `run_query` — **plus**
les champs de sortie. `submit_answer` écrit les 4 champs sémantiques (`prose`, `données`,
`hypothèses`, `statut`) ; `sql` est accumulé par le code. À la terminaison, **`ask()`
projette le `State` vers les 5 champs de `Réponse`** : la mémoire de travail ne franchit
jamais la frontière du module (couture GUI/audit non polluée).

### 8. Outils & schéma
**4 outils** : `list_tables`, `get_schema`, `run_query`, `submit_answer`. Schéma
**découvert dynamiquement par l'agent** via les outils (introspection au runtime), aucun
schéma codé en dur. Choix cohérent avec l'objectif « n'importe quelle base » : passe à
l'échelle sur les grosses bases où l'on ne peut pas tout injecter dans le prompt.

### 9. Dialecte SQL
**Fiche de dialecte injectée dans le prompt** selon le SGBD connecté (une fiche par type
de SGBD : SQLite, Postgres, …). Pas de couche de transpilation (mode d'échec = résultat
silencieusement faux). L'auto-correction de la boucle ReAct rattrape le reste.

### 10. Dialecte inconnu
**Fiche générique de repli (SQL ANSI)** pour tout SGBD sans fiche dédiée + auto-correction
→ dégradation gracieuse (l'agent tente toujours, ne refuse pas). Cohérent avec « viser
large ». Limite assumée : ne couvre pas les divergences qui produisent un résultat faux
sans erreur.

### 11. Langue & état
- **L'agent répond dans la langue de la question** et s'adapte à la langue du schéma
  (pont multilingue = compétence attendue). Golden set **en français** sur Chinook
  anglais.
- **Sans état maintenant**, signature **`ask(question, historique=None)`** préparée pour
  le conversationnel plus tard (A = cas particulier de B). Golden set teste le mode isolé.

---

## Coutures anticipant la GUI (construites maintenant, exploitées plus tard)
- `ask(question, historique=None) -> Réponse` : fonction (presque) pure, posable derrière
  n'importe quelle interface.
- `Réponse.données` séparé de `Réponse.prose` : la GUI fait ses tableaux/graphiques.
- `Réponse.sql` : trace d'audit affichable.
- `call_model()` : provider interchangeable.
- Couche d'accès DB abstraite : SGBD interchangeable.

## Hors scope (cette phase)
Interface graphique · conversationnel multi-tours · transpilation SQL · validation SQL
par allowlist · RAG / sélection sémantique de schéma · écriture dans la base.

## Ordre de construction
1. Couche d'accès DB (read-only, `fetchmany`, introspection) + connexion Chinook.
2. **Golden set (~25 questions FR graduées + SQL de référence vérifié).**
3. Graphe LangGraph explicite (nœuds, `State` interne ⊃ `Réponse`, budget, `submit_answer`).
4. Fiches de dialecte + repli ANSI.
5. Itération mesurée contre le golden set.
