// Contrat SSE modélisé en union discriminée (DESIGN décision 9).
// Miroir des dataclasses `Événement` du back, MAIS au vocabulaire ascii/anglais
// du fil (traduit dans `api/translate.py`). Le discriminant est `type` → `switch`
// exhaustif chez le consommateur.

export type StatutOutil = "success" | "error" | "timeout";
export type StatutFinal = "ok" | "error" | "budget_exceeded";

/** Une ligne de données : colonnes SQL → valeurs (clés déjà ascii). */
export type Ligne = Record<string, unknown>;

/** Le modèle a décidé d'appeler un outil (émis avant l'exécution). */
export interface OutilAppelé {
  type: "tool_call";
  name: string;
  args: Record<string, unknown>;
}

/** Retour d'un run_query : SQL tenté + issue. */
export interface RésultatOutil {
  type: "tool_result";
  sql: string;
  status: StatutOutil;
  row_count: number | null;
  message: string | null;
}

/** Une interprétation retenue en cas d'ambiguïté. */
export interface Hypothèse {
  type: "assumption";
  text: string;
}

/** Dernier événement : la Réponse publique projetée. */
export interface Final {
  type: "final";
  answer: string;
  rows: Ligne[] | null;
  sql: string[];
  assumptions: string[];
  status: StatutFinal;
}

export type Événement = OutilAppelé | RésultatOutil | Hypothèse | Final;

/** Événements de trace (tout sauf le Final) — ce qui défile dans le panneau gauche. */
export type ÉvénementTrace = OutilAppelé | RésultatOutil | Hypothèse;
