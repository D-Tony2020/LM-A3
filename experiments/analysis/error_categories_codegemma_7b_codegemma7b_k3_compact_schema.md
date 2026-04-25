# Error analysis — `codegemma_7b` / `codegemma7b_k3_compact_schema` (dev)

- Total queries: **466**
- Executed cleanly: **360** (77.3%)
- Errored: **106** (22.7%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 78 | 16.7% |
| `no_such_column` | 22 | 4.7% |
| `incomplete_input` | 4 | 0.9% |
| `other` | 1 | 0.2% |
| `syntax_error` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=78)

- query #15, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_servic…
  ```

- query #20, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.c…
  ```

### `no_such_column` (n=22)

- query #18, error: `OperationalError: no such column: city_1.city_`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , ai…
  ```

- query #23, error: `OperationalError: no such column: fare_1.round_trip_cost`
  ```sql
  SELECT DISTINCT flight_1.flight_id, fare_1.round_trip_cost FROM flight flight_1 , fare_basis fare_basis_1 , fare_basis fare_basis_2 , days days_1 , date_day date_day_1 , flight_fare flight_fare_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_…
  ```

### `incomplete_input` (n=4)

- query #106, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE fare_1.round_trip_cost IS NOT NULL AND fare_1.fare_bas…
  ```

- query #244, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , flight_fare flight_fare_1 , fare fare_1 , fare_basis fare_basis_1 WHERE flight_1.from_airport = airport_service_1.airport_…
  ```

### `other` (n=1)

- query #150, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , airline airline_1 , airline airline_2 WHERE ( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1…
  ```

### `syntax_error` (n=1)

- query #391, error: `OperationalError: near ".": syntax error`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , airport airport_1 , airport airport_2 , city city_1 , city city_2 , days days_1 WHERE fare_1.from_airport = airport_1.airport_code AND airport_1.city_code = city_1.city_code AND city_1.city_name = 'NEW YORK' AND fare_1.to_airport …
  ```
