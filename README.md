# data-analyst-agent

Agent autonome qui répond en langage naturel à des questions sur une base SQL
(lecture seule) via une boucle **ReAct** outillée. Backend Python (LangGraph +
Mistral) ; frontend **React/Vite** « agent console » qui diffuse le raisonnement
en direct.

- **Quoi** → [docs/SCOPE.md](docs/SCOPE.md)
- **Comment c'est découpé** → [docs/DESIGN.md](docs/DESIGN.md)

Base d'essai figée : `database/chinook.db` (commitée, socle de l'éval).

---

## Architecture (frontière de dépendance)

```
frontend/ (React)  ──HTTP/SSE──►  api/ (FastAPI)  ──►  agent  ──►  db, model
                                                         │
                             tout le monde parle  ►  response (Réponse, neutre)
```

- `agent.ask_stream(question) -> Iterator[Événement]` est la **primitive** : elle
  diffuse la trace ReAct (`OutilAppelé`, `RésultatOutil`, `Hypothèse`) puis un
  `Final` portant la `Réponse`. `agent.ask()` en est le *drain-to-final*.
- `api/` **enrobe** `ask_stream` en SSE et **traduit** le vocabulaire FR maison en
  JSON ascii/anglais (`données→rows`, `prose→answer`, `hypothèses→assumptions`,
  `statut→status`). Le Python reste en français ; seul le fil est ascii.
- `frontend/` ne parle qu'à `/api/*` — jamais aux entrailles de l'agent.

---

## Prérequis

- Python ≥ 3.12, Node ≥ 18.
- Une clé Mistral dans `.env` à la racine (cf. `.env.example`) :
  ```
  MISTRAL_API_KEY=...
  ```

Installation Python (couche HTTP incluse) :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows PowerShell  (source .venv/bin/activate sous Unix)
pip install -e ".[api]"
```

---

## Lancer

### Mode démo (un seul process, une commande)

Le front est *buildé* puis servi par FastAPI en fichiers statiques (même origine,
pas de proxy) :

```powershell
# PowerShell : pas de && ; on enchaîne étape par étape.
cd frontend
npm install        # une seule fois (ou après un changement de dépendances)
npm run build
cd ..
python -m data_analyst_agent.api
```

Puis ouvrir **http://127.0.0.1:8000**. L'API et le front sont servis par le même
process. (Rebuild du front → relancer `npm run build`.)

> Sous bash/zsh (Unix), la même séquence chaînée : `cd frontend && npm install && npm run build && cd .. && python -m data_analyst_agent.api`.

### Mode développement (deux process, rechargement à chaud)

FastAPI sert l'API ; Vite sert le front avec HMR et **proxifie `/api/*` → :8000**.

```powershell
# terminal 1 — API
python -m data_analyst_agent.api

# terminal 2 — front (Vite)
cd frontend
npm install        # une seule fois
npm run dev
```

Puis ouvrir **http://127.0.0.1:5173** (le port Vite). Les appels `/api/ask` sont
proxifiés vers l'API.

Variables optionnelles : `API_HOST`, `API_PORT` (défaut `127.0.0.1:8000`),
`MISTRAL_MODEL`, `MISTRAL_RPS` (throttle anti-429, défaut `0.5`).

---

## Endpoints

| Méthode | Route           | Rôle                                                            |
| -------- | --------------- | ---------------------------------------------------------------- |
| `POST` | `/api/ask`    | SSE (`text/event-stream`) : un `data:` JSON par événement. |
| `GET`  | `/api/health` | Sonde de vie.                                                    |
| `GET`  | `/`           | Le front (StaticFiles) si`frontend/dist/` existe.              |

Corps de `POST /api/ask` : `{"question": "..."}`. Chaque événement SSE porte un
champ `type` discriminant : `tool_call` · `tool_result` · `assumption` · `final`.

---

## Éval

Golden set de 25 cas gradués (paliers 1→5) contre `chinook.db`, rapport ventilé
par palier :

```bash
python -m eval.run
```

`ask()` et l'éval empruntent le **même** chemin que l'UI (`ask_stream`) : une
seule source de vérité (DESIGN décision 11).
