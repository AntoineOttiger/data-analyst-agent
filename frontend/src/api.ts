import type { Événement } from "./events";

// POST /api/ask renvoie du SSE (décision 4). EventSource natif est GET-only, donc
// on lit le corps en flux (fetch + ReadableStream) et on parse les trames SSE à
// la main : chaque trame = bloc séparé par "\n\n", ligne "data: <json>".

/**
 * Ouvre le flux SSE et appelle `onÉvénement` pour chaque événement décodé.
 * Résout quand le flux se termine ; rejette sur erreur HTTP/réseau (hors abort).
 */
export async function demanderFlux(
  question: string,
  onÉvénement: (é: Événement) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status} ${res.statusText}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let tampon = "";

  const vider = (bloc: string) => {
    // Une trame peut porter plusieurs lignes ; on ne retient que les "data:".
    const données = bloc
      .split("\n")
      .filter((l) => l.startsWith("data:"))
      .map((l) => l.slice(5).trim())
      .join("\n");
    if (données) onÉvénement(JSON.parse(données) as Événement);
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    tampon += decoder.decode(value, { stream: true });
    let i: number;
    while ((i = tampon.indexOf("\n\n")) >= 0) {
      vider(tampon.slice(0, i));
      tampon = tampon.slice(i + 2);
    }
  }
  if (tampon.trim()) vider(tampon); // trame résiduelle sans double saut final
}
