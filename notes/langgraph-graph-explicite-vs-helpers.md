# LangGraph : graphe explicite vs helpers préfabriqués

> Décision prise pour le projet **data-analyst-agent** : on construit l'agent au niveau
> **graphe explicite** (on écrit les nœuds et les arêtes), on s'interdit les helpers
> « SQL agent en une fonction » type `create_sql_agent`.
>
> Ce document justifie ce choix et sert de référence quand la tentation reviendra de
> « juste utiliser le préfabriqué pour aller plus vite ».

---

## Les deux niveaux d'abstraction

| Niveau                                                                                                   | Ce que tu écris                                                                                                                                                          | Ce que le framework fournit                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Helper préfabriqué** (`create_sql_agent`, `create_react_agent`, `NLSQLTableQueryEngine`) | Une config : la connexion DB, le modèle, éventuellement un prompt.                                                                                                      | **Tout** : la boucle, la décision d'appeler un outil, le format de sortie, la gestion d'erreur, l'arrêt.                                                         |
| **Graphe explicite** (LangGraph : `StateGraph`, nœuds, arêtes)                                 | Les**nœuds** (appeler le modèle, exécuter l'outil, formater la réponse), les **arêtes** (qui décide du prochain nœud), et le **state** partagé. | L'**orchestration** (exécuter le graphe, router selon les arêtes), la persistance du state, l'intégration multi-provider, la normalisation du function-calling. |

Rappel important : côté LangChain, `create_sql_agent` est aujourd'hui **déprécié**. La
voie recommandée est justement le graphe explicite. Le « préfabriqué magique » n'est
donc plus le chemin principal — le débat porte surtout sur les helpers résiduels et sur
la tentation de trop déléguer.

---

## Avantages du graphe explicite

### 1. Le type de retour est le tien

C'est la raison n°1 pour ce projet. On a décidé que l'agent renvoie un objet à cinq
champs :

```python
@dataclass
class Réponse:
    prose: str
    données: list[dict] | None
    sql: list[str]
    hypothèses: list[str]
    statut: Literal["ok", "échec", "budget_dépassé"]
```

Un helper préfabriqué renvoie une **string**. On ne peut pas y greffer `données`, `sql`,
`hypothèses` ni surtout `statut` sans se battre contre le wrapper. Le graphe explicite
place ce type au centre : c'est le `state` qui traverse les nœuds.

### 2. Le refus de répondre (palier 5) devient possible

On veut que l'agent réponde `statut="échec"` quand la donnée n'est pas dans la base
(« quelle est la météo à Paris ? »). Un helper suppose toujours qu'une réponse existe et
la fabrique. Le graphe explicite permet une arête conditionnelle « la donnée est-elle
atteignable ? → nœud d'échec ». C'est un différenciateur du projet, impossible à obtenir
proprement avec un préfabriqué.

### 3. La double troncature (50 lignes → LLM, 10 000 → `données`)

Deux consommateurs du résultat d'une requête (le LLM, la future GUI) ont des besoins
différents. Le graphe explicite laisse un nœud « exécuter la requête » appliquer les deux
politiques de troncature séparément. Un helper applique une seule vue, généralement tout
vers le contexte du LLM.

### 4. Debugging transparent

Quand un cas piège (palier 4) échoue, on doit voir exactement ce qui est parti dans le
prompt. Dans un nœud, c'est un `print` / un log. Dans un helper, il faut remonter
plusieurs couches de callbacks pour intercepter le prompt réel.

### 5. Contrôle du budget et de l'arrêt

La boucle ReAct a un budget de tours. Le graphe explicite rend ce budget visible (un
compteur dans le state, une arête « budget dépassé → `statut="budget_dépassé"` »). Le
helper cache sa condition d'arrêt.

### 6. Valeur portfolio réelle

Un repo qui montre un graphe LangGraph écrit à la main, avec éval et refus de répondre,
démontre une compétence. Un repo qui appelle `create_sql_agent(db, llm)` démontre qu'on
sait lire un tutoriel. L'objectif d'employabilité est mieux servi par le niveau explicite.

---

## Inconvénients du graphe explicite

### 1. Plus de code au démarrage

Il faut écrire les nœuds, les arêtes, le schéma du state. ~150 lignes contre ~20. Le
premier « ça répond » arrive plus tard.

### 2. Courbe d'apprentissage LangGraph

`StateGraph`, réducteurs de state, arêtes conditionnelles, checkpointing : autant de
concepts à absorber. Un helper les cache.

### 3. On réécrit des choses déjà résolues

Le helper a déjà pensé à des cas limites (retry basique, formatage). En explicite, on les
réimplémente — mais c'est aussi ce qui nous permet de les faire *à notre façon*.

### 4. Surface de bug plus grande

Plus de code écrit = plus d'endroits où se tromper. La boucle, le budget, le routage sont
sous notre responsabilité.

---

## Avantages des helpers préfabriqués

- **Vitesse de démarrage** : une démo qui marche en quelques minutes.
- **Cas d'usage simple couvert** : pour un texte→SQL basique qui renvoie une phrase, ça
  suffit et c'est robuste.
- **Moins de surface de bug** : moins de code écrit.
- **Bon pour un prototype jetable** ou une preuve de faisabilité de 10 minutes.

## Inconvénients des helpers préfabriqués

- **Retour en string** : incompatible avec l'objet `Réponse` à cinq champs.
- **Pas de refus de répondre** : le palier 5 est inatteignable proprement.
- **Sortie et troncature non contrôlées** : une seule vue du résultat.
- **Boîte noire au debugging** : le prompt réel est difficile à intercepter.
- **Souvent déprécié** (`create_sql_agent`) : on construirait sur une voie abandonnée.
- **Faible valeur portfolio** : ne démontre pas la maîtrise du framework.

---

## Synthèse pour ce projet

**LangGraph pour la plomberie, nos décisions pour la valeur.**

Le graphe nous donne l'orchestration, le multi-provider et le function-calling normalisé
(donc l'indépendance vis-à-vis de Mistral) ainsi que le nom sur le CV. Ce qui distingue
ce repo des milliers de tutoriels « SQL agent », c'est ce qui vit **au-dessus** du
framework et nous appartient : le harnais d'éval (golden set gradué), le refus de
répondre, et la `Réponse` structurée.

Le surcoût en lignes de code est réel mais faible en valeur absolue (~150 lignes), et il
est exactement le cœur intellectuel du projet — pas une corvée à externaliser.

**Ligne rouge :** pas de helper « SQL agent en une fonction », même s'il en existe encore
un qui marche. Le préfabriqué est précisément la couche qui interdit d'aller plus loin
que ce qui est déjà fait.
