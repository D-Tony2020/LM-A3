# Error analysis — `gemma_1b` / `gemma1b_k1_random` (dev)

- Total queries: **466**
- Executed cleanly: **158** (33.9%)
- Errored: **308** (66.1%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_table` | 122 | 26.2% |
| `no_such_column` | 94 | 20.2% |
| `unbalanced_parens` | 69 | 14.8% |
| `syntax_error` | 21 | 4.5% |
| `incomplete_input` | 1 | 0.2% |
| `aggregate_misuse` | 1 | 0.2% |

## Sample failing queries per category

### `no_such_table` (n=122)

- query #2, error: `OperationalError: no such table: arrival`
  ```sql
  SELECT DISTINCT arrival_date FROM arrival WHERE airport = 'BALTIMORE' AND arrival_time < '09:00'
  ```

- query #7, error: `OperationalError: no such table: flight_schedule`
  ```sql
  SELECT DISTINCT distance FROM flight_schedule WHERE destination = 'atlanta' AND origin = 'denver'
  ```

### `no_such_column` (n=94)

- query #4, error: `OperationalError: no such column: equipment_sequence_1.from_airport`
  ```sql
  SELECT DISTINCT flight_1.from_airport, flight_1.to_airport FROM flight flight_1, equipment_sequence equipment_sequence_1, flight flight_2 , airport_service airport_service_1, city city_1 , airport_service airport_service_2, city city_2 WHERE flight_1.from_airport = equipment_sequ…
  ```

- query #6, error: `OperationalError: no such column: flight.origin`
  ```sql
  SELECT DISTINCT flight.flight_number FROM flight WHERE flight.origin = 'Boston' AND flight.destination = 'San Francisco' AND flight.status = 'Nonstop'
  ```

### `unbalanced_parens` (n=69)

- query #15, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.departure_time BETWEEN 0 AND 800 AND( flight_1.airline_code = 'TW' AND( flight_…
  ```

- query #20, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time =(SELECT MAX( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_service…
  ```

### `syntax_error` (n=21)

- query #45, error: `OperationalError: near "FROM": syntax error`
  ```sql
  SELECT FROM denver TO BALTIMORE
  ```

- query #51, error: `OperationalError: near "FROM": syntax error`
  ```sql
  SELECT DISTINCT flight_id FROM flights FROM san francisco TO pittsburgh
  ```

### `incomplete_input` (n=1)

- query #196, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.time_departure >= '23:00' AND airport_service_1.city_code = 'PIT' AND city_1.city_name = 'PITTburgh' AND airport_…
  ```

### `aggregate_misuse` (n=1)

- query #372, error: `OperationalError: no such function: ST_GeomFromText`
  ```sql
  SELECT ST_Distance(ST_GeomFromText('POINT(37.7749 122.4194)'), ST_GeomFromText('POINT(37.7749 122.4194)'))
  ```
