"""Apply post-processing (paren balance) to a saved prediction file.

Re-evaluating an existing model run with a corrected SQL output costs
nothing (no GPU, no inference) and recovers the queries that errored
purely because of unbalanced parens. The cleaned predictions are
saved as a new `_pp` (post-processed) variant and logged to the
experiment registry as a derived run.

Usage:
    # Apply to a single registered run (uses its dev predictions):
    python tools/apply_postprocess.py \
        --model_type t5_ft --experiment_name t5_ft_baseline --split dev --log

    # Same but for test split (no metrics — just produce submission file):
    python tools/apply_postprocess.py \
        --model_type t5_ft --experiment_name t5_ft_baseline --split test

    # Sweep across all registry rows that have predictions:
    python tools/apply_postprocess.py --all --split dev --log
"""
import argparse
import csv
import os
import pickle
import sys
import time
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from utils import compute_metrics, save_queries_and_records  # noqa: E402
from experiment_registry import ExperimentRegistry  # noqa: E402
from tools.balance_parens import balance_parens  # noqa: E402


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')
DATA_DIR = os.path.join(ROOT, 'data')
REGISTRY_PATH = os.path.join(ROOT, 'experiments', 'registry.csv')


def _load_predictions(model_type: str, exp_name: str, split: str):
    prefix = f'{model_type}_{exp_name}'
    sql_path = os.path.join(RESULTS_DIR, f'{prefix}_{split}.sql')
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f'no predictions at {sql_path}')
    with open(sql_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def apply_to_run(model_type: str, exp_name: str, split: str,
                 log_to_registry: bool = False) -> dict:
    """Run paren-balance over a saved prediction file and re-evaluate.

    Returns a dict with the new metrics + paths. If `log_to_registry`
    is True (and we have GT for the split), creates a `_pp` registry row.
    """
    raw_sqls = _load_predictions(model_type, exp_name, split)
    n = len(raw_sqls)
    fixed = [balance_parens(s) for s in raw_sqls]
    n_changed = sum(1 for a, b in zip(raw_sqls, fixed) if a != b)

    new_exp = f'{exp_name}_pp'
    new_prefix = f'{model_type}_{new_exp}'
    new_sql_path = os.path.join(RESULTS_DIR, f'{new_prefix}_{split}.sql')
    new_rec_path = os.path.join(RECORDS_DIR, f'{new_prefix}_{split}.pkl')

    t0 = time.time()
    save_queries_and_records(fixed, new_sql_path, new_rec_path)

    out = {
        'source_run': exp_name,
        'queries': n,
        'queries_modified_by_paren_balance': n_changed,
        'sql_path': new_sql_path,
        'rec_path': new_rec_path,
    }

    if split == 'test':
        out['split'] = 'test'
        out['note'] = 'no GT, no metrics computed'
        return out

    # Dev split — compute new metrics
    gt_sql = os.path.join(DATA_DIR, f'{split}.sql')
    gt_rec = os.path.join(RECORDS_DIR, f'{split}_gt_records.pkl')
    gt_rec_arg = gt_rec if os.path.exists(gt_rec) else None
    sql_em, record_em, record_f1, err_msgs = compute_metrics(
        gt_sql, new_sql_path, gt_rec_arg, new_rec_path)
    err_rate = sum(1 for m in err_msgs if m) / max(len(err_msgs), 1)
    out.update({
        'dev_record_f1': record_f1,
        'dev_record_em': record_em,
        'dev_sql_em': sql_em,
        'dev_error_rate': err_rate,
        'eval_time_sec': time.time() - t0,
    })

    if log_to_registry:
        cfg = {
            'model_type': model_type,
            'experiment_name': new_exp,
            'source_run': exp_name,
            'derived_postprocess': 'balance_parens',
        }
        registry_results = {
            'dev_record_f1': record_f1,
            'dev_record_em': record_em,
            'dev_sql_em': sql_em,
            'dev_error_rate': err_rate,
            'duration_sec': out['eval_time_sec'],
            'best_hyperparam': 'paren-balance',
            'epochs_trained': 0,
        }
        rid = ExperimentRegistry().log_run(cfg, registry_results)
        out['registry_run_id'] = rid

    return out


def iter_registry_rows(split: str):
    if not os.path.exists(REGISTRY_PATH):
        return
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            mt, en = row.get('model_type'), row.get('experiment_name')
            if not mt or not en or en.endswith('_pp'):
                continue  # skip already post-processed rows
            prefix = f'{mt}_{en}'
            if os.path.exists(os.path.join(RESULTS_DIR, f'{prefix}_{split}.sql')):
                yield mt, en


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--model_type')
    p.add_argument('--experiment_name')
    p.add_argument('--split', default='dev', choices=['dev', 'test'])
    p.add_argument('--all', action='store_true')
    p.add_argument('--log', action='store_true',
                   help='Log new run to registry (dev splits only)')
    args = p.parse_args()

    if args.all:
        for mt, en in iter_registry_rows(args.split):
            print(f'\n--- {mt}/{en} ({args.split}) ---')
            r = apply_to_run(mt, en, args.split, log_to_registry=args.log)
            for k, v in r.items():
                if isinstance(v, float):
                    print(f'  {k}: {v:.4f}')
                else:
                    print(f'  {k}: {v}')
        return

    if not args.model_type or not args.experiment_name:
        p.error('--model_type and --experiment_name required when --all not set')
    r = apply_to_run(args.model_type, args.experiment_name, args.split,
                     log_to_registry=args.log)
    for k, v in r.items():
        if isinstance(v, float):
            print(f'  {k}: {v:.4f}')
        else:
            print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
