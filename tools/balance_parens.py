"""Post-process generated SQL to fix unbalanced parentheses.

Error analysis on iter 001 (`t5_ft_baseline`) showed that **23.6 %** of
the model's dev predictions failed SQLite execution because of
parenthesis imbalance — the autoregressive decoder generates `(` more
often than it generates `)` (or, more rarely, vice versa). A single
post-processing pass that balances parens recovers most of those
queries with no extra inference cost.

Rules:
- If the SQL has more `(` than `)`, append the missing `)` at the end.
- If the SQL has more `)` than `(`, drop excess trailing `)` characters
  (or if interior, scrub from the end).
- Quotes are honoured: parens inside `'...'` are NOT counted.
- A trailing semicolon is preserved.

The fix is conservative — never modifies anything else. Idempotent.
"""
from typing import List


def _strip_quoted(s: str) -> str:
    """Return s with `'...'` literal contents stripped (replaced by '')
    so paren counting ignores parens inside string literals.
    """
    out: List[str] = []
    i = 0
    in_str = False
    while i < len(s):
        c = s[i]
        if c == "'":
            if not in_str:
                in_str = True
                out.append("'")
                i += 1
                continue
            # closing quote OR escaped (SQL uses '' for ')
            if i + 1 < len(s) and s[i + 1] == "'":
                # escaped quote
                i += 2
                continue
            in_str = False
            out.append("'")
            i += 1
            continue
        if not in_str:
            out.append(c)
        i += 1
    return ''.join(out)


def balance_parens(sql: str) -> str:
    """Return a copy of `sql` with parens balanced.

    Strategy:
    - Count `(` minus `)` in the string-literal-stripped version.
    - If diff > 0 (more open): append diff `)` characters before any
      trailing semicolon.
    - If diff < 0 (more close): drop |diff| `)` characters from the
      right (skipping any trailing semicolon, then walking left).
    - If diff == 0: return unchanged.
    """
    if not sql:
        return sql

    stripped = _strip_quoted(sql)
    diff = stripped.count('(') - stripped.count(')')

    if diff == 0:
        return sql

    # Detect a trailing semicolon to preserve.
    rstripped = sql.rstrip()
    has_semi = rstripped.endswith(';')
    if has_semi:
        body = rstripped[:-1].rstrip()
        tail = ';'
    else:
        body = rstripped
        tail = ''

    if diff > 0:
        return body + (')' * diff) + tail

    # diff < 0: too many close parens; remove |diff| from the right of body.
    needed = -diff
    chars = list(body)
    j = len(chars) - 1
    while j >= 0 and needed > 0:
        if chars[j] == ')':
            # only remove if it's NOT inside a string literal
            literal_check = _strip_quoted(''.join(chars[:j + 1]))
            if literal_check.endswith(')'):
                chars.pop(j)
                needed -= 1
        j -= 1
    return ''.join(chars).rstrip() + tail


def balance_parens_batch(sqls):
    return [balance_parens(s) for s in sqls]


# --------------- self-test --------------- #
if __name__ == '__main__':
    cases = [
        ('SELECT * FROM t', 'SELECT * FROM t'),
        ('SELECT * FROM t WHERE (x = 1', 'SELECT * FROM t WHERE (x = 1)'),
        ('SELECT * FROM t WHERE (x = 1 AND (y > 0',
         'SELECT * FROM t WHERE (x = 1 AND (y > 0))'),
        ('SELECT * FROM t WHERE x = 1)',  'SELECT * FROM t WHERE x = 1'),
        ('SELECT (x) FROM t;', 'SELECT (x) FROM t;'),
        ("SELECT * FROM t WHERE name = 'O''Brien' AND (x",
         "SELECT * FROM t WHERE name = 'O''Brien' AND (x)"),
        ("SELECT * FROM t WHERE city = 'NEW(YORK' AND y = 1",
         "SELECT * FROM t WHERE city = 'NEW(YORK' AND y = 1"),
    ]
    fails = 0
    for inp, want in cases:
        got = balance_parens(inp)
        ok = got == want
        if not ok:
            fails += 1
        print(('PASS' if ok else 'FAIL'), '|', repr(inp), '->', repr(got),
              '' if ok else f'  (expected {want!r})')
    print(f'\n{len(cases) - fails}/{len(cases)} cases pass')
