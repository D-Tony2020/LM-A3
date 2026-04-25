# Error analysis — `gemma_1b` / `gemma1b_k3_random` (dev)

- Total queries: **466**
- Executed cleanly: **151** (32.4%)
- Errored: **315** (67.6%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 167 | 35.8% |
| `no_such_column` | 83 | 17.8% |
| `no_such_table` | 38 | 8.2% |
| `syntax_error` | 18 | 3.9% |
| `ambiguous_column` | 5 | 1.1% |
| `incomplete_input` | 3 | 0.6% |
| `other` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=167)

- query #0, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , flight_fare flight_fare_1 , fare fare_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1…
  ```

- query #12, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

### `no_such_column` (n=83)

- query #7, error: `OperationalError: no such column: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, flight_fare flight_fare_1, fare fare_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

- query #9, error: `OperationalError: no such column: airport_service_2.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1 , city city_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'NEWARK' AND flight_1.to_airport = airpo…
  ```

### `no_such_table` (n=38)

- query #2, error: `OperationalError: no such table: flight_basis`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , flight_basis fare_basis_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.ai…
  ```

- query #47, error: `OperationalError: no such table: schedule`
  ```sql
  SELECT DISTINCT ground_transportation FROM schedule WHERE city = 'PHILADELPHIA' AND date = 'WEDNESDAY'
  ```

### `syntax_error` (n=18)

- query #23, error: `OperationalError: near "I": syntax error`
  ```sql
  I'm sorry, I cannot fulfill this request. The instruction is ambiguous and requires more context.
  ```

- query #43, error: `OperationalError: near "f": syntax error`
  ```sql
  SELECT DISTINCT a.aircraft_type FROM aircraft a , flight f , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE f.departure_time < (SELECT MAX(departure_time) FROM flight f , airport_service airport_service_1 , city city_1 , ai…
  ```

### `ambiguous_column` (n=5)

- query #10, error: `OperationalError: ambiguous column name: flight_1.flight_id`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.to_airport = airport_service_1.airport_code AND flight_1.from_airport…
  ```

- query #13, error: `OperationalError: ambiguous column name: flight_1.flight_id`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_servi…
  ```

### `incomplete_input` (n=3)

- query #247, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , flight_fare flight_fare_1 , flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code AND far…
  ```

- query #264, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id, fare_1.fare_id FROM flight flight_1, fare_basis fare_basis_1, days days_1, date_day date_day_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport airport_1, days days_2, date_day date_day_2 WHER…
  ```

### `other` (n=1)

- query #460, error: `OperationalError: unrecognized token: ":"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time BETWEEN '2023-06-03 00:00:00' AND '2023-06-03 1200:00':
  ```
