# Error analysis — `gemma_1b` / `gemma1b_k3_bm25` (dev)

- Total queries: **466**
- Executed cleanly: **272** (58.4%)
- Errored: **194** (41.6%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 120 | 25.8% |
| `no_such_column` | 56 | 12.0% |
| `syntax_error` | 11 | 2.4% |
| `no_such_table` | 3 | 0.6% |
| `query_timeout` | 2 | 0.4% |
| `ambiguous_column` | 1 | 0.2% |
| `other` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=120)

- query #0, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

- query #2, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_se…
  ```

### `no_such_column` (n=56)

- query #6, error: `OperationalError: no such column: flight_1.flight_status`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

- query #22, error: `OperationalError: no such column: airport_service_2.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'BALTIMORE' AND( flight_1.to_airport = …
  ```

### `syntax_error` (n=11)

- query #28, error: `OperationalError: near "The": syntax error`
  ```sql
  The cost of united airlines flight 415 from chicago to kansas city thursday night is not available.
  ```

- query #52, error: `OperationalError: near "19": syntax error`
  ```sql
  SELECT DISTINCT price FROM flight 19 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE airline_1.airline_code = flight_19.airline_code AND flight_19.from_airport = airport_service_1.airport_code AND airport_service_1.city_co…
  ```

### `no_such_table` (n=3)

- query #336, error: `OperationalError: no such table: airport_airport`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , flight_stop flight_stop_1 , airport_airport airport_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airp…
  ```

- query #388, error: `OperationalError: no such table: flightfare`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , flightfare flightfare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

### `query_timeout` (n=2)

- query #195, error: `Query timed out`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, flight_fare flight_fare_1 , fare fare_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.…
  ```

- query #264, error: `Query timed out`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , flight_fare flight_fare_1 , fare fare_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1…
  ```

### `ambiguous_column` (n=1)

- query #170, error: `OperationalError: ambiguous column name: airport_service_1.miles_distant`
  ```sql
  SELECT DISTINCT airport_service_1.miles_distant FROM airport_service airport_service_1 , city city_1 , airport_service airport_service_1 , airport airport_1 WHERE airport_service_1.airport_code = 'DFW' AND airport_service_1.city_code = 'DALLAS'
  ```

### `other` (n=1)

- query #311, error: `OperationalError: unrecognized token: "718am"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.airline_code = 'TW' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_co…
  ```
