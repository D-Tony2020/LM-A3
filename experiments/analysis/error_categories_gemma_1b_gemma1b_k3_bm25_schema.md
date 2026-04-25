# Error analysis — `gemma_1b` / `gemma1b_k3_bm25_schema` (dev)

- Total queries: **466**
- Executed cleanly: **288** (61.8%)
- Errored: **178** (38.2%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 109 | 23.4% |
| `no_such_column` | 56 | 12.0% |
| `syntax_error` | 7 | 1.5% |
| `ambiguous_column` | 3 | 0.6% |
| `other` | 2 | 0.4% |
| `no_such_table` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=109)

- query #2, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_se…
  ```

- query #12, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 WHERE flight_1.airline_code = 'AA' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_ser…
  ```

### `no_such_column` (n=56)

- query #22, error: `OperationalError: no such column: airport_service_2.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'BALTIMORE' AND( flight_1.to_airport = …
  ```

- query #26, error: `OperationalError: no such column: days_1.days_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.to_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_na…
  ```

### `syntax_error` (n=7)

- query #51, error: `OperationalError: near "The": syntax error`
  ```sql
  The provided data doesn't include the necessary information to construct the SQL query. The query needs to specify the `flights` table and the `from_airport` and `to_airport` columns.
  ```

- query #64, error: `OperationalError: near "FROM": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 , flight_fare flight_fare_1 , fare fare_1 , fare_basis fare_basis_1 , days days_2 , date…
  ```

### `ambiguous_column` (n=3)

- query #48, error: `OperationalError: ambiguous column name: flight_1.flight_id`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.c…
  ```

- query #56, error: `OperationalError: ambiguous column name: fare_1.fare_id`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, fare_basis fare_basis_1, flight flight_1, flight_fare flight_fare_1, fare fare_1, fare_basis fare_basis_1 WHERE( fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND fare_basis_1.class_type = 'BUSINESS' AND 1 = 1 ) AND fare_1.…
  ```

### `other` (n=2)

- query #55, error: `OperationalError: unrecognized token: "}"`
  ```sql
  }
  ```

- query #115, error: `OperationalError: unrecognized token: "}"`
  ```sql
  }
  ```

### `no_such_table` (n=1)

- query #110, error: `OperationalError: no such table: flights`
  ```sql
  SELECT DISTINCT flight_id FROM flights flights
  ```
