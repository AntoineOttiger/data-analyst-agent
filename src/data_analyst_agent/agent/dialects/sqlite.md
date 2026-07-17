## Dialecte SQL : SQLite

Tu écris du SQL pour **SQLite**. Points saillants :

- Concaténation de chaînes : `||` (ex. `FirstName || ' ' || LastName`). Pas de `CONCAT`.
- Pas de `FULL OUTER JOIN` ni de `RIGHT JOIN` (utilise `LEFT JOIN` en inversant).
- Dates stockées en TEXTE ISO-8601 ; utilise `strftime('%Y', colonne)` pour extraire
  l'année, `date(colonne)`, `julianday(...)` pour les différences.
- `LIMIT n OFFSET m` pour paginer. `LIMIT` avec `ORDER BY` pour un « top n ».
- Division entière : `a / b` est entière si les deux sont entiers ; force le flottant
  avec `1.0 * a / b`.
- Comparaisons de texte insensibles à la casse : `LIKE` l'est pour l'ASCII ;
  `COLLATE NOCASE` au besoin.
- `NULL` : `col IS NULL` / `IS NOT NULL`. Les agrégats (`COUNT`, `AVG`) ignorent les
  `NULL` ; `COUNT(*)` les compte, `COUNT(col)` non.
- Booléens : pas de type dédié, utilise `0`/`1`.
