# Error analysis — `t5_ft` / `t5_ft_frozen_encoder_beam4` (dev)

- Total queries: **466**
- Executed cleanly: **370** (79.4%)
- Errored: **96** (20.6%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 82 | 17.6% |
| `no_such_column` | 8 | 1.7% |
| `ambiguous_column` | 5 | 1.1% |
| `syntax_error` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=82)

- query #12, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE flight_1.airline_code = 'AA' AND( flight_1.from_airport = airport_service_1.airport_code…
  ```

- query #15, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1, airport_service airport_service_1, …
  ```

### `no_such_column` (n=8)

- query #59, error: `OperationalError: no such column: flight_1.aircraft_code_code_sequence`
  ```sql
  SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1, equipment_sequence equipment_sequence_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE aircraft_1.aircraft_code = equipment_sequence_1.aircra…
  ```

- query #62, error: `OperationalError: no such column: days_1.days_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2 WHERE flight_1.airline_code = 'US' AND( flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code =…
  ```

### `ambiguous_column` (n=5)

- query #290, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport airport_1, airport airport_1 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'DALLAS' AND flight_1.to_airport = airport_1.airport_code AND airport_1.airport_code …
  ```

- query #316, error: `OperationalError: ambiguous column name: airport_1.airport_code`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport airport_1 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'MKE' AND flight_1.to_airport = airport_1.airport_code AND airport_1.airport_code = 'MKE'
  ```

### `syntax_error` (n=1)

- query #389, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1, flight_fare flight_fare_1, flight flight_1, airport_service airport_service_1, city city_1, airport_service airport_service_2, city city_2, days days_1, date_day date_day_1 WHERE fare_1.fare_id = flight_fare_1.fare_id AND flight_fa…
  ```
