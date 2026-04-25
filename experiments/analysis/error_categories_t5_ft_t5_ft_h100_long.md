# Error analysis — `t5_ft` / `t5_ft_h100_long` (dev)

- Total queries: **466**
- Executed cleanly: **330** (70.8%)
- Errored: **136** (29.2%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 95 | 20.4% |
| `no_such_column` | 17 | 3.6% |
| `syntax_error` | 15 | 3.2% |
| `incomplete_input` | 3 | 0.6% |
| `ambiguous_column` | 3 | 0.6% |
| `no_such_table` | 2 | 0.4% |
| `other` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=95)

- query #2, error: `OperationalError: near "flight_1": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport…
  ```

- query #15, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1, airport_service airport_service_1, …
  ```

### `no_such_column` (n=17)

- query #19, error: `OperationalError: no such column: days_1.days_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time BETWEEN 0 AND 1200 AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service…
  ```

- query #39, error: `OperationalError: no such column: flight_`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_id = flight_fare_1.fare_id AND flight_fare_1.flight_id = flight_
  ```

### `syntax_error` (n=15)

- query #63, error: `OperationalError: near "1800": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

- query #96, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, flight_fare flight_fare_1, fare fare_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.flight_id = flight_fare_1.flight_id AND flight_fare_1.fare_id = fare_1.on…
  ```

### `incomplete_input` (n=3)

- query #65, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, fare_basis fare_basis_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND far…
  ```

- query #120, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'KANSAS' AND flight_1.flight_id = flight_fare_1.flight_id AND flight_fare_1.fare_id = flight_fare_1.fare_id AND flight_fare_1.fare_id =
  ```

### `ambiguous_column` (n=3)

- query #178, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport airport_1 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'DAL' AND flight_1.to_airport = airport_1.airport_code AND airport_1.airport_code = 'DAL'
  ```

- query #214, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport airport_1 WHERE flight_1.airline_code = 'UA' AND( flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'BWI' AND flight_1.to_airport = airport_1.airport_code AND airport_1.a…
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

### `other` (n=1)

- query #137, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.airline_code = 'CO' AND( flight_1.from_airport = airport_service_1.airport_code…
  ```
