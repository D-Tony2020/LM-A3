# Error analysis — `gemma_1b` / `gemma1b_k0` (dev)

- Total queries: **466**
- Executed cleanly: **4** (0.9%)
- Errored: **462** (99.1%)

## Counts by category

| Category | Count | % of all |
|---|---:|---:|
| `no_such_table` | 422 | 90.6% |
| `syntax_error` | 30 | 6.4% |
| `no_such_column` | 10 | 2.1% |

## Sample failing queries per category

### `no_such_table` (n=422)

- query #0, error: `OperationalError: no such table: flights`
  ```sql
  SELECT flight_number FROM flights WHERE city = 'Denver' AND origin = 'Denver' AND destination = 'Philadelphia'
  ```

- query #1, error: `OperationalError: no such table: flights`
  ```sql
  SELECT flight FROM flights WHERE destination = 'boston' AND departure_time BETWEEN '2:00 PM' AND '5:00 PM'
  ```

### `syntax_error` (n=30)

- query #6, error: `OperationalError: near "From": syntax error`
  ```sql
  SELECT * FROM Flights WHERE From = 'Boston' AND To = 'San Francisco' AND FlightType = 'Nonstop'
  ```

- query #11, error: `OperationalError: near "From": syntax error`
  ```sql
  SELECT * FROM Flights WHERE From = 'dallas' AND To = 'boston'
  ```

### `no_such_column` (n=10)

- query #39, error: `OperationalError: no such column: cost`
  ```sql
  SELECT cost FROM flight WHERE flight_id = 'ua 201' AND flight_id = 'ua 343'
  ```

- query #124, error: `OperationalError: no such column: origin`
  ```sql
  SELECT flight.flight_number FROM flight WHERE origin = 'miami' AND destination = 'cleveland' AND flight.departure_time > '12:00'
  ```
