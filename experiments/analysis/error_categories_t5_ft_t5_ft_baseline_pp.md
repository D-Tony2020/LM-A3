# Error analysis — `t5_ft` / `t5_ft_baseline_pp` (dev)

- Total queries: **466**
- Executed cleanly: **337** (72.3%)
- Errored: **129** (27.7%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_column` | 74 | 15.9% |
| `syntax_error` | 39 | 8.4% |
| `aggregate_misuse` | 5 | 1.1% |
| `query_timeout` | 4 | 0.9% |
| `incomplete_input` | 2 | 0.4% |
| `other` | 2 | 0.4% |
| `no_such_table` | 1 | 0.2% |
| `ambiguous_column` | 1 | 0.2% |
| `unbalanced_parens` | 1 | 0.2% |

## Sample failing queries per category

### `no_such_column` (n=74)

- query #2, error: `OperationalError: no such column: airport_service_`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_service_…
  ```

- query #18, error: `OperationalError: no such column: flight`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1, fligh…
  ```

### `syntax_error` (n=39)

- query #12, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.airline_code = 'AA' AND( flight_1.from_airport = airport_service_1.airport_code…
  ```

- query #19, error: `OperationalError: near "8": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service…
  ```

### `aggregate_misuse` (n=5)

- query #107, error: `OperationalError: misuse of aggregate: MIN()`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.one_direction_cost =( SELECT MIN( fare_1.one_direction_cost ) FROM fare fare_)
  ```

- query #152, error: `OperationalError: misuse of aggregate: MIN()`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.one_direction_cost =( SELECT MIN( fare_1.one_direction_cost ) FROM fare fare_)
  ```

### `query_timeout` (n=4)

- query #28, error: `Query timed out`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, fare_basis fare_basis_1, days days_1, date_day date_day_1 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND fare_basis_1.fare_basis_code = fare_basis_1.fare_basis_code
  ```

- query #180, error: `Query timed out`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, flight_stop flight_stop_1, airport_service airport_service_3, city city_3 WHERE flight_1.airline_code = 'AA' AND( flight_1.from…
  ```

### `incomplete_input` (n=2)

- query #47, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1, days days_1, date_day date_day_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'PHILADELPHIA' AND ground_service_1.transport_type = 'COACH' AND ground_s…
  ```

- query #78, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.to_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_na…
  ```

### `other` (n=2)

- query #120, error: `OperationalError: unrecognized token: "'Id FROM flight flight_1, airport_service airport_service_1.airline_code AND airport_service_1.city_code ="`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'CANADA' AND flight_1.flight_id = flight_1.flight_id AND flight_1.airline_code = 'Id FROM flight flight_1, airport_service airport_service_1.airli…
  ```

- query #209, error: `OperationalError: unrecognized token: "')"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = 'AA' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

### `no_such_table` (n=1)

- query #122, error: `OperationalError: no such table: capacity_1`
  ```sql
  SELECT DISTINCT capacity_1.capacity_code FROM capacity_1 WHERE capacity = 'F28'
  ```

### `ambiguous_column` (n=1)

- query #219, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport airport_1, airport airport_1, airport_service airport_service_1, city city_2 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = …
  ```

### `unbalanced_parens` (n=1)

- query #311, error: `OperationalError: unrecognized token: "'718 ) )))"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = 'TW' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```
