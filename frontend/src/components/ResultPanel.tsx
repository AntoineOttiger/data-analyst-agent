import { useState } from "react";
import Markdown from "react-markdown";
import type { Final } from "../events";
import { DataTable } from "./DataTable";
import { Sql } from "./Sql";
import { StatusBadge } from "./StatusBadge";

/** Accordéon des requêtes SQL exécutées (toutes, pour l'audit — décision 8). */
function SqlAccordéon({ requêtes }: { requêtes: string[] }) {
  const [ouvert, setOuvert] = useState(false);
  if (requêtes.length === 0) return null;
  return (
    <details className="accordeon" open={ouvert} onToggle={(e) => setOuvert((e.target as HTMLDetailsElement).open)}>
      <summary>
        SQL exécuté <span className="compteur">{requêtes.length}</span>
      </summary>
      <div className="accordeon-corps">
        {requêtes.map((q, i) => (
          <Sql key={i} code={q} />
        ))}
      </div>
    </details>
  );
}

/** Panneau droit : le résultat final (prose, hypothèses, données, SQL, statut). */
export function ResultPanel({ final }: { final: Final | null }) {
  if (!final) {
    return (
      <section className="panneau panneau-result">
        <header className="panneau-titre">résultat</header>
        <p className="vide">Le résultat apparaîtra ici une fois l'agent terminé.</p>
      </section>
    );
  }

  return (
    <section className="panneau panneau-result">
      <header className="panneau-titre">
        résultat <StatusBadge statut={final.status} />
      </header>

      <div className="prose">
        <Markdown>{final.answer}</Markdown>
      </div>

      {final.assumptions.length > 0 && (
        <div className="callout callout-hyp">
          <div className="callout-titre">Hypothèses retenues</div>
          <ul>
            {final.assumptions.map((h, i) => (
              <li key={i}>{h}</li>
            ))}
          </ul>
        </div>
      )}

      {final.rows && final.rows.length > 0 && <DataTable rows={final.rows} />}

      <SqlAccordéon requêtes={final.sql} />
    </section>
  );
}
