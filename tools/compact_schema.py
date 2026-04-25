"""Compact the 23 KB JSON schema into a ~2 KB DDL-style summary string.

Why: passing the raw `data/flight_database.schema` (23 KB ~ 7 K Gemma
tokens) into every prompt eats the entire 8 K context window of
CodeGemma-7B-it, triggering the runtime warning
``"the current text generation call has exceeded the model's predefined
maximum length"`` and silent prompt truncation. A compact DDL-style
representation (table → column list) keeps the same information that
matters for SQL generation while shaving ~90 % of tokens.

Resulting format:

    Tables and their columns:
    - airline(airline_code, airline_name)
    - airport(airport_code, airport_name, ...)
    - flight(flight_id, from_airport, to_airport, ...)
    ...
    Foreign-key links (table -> referenced):
    - flight.from_airport -> airport.airport_code
    - flight.to_airport -> airport.airport_code
    ...

Usage:

    from tools.compact_schema import compact_schema
    compact = compact_schema(raw_schema_text)
"""
import json
from typing import List


def compact_schema(raw_text: str, include_links: bool = True) -> str:
    """Convert the raw schema JSON text into a compact, prompt-friendly string.

    Falls back to returning the raw text unchanged if the input cannot
    be parsed as JSON (so callers don't need to special-case errors).
    """
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return raw_text

    ents = data.get('ents', {}) if isinstance(data, dict) else {}
    links = data.get('links', {}) if isinstance(data, dict) else {}
    defaults = data.get('defaults', {}) if isinstance(data, dict) else {}

    out: List[str] = []

    if ents:
        out.append('Tables and their columns:')
        for table in sorted(ents):
            cols_dict = ents[table]
            if isinstance(cols_dict, dict):
                col_names = list(cols_dict.keys())
            else:
                col_names = []
            # Put the "default" column first if present, then the rest sorted.
            default_col = None
            if isinstance(defaults.get(table), dict):
                default_col = defaults[table].get('col')
            if default_col and default_col in col_names:
                col_names.remove(default_col)
                col_names = [default_col] + sorted(col_names)
            else:
                col_names = sorted(col_names)
            out.append(f'- {table}({", ".join(col_names)})')

    if include_links and links:
        link_lines: List[str] = []
        for table in sorted(links):
            tlinks = links[table]
            if not isinstance(tlinks, dict) or not tlinks:
                continue
            for col, target in sorted(tlinks.items()):
                # target shape varies; commonly {"ent": "<table>", "col": "<col>"}
                if isinstance(target, dict):
                    tgt_table = target.get('ent') or target.get('table')
                    tgt_col = target.get('col') or target.get('column')
                    if tgt_table and tgt_col:
                        link_lines.append(
                            f'- {table}.{col} -> {tgt_table}.{tgt_col}')
                    elif tgt_table:
                        link_lines.append(f'- {table}.{col} -> {tgt_table}')
                elif isinstance(target, str):
                    link_lines.append(f'- {table}.{col} -> {target}')
        if link_lines:
            out.append('')
            out.append('Foreign-key links (table.column -> referenced):')
            out.extend(link_lines)

    return '\n'.join(out) if out else raw_text


# --------------- self-test --------------- #
if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, 'data', 'flight_database.schema'),
              'r', encoding='utf-8') as f:
        raw = f.read()
    compact = compact_schema(raw)
    print(f'raw   : {len(raw):>6,} chars')
    print(f'compact: {len(compact):>6,} chars  ({100 * len(compact) / len(raw):.1f}% of raw)')
    print('--- first 500 chars of compact ---')
    print(compact[:500])
    print('...')
    print('--- last 400 chars ---')
    print(compact[-400:])
