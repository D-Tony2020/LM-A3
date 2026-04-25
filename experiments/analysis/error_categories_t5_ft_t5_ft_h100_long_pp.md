# Error analysis — `t5_ft` / `t5_ft_h100_long_pp` (dev)

- Total queries: **466**
- Executed cleanly: **361** (77.5%)
- Errored: **105** (22.5%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_column` | 39 | 8.4% |
| `syntax_error` | 36 | 7.7% |
| `other` | 18 | 3.9% |
| `ambiguous_column` | 6 | 1.3% |
| `incomplete_input` | 4 | 0.9% |
| `no_such_table` | 2 | 0.4% |

## Sample failing queries per category

### `no_such_column` (n=39)

- query #19, error: `OperationalError: no such column: days_1.days_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service…
  ```

- query #39, error: `OperationalError: no such column: flight_`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_id = flight_fare_1.fare_id AND flight_fare_1.flight_id = flight_
  ```

### `syntax_error` (n=36)

- query #2, error: `OperationalError: near "flight_1": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport…
  ```

- query #24, error: `OperationalError: near "flight_1": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

### `other` (n=18)

- query #15, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1, airport_service airport_service_1, …
  ```

- query #18, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1)
  ```

### `ambiguous_column` (n=6)

- query #20, error: `OperationalError: ambiguous column name: airport_service_2.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, flight_stop flight_stop_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airpo…
  ```

- query #123, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1, airport airport_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE ground_service_1.airp…
  ```

### `incomplete_input` (n=4)

- query #65, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, fare_basis fare_basis_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND far…
  ```

- query #120, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'KANSAS' AND flight_1.flight_id = flight_fare_1.flight_id AND flight_fare_1.fare_id = flight_fare_1.fare_id AND flight_fare_1.fare_id =
  ```

### `no_such_table` (n=2)

- query #263, error: `OperationalError: no such table: code_1`
  ```sql
  SELECT DISTINCT code_1.airline_code FROM code_1 WHERE code_1.airline_code = 'Y'
  ```

- query #270, error: `OperationalError: no such table: code_1`
  ```sql
  SELECT DISTINCT code_1.airline_code FROM code_1 WHERE code = 'YN'
  ```
