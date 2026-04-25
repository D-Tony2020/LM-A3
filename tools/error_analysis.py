"""Qualitative error analysis on a generated submission.

For a given run (`{model_type}_{experiment_name}` on a `split`), this
script reads the per-query error messages stored in the .pkl file
produced by `utils.save_queries_and_records`, classifies them into a
small set of SQLite error categories, and emits a markdown table plus
representative example queries for the report.

The output is written to:
    experiments/analysis/error_categories_{model_type}_{experiment_name}.md

CLI:

    # Single run on dev
    python tools/error_analysis.py --model_type t5_ft \\
        --experiment_name t5_ft_baseline --split dev

    # Iterate over every dev row in registry.csv
    python tools/error_analysis.py --all --split dev

The script is read-only — it never modifies registry, results, or records.
"""
import argparse
import csv
import os
import pickle
import re
import sys
from collections import defaultdict, Counter
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')
ANALYSIS_DIR = os.path.join(ROOT, 'experiments', 'analysis')
REGISTRY_PATH = os.path.join(ROOT, 'experiments', 'registry.csv')


# Order matters: more-specific categories listed first.
_RULES = [
    ('query_timeout',        re.compile(r'(timed out|timeout)', re.I)),
    ('no_such_column',       re.compile(r'no such column', re.I)),
    ('no_such_table',        re.compile(r'no such table', re.I)),
    ('ambiguous_column',     re.compile(r'ambiguous column name', re.I)),
    ('aggregate_misuse',     re.compile(r'(misuse of aggregate|no such function)', re.I)),
    ('incomplete_input',     re.compile(r'incomplete input', re.I)),
    ('syntax_error',         re.compile(r'(syntax error|near "|near \')', re.I)),
]


def classify(error_msg: str, sql: str) -> Optional[str]:
    """Return a category string for an error_msg, or None for clean execution."""
    if not error_msg:
        return None

    # Structural checks first — catch issues a parser would reduce to "syntax error"
    # but the report cares about the underlying class.
    paren_diff = sql.count('(') - sql.count(')')
    if paren_diff != 0:
        return 'unbalanced_parens'

    # Apply ordered regex rules.
    for label, pattern in _RULES:
        if pattern.search(error_msg):
            return label

    return 'other'


def load_predictions(model_type: str, experiment_name: str, split: str) -> Tuple[List[str], List[str]]:
    """Load the SQL strings + per-query error messages for a single run/split."""
    prefix = f'{model_type}_{experiment_name}'
    rec_path = os.path.join(RECORDS_DIR, f'{prefix}_{split}.pkl')
    sql_path = os.path.join(RESULTS_DIR, f'{prefix}_{split}.sql')

    if not os.path.exists(rec_path):
        raise FileNotFoundError(f'records pkl missing: {rec_path}')
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f'predictions sql missing: {sql_path}')

    with open(rec_path, 'rb') as f:
        records, error_msgs = pickle.load(f)
    with open(sql_path, 'r', encoding='utf-8') as f:
        sqls = [line.strip() for line in f if line.strip()]

    return sqls, error_msgs


def analyse(model_type: str, experiment_name: str, split: str,
            samples_per_cat: int = 2) -> str:
    """Produce the per-run markdown error-category report."""
    sqls, error_msgs = load_predictions(model_type, experiment_name, split)
    n = max(len(sqls), len(error_msgs))
    if len(sqls) != len(error_msgs):
        # Pad whichever is shorter for safety; flag in the output.
        sqls = sqls + [''] * (n - len(sqls))
        error_msgs = list(error_msgs) + [''] * (n - len(error_msgs))

    grouped: dict = defaultdict(list)  # category -> [(idx, sql, msg)]
    n_clean = 0
    for i, (sql, msg) in enumerate(zip(sqls, error_msgs)):
        cat = classify(msg or '', sql)
        if cat is None:
            n_clean += 1
        else:
            grouped[cat].append((i, sql, msg))

    n_err = sum(len(v) for v in grouped.values())
    err_pct = 100.0 * n_err / n if n else 0.0

    lines: List[str] = []
    lines.append(f'# Error analysis — `{model_type}` / `{experiment_name}` ({split})')
    lines.append('')
    lines.append(f'- Total queries: **{n}**')
    lines.append(f'- Executed cleanly: **{n_clean}** ({100.0 * n_clean / n:.1f}%)')
    lines.append(f'- Errored: **{n_err}** ({err_pct:.1f}%)')
    lines.append('')

    if grouped:
        lines.append('## Counts by category')
        lines.append('')
        lines.append('| Category | Count | % of all |')
        lines.append('|---|---:|---:|')
        cats_sorted = sorted(grouped.keys(), key=lambda c: -len(grouped[c]))
        for cat in cats_sorted:
            cnt = len(grouped[cat])
            lines.append(f'| `{cat}` | {cnt} | {100.0 * cnt / n:.1f}% |')
        lines.append('')

        lines.append('## Sample failing queries per category')
        for cat in cats_sorted:
            samples = grouped[cat][:samples_per_cat]
            lines.append('')
            lines.append(f'### `{cat}` (n={len(grouped[cat])})')
            for idx, sql, msg in samples:
                lines.append('')
                lines.append(f'- query #{idx}, error: `{(msg or "").strip()[:160]}`')
                trimmed = (sql or '').strip()
                if len(trimmed) > 280:
                    trimmed = trimmed[:280] + '…'
                lines.append(f'  ```sql\n  {trimmed}\n  ```')
    else:
        lines.append('No errors found — every prediction executed cleanly.')

    lines.append('')
    return '\n'.join(lines)


def write_report(text: str, model_type: str, experiment_name: str) -> str:
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    out_path = os.path.join(
        ANALYSIS_DIR, f'error_categories_{model_type}_{experiment_name}.md'
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return out_path


def iter_registry_rows(split: str):
    if not os.path.exists(REGISTRY_PATH):
        return
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            mt, en = row.get('model_type', ''), row.get('experiment_name', '')
            if not mt or not en:
                continue
            prefix = f'{mt}_{en}'
            if os.path.exists(os.path.join(RECORDS_DIR, f'{prefix}_{split}.pkl')):
                yield mt, en


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--model_type', default=None,
                   help='e.g. t5_ft, t5_scr, gemma_1b, codegemma_7b')
    p.add_argument('--experiment_name', default=None,
                   help='matches registry.experiment_name')
    p.add_argument('--split', default='dev', choices=['dev', 'test'])
    p.add_argument('--all', action='store_true',
                   help='Iterate over every registry row that has predictions for SPLIT')
    p.add_argument('--samples_per_cat', type=int, default=2)
    args = p.parse_args()

    if args.all:
        any_done = False
        for mt, en in iter_registry_rows(args.split):
            text = analyse(mt, en, args.split, samples_per_cat=args.samples_per_cat)
            out = write_report(text, mt, en)
            print(f'  {mt}/{en} -> {out}')
            any_done = True
        if not any_done:
            print(f'no registry rows have predictions on split={args.split}')
        return

    if not args.model_type or not args.experiment_name:
        p.error('--model_type and --experiment_name are required when --all is not set')

    text = analyse(args.model_type, args.experiment_name, args.split,
                   samples_per_cat=args.samples_per_cat)
    out = write_report(text, args.model_type, args.experiment_name)
    print(f'wrote {out}')

    # Also echo the counts table to stdout for quick eyeballing.
    print()
    for line in text.splitlines():
        if line.startswith('|') or line.startswith('- '):
            print(line)


if __name__ == '__main__':
    main()
