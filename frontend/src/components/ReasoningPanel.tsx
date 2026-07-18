import type { ÉvénementTrace } from "../events";

// Icône status d'un run_query → pastille colorée (technique, monospace).
const PASTILLE: Record<string, string> = {
  success: "pastille ok",
  error: "pastille err",
  timeout: "pastille timeout",
};

function LigneTrace({ é }: { é: ÉvénementTrace }) {
  switch (é.type) {
    case "tool_call": {
      const arg = typeof é.args.sql === "string" ? é.args.sql : "";
      return (
        <li className="trace-item trace-appel">
          <span className="tag">appel</span>
          <span className="mono nom-outil">{é.name}</span>
          {arg && <span className="mono arg">{arg}</span>}
        </li>
      );
    }
    case "tool_result":
      return (
        <li className="trace-item trace-res">
          <span className={PASTILLE[é.status] ?? "pastille"} />
          <span className="mono">
            {é.status === "success"
              ? `${é.row_count ?? 0} ligne(s)`
              : é.status === "timeout"
                ? "timeout"
                : "erreur"}
          </span>
          {é.message && <span className="mono err-msg">{é.message}</span>}
        </li>
      );
    case "assumption":
      return (
        <li className="trace-item trace-hyp">
          <span className="tag tag-hyp">hypothèse</span>
          <span>{é.text}</span>
        </li>
      );
  }
}

/** Panneau gauche : le flux ReAct qui défile en direct. */
export function ReasoningPanel({
  trace,
  enCours,
}: {
  trace: ÉvénementTrace[];
  enCours: boolean;
}) {
  return (
    <section className="panneau panneau-raison">
      <header className="panneau-titre">
        raisonnement
        {enCours && <span className="curseur">▍</span>}
      </header>
      {trace.length === 0 && !enCours ? (
        <p className="vide">La trace de raisonnement s'affichera ici.</p>
      ) : (
        <ul className="trace">
          {trace.map((é, i) => (
            <LigneTrace key={i} é={é} />
          ))}
          {enCours && (
            <li className="trace-item trace-attente">
              <span className="pastille pending" />
              <span className="mono">réflexion…</span>
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
