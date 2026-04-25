# Error analysis — `t5_ft` / `t5_ft_baseline_beam4` (dev)

- Total queries: **466**
- Executed cleanly: **307** (65.9%)
- Errored: **159** (34.1%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 102 | 21.9% |
| `no_such_column` | 46 | 9.9% |
| `syntax_error` | 6 | 1.3% |
| `incomplete_input` | 3 | 0.6% |
| `query_timeout` | 1 | 0.2% |
| `ambiguous_column` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=102)

- query #2, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_service_…
  ```

- query #6, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.stops = 0 AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.ci…
  ```

### `no_such_column` (n=46)

- query #28, error: `OperationalError: no such column: flight_fare_1.fare_i`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE fare_1.fare_id = flight_fare_1.fare_i
  ```

- query #39, error: `OperationalError: no such column: flight_`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_id = flight_fare_1.fare_id AND flight_fare_1.flight_id = flight_
  ```

### `syntax_error` (n=6)

- query #63, error: `OperationalError: near "1800": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

- query #146, error: `OperationalError: near ".": syntax error`
  ```sql
  SELECT DISTINCT class_of_service_1.class_type FROM class_of_service class_of_service_1 WHERE class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service_1.class_of_service…
  ```

### `incomplete_input` (n=3)

- query #65, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, fare_basis fare_basis_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND far…
  ```

- query #120, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = flight_1.airline_code AND flight_1.airline_code = 'CANADA' AND flight_1.to_airport = airport_servi…
  ```

### `query_timeout` (n=1)

- query #187, error: `Query timed out`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.flight_days = days_1.days_code AND days_1.day_name = date_day_1.day_name AND da…
  ```

### `ambiguous_column` (n=1)

- query #219, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'ORLANDO' AND ground_service_1.air…
  ```
