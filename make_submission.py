"""Pick best dev-F1 run per track and copy to the canonical submission paths.

After running a batch of experiments, this script reads
`experiments/registry.csv`, finds the best `dev_record_f1` per
`model_type`, and copies that run's prediction files into the names the
leaderboard expects:

    results/t5_ft_test.sql      records/t5_ft_test.pkl
    results/t5_scr_test.sql     records/t5_scr_test.pkl
    results/test_test.sql       records/test_test.pkl   (LLM track)

The LLM track collapses every gemma_* / codegemma_* model_type onto the
single `test_test` filename — the assignment only allows one LLM
submission regardless of how many variants you tried.

Usage:
    python make_submission.py            # for all three tracks
    python make_submission.py --tracks t5_ft,gemma   # subset
    python make_submission.py --dry-run  # show what would happen
"""
import argparse
import os
import shutil
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiment_registry import ExperimentRegistry


ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')


# Mapping: leaderboard target prefix -> the model_type prefixes that feed it.
TARGETS: Dict[str, List[str]] = {
    't5_ft':  ['t5_ft'],     # T5 finetune track
    't5_scr': ['t5_scr'],    # T5 from-scratch track
    'test':   ['gemma_', 'codegemma_'],  # any LLM variant -> test_test
}


def _candidates_for(prefix_list: List[str], registry) -> List[dict]:
    rows = registry.get_all()
    out = []
    for r in rows:
        mt = r.get('model_type', '')
        for p in prefix_list:
            if mt.startswith(p) or mt == p.rstrip('_'):
                out.append(r)
                break
    return out


def _pick_best(rows: List[dict]) -> Optional[dict]:
    rows = [r for r in rows if ExperimentRegistry._to_float(r.get('dev_record_f1')) is not None]
    if not rows:
        return None
    return max(rows, key=lambda r: ExperimentRegistry._to_float(r['dev_record_f1']))


def _source_paths(row: dict) -> tuple:
    """Reconstruct the prediction file paths used by `evaluate_t5` and
    `evaluate_prompting`. Both use `{model_type}_{experiment_name}_test.{sql,pkl}`.
    """
    mt = row['model_type']
    exp = row['experiment_name']
    prefix = f'{mt}_{exp}'
    return (
        os.path.join(RESULTS_DIR, f'{prefix}_test.sql'),
        os.path.join(RECORDS_DIR, f'{prefix}_test.pkl'),
    )


def _target_paths(target_prefix: str) -> tuple:
    return (
        os.path.join(RESULTS_DIR, f'{target_prefix}_test.sql'),
        os.path.join(RECORDS_DIR, f'{target_prefix}_test.pkl'),
    )


def make_submission(target_prefix: str, model_type_prefixes: List[str],
                    registry, dry_run: bool = False) -> bool:
    rows = _candidates_for(model_type_prefixes, registry)
    if not rows:
        print(f'  [{target_prefix}] no runs found for prefixes {model_type_prefixes}')
        return False
    best = _pick_best(rows)
    if best is None:
        print(f'  [{target_prefix}] {len(rows)} runs but none have dev_record_f1')
        return False

    src_sql, src_rec = _source_paths(best)
    tgt_sql, tgt_rec = _target_paths(target_prefix)

    f1 = ExperimentRegistry._to_float(best['dev_record_f1'])
    print(f"  [{target_prefix}] best run: {best['experiment_name']} "
          f"(F1={f1:.4f}, model_type={best['model_type']})")

    if not os.path.exists(src_sql):
        print(f'    !! source missing: {src_sql}')
        return False
    if not os.path.exists(src_rec):
        print(f'    !! source missing: {src_rec}')
        return False

    print(f'    source: {os.path.relpath(src_sql, ROOT)}')
    print(f'    target: {os.path.relpath(tgt_sql, ROOT)}')

    if dry_run:
        print('    (dry-run, no files copied)')
        return True

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(RECORDS_DIR, exist_ok=True)
    shutil.copyfile(src_sql, tgt_sql)
    shutil.copyfile(src_rec, tgt_rec)
    print('    copied OK')
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tracks', default='t5_ft,t5_scr,test',
                        help='Comma-separated subset of {t5_ft, t5_scr, test}')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    requested = [t.strip() for t in args.tracks.split(',') if t.strip()]
    invalid = [t for t in requested if t not in TARGETS]
    if invalid:
        print(f'unknown tracks: {invalid}', file=sys.stderr)
        sys.exit(1)

    registry = ExperimentRegistry()
    print(f'== make_submission (tracks={requested}, dry_run={args.dry_run}) ==')
    success = []
    for t in requested:
        if make_submission(t, TARGETS[t], registry, dry_run=args.dry_run):
            success.append(t)
    print(f'\nDone. {len(success)}/{len(requested)} submissions ready: {success}')


if __name__ == '__main__':
    main()
