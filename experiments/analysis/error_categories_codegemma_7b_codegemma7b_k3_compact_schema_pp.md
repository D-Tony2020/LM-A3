# Error analysis — `codegemma_7b` / `codegemma7b_k3_compact_schema_pp` (dev)

- Total queries: **466**
- Executed cleanly: **377** (80.9%)
- Errored: **89** (19.1%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_column` | 59 | 12.7% |
| `syntax_error` | 22 | 4.7% |
| `other` | 4 | 0.9% |
| `incomplete_input` | 4 | 0.9% |

## Sample failing queries per category

### `no_such_column` (n=59)

- query #15, error: `OperationalError: no such column: airport_service_`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_servic…
  ```

- query #18, error: `OperationalError: no such column: city_1.city_`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , ai…
  ```

### `syntax_error` (n=22)

- query #82, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight fligh…
  ```

- query #84, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

### `other` (n=4)

- query #40, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 , fare fare_1 , fare_basis fare_basis_1 , days days_2 , date_day date_day_2 WHERE flight…
  ```

- query #118, error: `OperationalError: unrecognized token: "'BOSTON)"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport airport_1 , food_service food_service_1 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_servic…
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
