# Error analysis — `t5_scr` / `t5_scr_h100_pp` (dev)

- Total queries: **466**
- Executed cleanly: **152** (32.6%)
- Errored: **314** (67.4%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_column` | 119 | 25.5% |
| `syntax_error` | 115 | 24.7% |
| `unbalanced_parens` | 52 | 11.2% |
| `other` | 18 | 3.9% |
| `no_such_table` | 10 | 2.1% |

## Sample failing queries per category

### `no_such_column` (n=119)

- query #0, error: `OperationalError: no such column: date_number`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

- query #5, error: `OperationalError: no such column: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = '…
  ```

### `syntax_error` (n=115)

- query #3, error: `OperationalError: near "PHOENIX": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

- query #9, error: `OperationalError: near "NEWARK": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

### `unbalanced_parens` (n=52)

- query #12, error: `OperationalError: near "PHOENIX": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

- query #17, error: `OperationalError: near "PHILADELPHIA": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

### `other` (n=18)

- query #19, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time BETWEEN 0 AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_c…
  ```

- query #46, error: `OperationalError: unrecognized token: "'PITTS)"`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, flight_fare flight_1, fare fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, fare_1, flight_1, fl…
  ```

### `no_such_table` (n=10)

- query #194, error: `OperationalError: no such table: fare_1`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, flight_fare flight_1, fare fare_1, fare_1, fare_1, fare_1, fare_basis fare_1, fare_basis fare_basis_1 WHERE flight_1.from_airpo…
  ```

- query #269, error: `OperationalError: no such table: airport_1`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = 'UA' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.…
  ```
