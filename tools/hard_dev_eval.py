"""Hard-dev evaluation: F1 on the dev subset that is *distributionally far*
from train.

Why this exists
---------------
Cross-department analysis (2026-04-25) found that 35.2% of dev queries have a
near-duplicate (Jaccard >= 0.8) in train.nl, vs only 11.1% of test queries.
The champion run codegemma7b_k3_bm25_schema_pp scores dev F1 = 0.697 overall
but stratified F1 ranges from 0.82 (Jaccard=1) down to 0.51 (Jaccard 0.2-0.4).
Plain dev F1 therefore *systematically over-estimates* test F1 because
BM25 + ICL trivially solves the high-similarity tail.

This tool re-evaluates a saved run on the *Jaccard<threshold* subset of dev,
giving a tougher, more test-aligned signal for model selection and
qualitative limitation reporting.

Outputs
-------
- A per-run line printed to stdout with: n_hard, hard_F1, hard_EM, hard_err
- (Optional, with --write-md) a markdown table at
  experiments/analysis/hard_dev_summary.md aggregating every registry row
  that has dev predictions on disk.

CLI
---
    # Single run
    python tools/hard_dev_eval.py --model_type codegemma_7b \\
        --experiment_name codegemma7b_k3_bm25_schema_pp

    # Tighter threshold (default 0.8, smaller -> harder subset)
    python tools/hard_dev_eval.py --threshold 0.6 --all

    # Aggregate over the registry and write the markdown table
    python tools/hard_dev_eval.py --all --write-md
"""
from __future__ import annotations

import argparse
import csv
import os
import pickle
import re
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT, 'data')
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')
ANALYSIS_DIR = os.path.join(ROOT, 'experiments', 'analysis')
REGISTRY_PATH = os.path.join(ROOT, 'experiments', 'registry.csv')
GT_REC_PATH = os.path.join(RECORDS_DIR, 'dev_gt_records.pkl')


def _tokenize(s: str) -> List[str]:
    return re.findall(r'\w+', s.lower())


def compute_jaccard_top1(dev_nl: List[str],
                          train_nl: List[str]) -> List[float]:
    """For each dev query, return the max Jaccard similarity over train.

    O(N * M) but tractable: 466 * 4225 = ~2M cheap set ops.
    """
    train_sets = [set(_tokenize(t)) for t in train_nl]
    out = []
    for q in dev_nl:
        q_set = set(_tokenize(q))
        best = 0.0
        for d_set in train_sets:
            denom = len(q_set | d_set)
            if denom == 0:
                continue
            j = len(q_set & d_set) / denom
            if j > best:
                best = j
        out.append(best)
    return out


# Cache the similarity vector so --all over many rows isn't N*M*K
_SIM_CACHE: Optional[List[float]] = None


def _get_dev_train_similarity() -> List[float]:
    global _SIM_CACHE
    if _SIM_CACHE is None:
        with open(os.path.join(DATA_DIR, 'train.nl'), encoding='utf-8') as f:
            train_nl = [line.strip() for line in f]
        with open(os.path.join(DATA_DIR, 'dev.nl'), encoding='utf-8') as f:
            dev_nl = [line.strip() for line in f]
        _SIM_CACHE = compute_jaccard_top1(dev_nl, train_nl)
    return _SIM_CACHE


def _f1_for_pair(gt: list, pred: list) -> float:
    g, p = set(gt), set(pred)
    if len(p) == 0:
        precision = 1.0
    else:
        precision = len([r for r in p if r in g]) / len(p)
    if len(g) == 0:
        recall = 1.0
    else:
        recall = len([r for r in g if r in p]) / len(g)
    return 2 * precision * recall / (precision + recall + 1e-8)


def evaluate_hard(model_type: str, experiment_name: str,
                  threshold: float = 0.8) -> dict:
    """Compute (hard_F1, hard_EM, hard_err, n_hard) on the dev subset
    where Jaccard top-1 with train < threshold.

    Returns also (overall_F1, overall_EM, overall_err) for context.
    """
    prefix = f'{model_type}_{experiment_name}'
    pred_path = os.path.join(RECORDS_DIR, f'{prefix}_dev.pkl')
    if not os.path.exists(pred_path):
        raise FileNotFoundError(f'no predictions at {pred_path}')
    if not os.path.exists(GT_REC_PATH):
        raise FileNotFoundError(
            f'no GT records cache at {GT_REC_PATH} — '
            f'run cache_gt_records.py --split dev first')

    with open(pred_path, 'rb') as f:
        pred_recs, pred_errs = pickle.load(f)
    with open(GT_REC_PATH, 'rb') as f:
        gt_recs, _ = pickle.load(f)

    sim = _get_dev_train_similarity()
    if not (len(sim) == len(pred_recs) == len(gt_recs)):
        raise ValueError(
            f'length mismatch: sim={len(sim)} '
            f'pred={len(pred_recs)} gt={len(gt_recs)}')

    hard_idx = [i for i, s in enumerate(sim) if s < threshold]
    easy_idx = [i for i, s in enumerate(sim) if s >= threshold]

    def _agg(idx):
        if not idx:
            return {'n': 0, 'f1': 0.0, 'em': 0.0, 'err': 0.0}
        f1s = [_f1_for_pair(gt_recs[i], pred_recs[i]) for i in idx]
        ems = [1 if set(gt_recs[i]) == set(pred_recs[i]) else 0 for i in idx]
        errs = [1 if pred_errs[i] else 0 for i in idx]
        return {
            'n': len(idx),
            'f1': sum(f1s) / len(idx),
            'em': sum(ems) / len(idx),
            'err': sum(errs) / len(idx),
        }

    return {
        'model_type': model_type,
        'experiment_name': experiment_name,
        'threshold': threshold,
        'overall': _agg(list(range(len(sim)))),
        'hard': _agg(hard_idx),
        'easy': _agg(easy_idx),
    }


def iter_registry_rows():
    """Yield (model_type, experiment_name) for every registry row that
    has a dev .pkl on disk.
    """
    seen = set()
    if not os.path.exists(REGISTRY_PATH):
        return
    with open(REGISTRY_PATH, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            mt, en = row.get('model_type'), row.get('experiment_name')
            if not mt or not en:
                continue
            key = (mt, en)
            if key in seen:
                continue
            prefix = f'{mt}_{en}'
            if os.path.exists(os.path.join(RECORDS_DIR, f'{prefix}_dev.pkl')):
                seen.add(key)
                yield key


def write_markdown(results: List[dict], out_path: str,
                   threshold: float) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sim = _get_dev_train_similarity()
    n_hard = sum(1 for s in sim if s < threshold)
    n_easy = len(sim) - n_hard

    lines = [
        f'# Hard-dev F1 (Jaccard < {threshold:.2f} with train.nl)',
        '',
        f'- dev split size: {len(sim)}',
        f'- hard subset (low train similarity): {n_hard} '
        f'({100 * n_hard / len(sim):.1f}%)',
        f'- easy subset (high train similarity): {n_easy} '
        f'({100 * n_easy / len(sim):.1f}%)',
        '',
        ('Hard-dev F1 is a more test-aligned signal: only 11.1% of *test* '
         f'queries have Jaccard >= {threshold:.2f} with train, vs '
         f'{100 * n_easy / len(sim):.1f}% of dev. Use hard-dev F1 when '
         'choosing among prompting/finetuning configurations.'),
        '',
        '| run | overall F1 | hard F1 | easy F1 | hard\u2212overall \u0394 |',
        '|---|---:|---:|---:|---:|',
    ]

    sortable = sorted(
        results,
        key=lambda r: r['hard']['f1'],
        reverse=True,
    )
    for r in sortable:
        name = f'{r["model_type"]}/{r["experiment_name"]}'
        lines.append(
            f'| `{name}` | {r["overall"]["f1"]:.4f} '
            f'| **{r["hard"]["f1"]:.4f}** '
            f'| {r["easy"]["f1"]:.4f} '
            f'| {r["hard"]["f1"] - r["overall"]["f1"]:+.4f} |'
        )

    lines.append('')
    lines.append(
        '> A large negative \u0394 means the run benefits disproportionately '
        'from BM25 retrieval finding near-duplicates and is therefore at '
        'risk of over-estimating test F1.'
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model_type')
    p.add_argument('--experiment_name')
    p.add_argument('--threshold', type=float, default=0.8,
                   help='Jaccard threshold; queries with top-1 train '
                        'similarity below this are the "hard" subset')
    p.add_argument('--all', action='store_true')
    p.add_argument('--write-md', action='store_true',
                   help='Write experiments/analysis/hard_dev_summary.md')
    args = p.parse_args()

    if args.all:
        results = []
        for mt, en in iter_registry_rows():
            try:
                r = evaluate_hard(mt, en, threshold=args.threshold)
            except Exception as exc:
                print(f'[skip] {mt}/{en}: {exc}')
                continue
            results.append(r)
            print(
                f'{mt}/{en:42s} '
                f'overall={r["overall"]["f1"]:.4f}  '
                f'hard={r["hard"]["f1"]:.4f} (n={r["hard"]["n"]})  '
                f'easy={r["easy"]["f1"]:.4f} (n={r["easy"]["n"]})  '
                f'\u0394={r["hard"]["f1"] - r["overall"]["f1"]:+.4f}'
            )
        if args.write_md and results:
            out = os.path.join(ANALYSIS_DIR, 'hard_dev_summary.md')
            write_markdown(results, out, args.threshold)
            print(f'\nwrote {out}')
        return

    if not args.model_type or not args.experiment_name:
        p.error('--model_type and --experiment_name required when --all not set')

    r = evaluate_hard(args.model_type, args.experiment_name,
                      threshold=args.threshold)
    print(f'run: {r["model_type"]}/{r["experiment_name"]}')
    print(f'threshold (Jaccard top-1 with train): < {r["threshold"]:.2f}')
    print(f'overall: n={r["overall"]["n"]:3d}  '
          f'F1={r["overall"]["f1"]:.4f}  '
          f'EM={r["overall"]["em"]:.4f}  '
          f'err={r["overall"]["err"]:.4f}')
    print(f'hard:    n={r["hard"]["n"]:3d}  '
          f'F1={r["hard"]["f1"]:.4f}  '
          f'EM={r["hard"]["em"]:.4f}  '
          f'err={r["hard"]["err"]:.4f}')
    print(f'easy:    n={r["easy"]["n"]:3d}  '
          f'F1={r["easy"]["f1"]:.4f}  '
          f'EM={r["easy"]["em"]:.4f}  '
          f'err={r["easy"]["err"]:.4f}')
    print(f'hard - overall \u0394 = {r["hard"]["f1"] - r["overall"]["f1"]:+.4f}')


if __name__ == '__main__':
    main()
