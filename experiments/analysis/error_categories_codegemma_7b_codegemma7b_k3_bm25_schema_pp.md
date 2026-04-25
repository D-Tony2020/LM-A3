# Error analysis — `codegemma_7b` / `codegemma7b_k3_bm25_schema_pp` (dev)

- Total queries: **466**
- Executed cleanly: **385** (82.6%)
- Errored: **81** (17.4%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_column` | 47 | 10.1% |
| `syntax_error` | 12 | 2.6% |
| `ambiguous_column` | 9 | 1.9% |
| `other` | 6 | 1.3% |
| `no_such_table` | 4 | 0.9% |
| `incomplete_input` | 3 | 0.6% |

## Sample failing queries per category

### `no_such_column` (n=47)

- query #28, error: `OperationalError: no such column: flight.fare_id`
  ```sql
  SELECT fare.round_trip_cost FROM flight flight , fare , airline WHERE flight.flight_id = '415' AND flight.fare_id = fare.fare_id AND flight.airline_code = airline.airline_code AND airline.airline_name = 'united airlines' AND ( ( flight.from_airport = (SELECT airport_code FROM air…
  ```

- query #40, error: `OperationalError: no such column: flight_1.round_trip_required`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , days days_1 , date_day date_day_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

### `syntax_error` (n=12)

- query #96, error: `OperationalError: near "flight_1": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight flight_1 , flight_fare flight_fare_1 , fare fare_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.flight_id = flight_fare_1.flight_id AND flight_fare_1.fare_i…
  ```

- query #156, error: `OperationalError: near ")": syntax error`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE fare_1.fare_basis_code = fare_basis_1.fare_basis_code …
  ```

### `ambiguous_column` (n=9)

- query #82, error: `OperationalError: ambiguous column name: city_code`
  ```sql
  SELECT DISTINCT flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 WHERE from_airport = airport_code AND to_airport = airport_code AND city_code = city_code AND city_name = 'ATLANTA' AND day_name = 'THURSDAY' AND month_number = 9 AND day_number = 5
  ```

- query #152, error: `OperationalError: ambiguous column name: fare_id`
  ```sql
  SELECT DISTINCT fare_id FROM fare f , flight_fare ff , flight flt , airport a , city c , airport_service as ap , city c2 WHERE f.round_trip_required = 'NO' AND f.one_direction_cost = ( SELECT MIN( f.one_direction_cost ) FROM fare f , flight_fare ff , flight flt , airport a , city…
  ```

### `other` (n=6)

- query #15, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.departure_time =( SELECT MIN( flight_1.departure_time ) FROM flight flight_1 , airport_service airport_service_1 , cit…
  ```

- query #18, error: `OperationalError: interrupted`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 WHERE fare_1.round_trip_cost =( SELECT MIN( fare_1.round_trip_cost ) FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , ai…
  ```

### `no_such_table` (n=4)

- query #30, error: `OperationalError: no such table: days_2`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , days_2 , days_3 WHERE flight_1.departure_time BETWEEN 0 AND 800 AND( flight_1.from_airport = airport_service…
  ```

- query #234, error: `OperationalError: no such table: fare_1`
  ```sql
  SELECT DISTINCT flight_id FROM flight flight_1 , flight_fare flight_fare_1 , fare fare_1 WHERE flight_1.flight_id = flight_fare_1.flight_id AND flight_fare_1.fare_id = fare_1.fare_id AND fare_1.one_direction_cost =( SELECT MAX( fare_1.one_direction_cost ) FROM fare_1 , flight_far…
  ```

### `incomplete_input` (n=3)

- query #39, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.round_trip_cost , fare_2.round_trip_cost FROM fare fare_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , fare fare_2 , flight_fare flight_fare_2 , flight fl…
  ```

- query #106, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT fare_1.fare_id FROM fare fare_1 , fare_basis fare_basis_1 , flight_fare flight_fare_1 , flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE fare_1.round_trip_cost IS NOT NULL AND fare_1.fare_bas…
  ```
