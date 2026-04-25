# Error analysis — `codegemma_7b` / `codegemma7b_k3_bm25_schema` (dev)

- Total queries: **466**
- Executed cleanly: **290** (62.2%)
- Errored: **176** (37.8%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `unbalanced_parens` | 142 | 30.5% |
| `no_such_column` | 23 | 4.9% |
| `ambiguous_column` | 5 | 1.1% |
| `incomplete_input` | 3 | 0.6% |
| `query_timeout` | 1 | 0.2% |
| `no_such_table` | 1 | 0.2% |
| `syntax_error` | 1 | 0.2% |

## Sample failing queries per category

### `unbalanced_parens` (n=142)

- query #0, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

- query #2, error: `OperationalError: incomplete input`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , date_day date_day_1 WHERE flight_1.arrival_time < 900 AND( flight_1.to_airport = airport_service_1.airport_c…
  ```

### `no_such_column` (n=23)

- query #40, error: `OperationalError: no such column: flight_1.round_trip_required`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , days days_1 , date_day date_day_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 WHERE flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_…
  ```

- query #52, error: `OperationalError: no such column: flight.fare_id`
  ```sql
  SELECT fare.round_trip_cost FROM flight flight, fare, airline WHERE flight.flight_id = '19' AND flight.airline_code = 'AA' AND flight.from_airport = 'JFK' AND flight.to_airport = 'LAX' AND flight.fare_id = fare.fare_id
  ```

### `ambiguous_column` (n=5)

- query #82, error: `OperationalError: ambiguous column name: city_code`
  ```sql
  SELECT DISTINCT flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 WHERE from_airport = airport_code AND to_airport = airport_code AND city_code = city_code AND city_name = 'ATLANTA' AND day_name = 'THURSDAY' AND month_number = 9 AND day_number = 5
  ```

- query #247, error: `OperationalError: ambiguous column name: fare_id`
  ```sql
  SELECT DISTINCT fare_id FROM fare, flight_fare, flight, airport, days, date_day WHERE from_airport = 'OAKLAND' AND to_airport = 'DALLAS' AND round_trip_required = 'NO' AND flight_id = flight_fare.flight_id AND flight_fare.date_day = date_day.day_number AND date_day.day_name = 'De…
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

### `query_timeout` (n=1)

- query #23, error: `Query timed out`
  ```sql
  SELECT DISTINCT flight_id FROM flight flight , airport_service , city , days , date_day , fare
  ```

### `no_such_table` (n=1)

- query #30, error: `OperationalError: no such table: days_2`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , airport_service airport_service_1 , city city_1 , airport_service airport_service_2 , city city_2 , days days_1 , days_2 , days_3 WHERE flight_1.departure_time BETWEEN 0 AND 800 AND( flight_1.from_airport = airport_service…
  ```

### `syntax_error` (n=1)

- query #352, error: `OperationalError: near "city_1": syntax error`
  ```sql
  SELECT DISTINCT flight_1.flight_id FROM flight flight_1 , flight_fare flight_fare_1 , airport_service airport_service_1 , city city city_1 , airport_service airport_service_2 , city city_2 , days days days_1 , date_day date_day_1 , fare_basis fare_basis_1 , days days days_2 , dat…
  ```
