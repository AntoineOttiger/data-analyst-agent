## Dialecte SQL : ANSI (repli générique)

Le SGBD connecté n'a pas de fiche dédiée. Tiens-t'en au **SQL standard (ANSI)** et
reste prudent :

- Concaténation : `||` (standard). Évite les fonctions propriétaires.
- `SELECT ... FROM ... JOIN ... ON ...`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`.
- Pagination : `FETCH FIRST n ROWS ONLY` (le plus portable) ou `LIMIT n` si accepté.
- `NULL` : `IS NULL` / `IS NOT NULL` ; les agrégats ignorent les `NULL`.
- Évite : fonctions de date propriétaires, `ILIKE`, `LIMIT/OFFSET` exotiques,
  casts spécifiques. Privilégie `CAST(col AS type)`.
- En cas d'erreur du moteur, LIS le message et corrige : c'est ta boucle
  d'auto-correction.
