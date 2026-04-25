# Error analysis — `gemma_12b` / `gemma3_12b_k3_bm25_compact_schema` (dev)

- Total queries: **466**
- Executed cleanly: **370** (79.4%)
- Errored: **96** (20.6%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 68 | 14.6% |
| `no_such_column` | 20 | 4.3% |
| `other` | 4 | 0.9% |
| `incomplete_input` | 3 | 0.6% |
| `no_such_table` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=68)

- query #15, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_servic…
  ```

- query #23, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , days days_1 , date_day date_day_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_2 , date_day…
  ```

### `no_such_column` (n=20)

- query #18, error: `OperationalError: no such column: city_1.city`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , ai…
  ```

- query #28, error: `OperationalError: no such column: date_day_`
  ```sql
  SELECT DISTINCT fare_1.round_trip_cost FROM fare fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE fare_1.from_airport = airport_service_1.airport_code AND airport…
  ```

### `other` (n=4)

- query #199, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

- query #202, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

### `incomplete_input` (n=3)

- query #153, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , state state_1 , airport_service airport_service_2 , city city_2 , state state_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_…
  ```

- query #249, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE fare_1.fare_basis_…
  ```

### `no_such_table` (n=1)

- query #90, error: `OperationalError: no such table: aircraft_sequence_1`
  ```sql
  SELECT DISTINCT aircraft_1.aircraft_code FROM flight flight_1 JOIN aircraft_sequence_1 equipment_sequence_1 ON flight_1.aircraft_code_sequence = equipment_sequence_1.aircraft_code_sequence JOIN aircraft aircraft_1 ON equipment_sequence_1.aircraft_code = aircraft_1.aircraft_code J…
  ```
