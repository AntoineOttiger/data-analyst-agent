import type { StatutFinal } from "../events";

// Un `échec` sur un cas « impossible » est un SUCCÈS du refus (décision 8) : on le
// montre dignement (ambre « refus assumé »), pas comme une panne rouge.
const LIBELLÉS: Record<StatutFinal, { texte: string; classe: string }> = {
  ok: { texte: "ok", classe: "badge-ok" },
  error: { texte: "refus assumé", classe: "badge-refus" },
  budget_exceeded: { texte: "budget dépassé", classe: "badge-budget" },
};

export function StatusBadge({ statut }: { statut: StatutFinal }) {
  const { texte, classe } = LIBELLÉS[statut] ?? LIBELLÉS.budget_exceeded;
  return <span className={`badge ${classe}`}>{texte}</span>;
}
