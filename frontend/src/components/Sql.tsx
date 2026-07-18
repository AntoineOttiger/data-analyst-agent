import { useMemo } from "react";
import hljs from "highlight.js/lib/core";
import sql from "highlight.js/lib/languages/sql";

// On n'enregistre QUE le langage SQL (bundle minimal). Le thème (couleurs des
// tokens .hljs-*) vit dans styles.css, calibré pour le fond sombre.
hljs.registerLanguage("sql", sql);

/** Bloc SQL colorisé sur fond sombre. */
export function Sql({ code }: { code: string }) {
  const html = useMemo(
    () => hljs.highlight(code, { language: "sql" }).value,
    [code],
  );
  return (
    <pre className="sql">
      <code
        className="hljs language-sql"
        // hljs produit un HTML de tokens sûr (échappe le code source).
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </pre>
  );
}
