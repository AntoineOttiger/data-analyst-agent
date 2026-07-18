import type { Ligne } from "../events";

const PLAFOND = 200; // lignes AFFICHÉES (décision 8) ; cohérent SCOPE §3.

function cellule(v: unknown): string {
  if (v === null || v === undefined) return "∅";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

/** Tableau des données finales, plafonné à 200 lignes affichées avec bandeau. */
export function DataTable({ rows }: { rows: Ligne[] }) {
  if (rows.length === 0) {
    return <p className="vide">Aucune ligne renvoyée.</p>;
  }
  const colonnes = Object.keys(rows[0]);
  const vues = rows.slice(0, PLAFOND);
  const tronqué = rows.length > PLAFOND;

  return (
    <div className="tableau-bloc">
      {tronqué && (
        <div className="bandeau">
          affichage limité à {PLAFOND} lignes sur {rows.length}
        </div>
      )}
      <div className="tableau-scroll">
        <table className="tableau">
          <thead>
            <tr>
              {colonnes.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {vues.map((ligne, i) => (
              <tr key={i}>
                {colonnes.map((c) => (
                  <td key={c}>{cellule(ligne[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
