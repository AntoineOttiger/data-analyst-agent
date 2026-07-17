## Dialecte SQL : PostgreSQL

Tu écris du SQL pour **PostgreSQL**. Points saillants :

- Concaténation : `||` ou `CONCAT(...)`. `col::text` pour caster.
- Guillemets : `'texte'` pour les littéraux, `"Identifiant"` pour un nom sensible à la
  casse. Les identifiants non cités sont repliés en minuscules.
- Dates/heures : types `date`, `timestamp` ; `EXTRACT(YEAR FROM col)`,
  `date_trunc('month', col)`, `col - interval '7 days'`.
- `LIMIT n OFFSET m`. `FETCH FIRST n ROWS ONLY` accepté.
- Division : entre entiers elle est entière ; force avec `col::numeric` ou `1.0 * a / b`.
- Texte insensible à la casse : `ILIKE`.
- Agrégats : `NULL` ignorés ; `bool_and`, `bool_or`, `string_agg(col, ',')` disponibles.
- `FULL OUTER JOIN` et `RIGHT JOIN` supportés.
