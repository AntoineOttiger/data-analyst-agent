import { useRef, useState } from "react";
import { demanderFlux } from "./api";
import type { Final, Événement, ÉvénementTrace } from "./events";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { ResultPanel } from "./components/ResultPanel";

type Phase = "repos" | "flux" | "fini" | "erreur";

const EXEMPLES = [
  "Quels sont les 5 artistes avec le plus d'albums ?",
  "Quel pays génère le plus de revenus ?",
  "Combien de pistes durent plus de 5 minutes ?",
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [trace, setTrace] = useState<ÉvénementTrace[]>([]);
  const [final, setFinal] = useState<Final | null>(null);
  const [phase, setPhase] = useState<Phase>("repos");
  const [erreur, setErreur] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);

  const enCours = phase === "flux";

  async function lancer(q: string) {
    if (enCours || !q.trim()) return;
    setTrace([]);
    setFinal(null);
    setErreur(null);
    setPhase("flux");
    const ctrl = new AbortController();
    abort.current = ctrl;

    try {
      await demanderFlux(
        q,
        (é: Événement) => {
          if (é.type === "final") setFinal(é);
          else setTrace((t) => [...t, é]);
        },
        ctrl.signal,
      );
      setPhase("fini");
    } catch (e) {
      if (ctrl.signal.aborted) {
        setPhase("repos");
        return;
      }
      setErreur(e instanceof Error ? e.message : String(e));
      setPhase("erreur");
    }
  }

  function annuler() {
    abort.current?.abort();
  }

  return (
    <div className="app">
      <header className="entete">
        <h1>
          data-analyst-agent <span className="mono sous-titre">// console</span>
        </h1>
        <p className="pitch">
          Pose une question en langage naturel sur la base <code>chinook</code>.
          L'agent explore le schéma, écrit du SQL, et raisonne en direct.
        </p>
      </header>

      <form
        className="barre"
        onSubmit={(e) => {
          e.preventDefault();
          lancer(question);
        }}
      >
        <input
          className="champ"
          type="text"
          placeholder="Ex. : Quel pays génère le plus de revenus ?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={enCours}
        />
        {enCours ? (
          <button type="button" className="btn btn-stop" onClick={annuler}>
            arrêter
          </button>
        ) : (
          <button type="submit" className="btn" disabled={!question.trim()}>
            demander
          </button>
        )}
      </form>

      {phase === "repos" && trace.length === 0 && (
        <div className="exemples">
          {EXEMPLES.map((ex) => (
            <button
              key={ex}
              className="chip"
              onClick={() => {
                setQuestion(ex);
                lancer(ex);
              }}
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {erreur && <div className="erreur">Erreur : {erreur}</div>}

      <main className="zones">
        <ReasoningPanel trace={trace} enCours={enCours} />
        <ResultPanel final={final} />
      </main>
    </div>
  );
}
