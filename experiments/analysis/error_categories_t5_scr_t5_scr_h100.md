# Error analysis — `t5_scr` / `t5_scr_h100` (dev)

- Total queries: **466**
- Executed cleanly: **95** (20.4%)
- Errored: **371** (79.6%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 227 | 48.7% |
| `syntax_error` | 71 | 15.2% |
| `no_such_column` | 55 | 11.8% |
| `other` | 13 | 2.8% |
| `no_such_table` | 5 | 1.1% |

## Sample failing queries per category

### `unbalanced_parens` (n=227)

- query #2, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

- query #6, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

### `syntax_error` (n=71)

- query #3, error: `OperationalError: near "PHOENIX": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

- query #9, error: `OperationalError: near "NEWARK": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_…
  ```

### `no_such_column` (n=55)

- query #0, error: `OperationalError: no such column: date_number`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

- query #5, error: `OperationalError: no such column: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = airport_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = '…
  ```

### `other` (n=13)

- query #71, error: `OperationalError: unrecognized token: "'"`
  ```sql
  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = '
  ```

- query #103, error: `OperationalError: unrecognized token: "'"`
  ```sql
  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = '
  ```

### `no_such_table` (n=5)

- query #269, error: `OperationalError: no such table: airport_1`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = 'UA' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.…
  ```

- query #316, error: `OperationalError: no such table: airport_1`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_1 WHERE flight_1.airline_code ='AND flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = '
  ```
