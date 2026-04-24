"""One-off helper: pre-compute and cache the ground-truth dev records.

`compute_records` runs every dev SQL query against the SQLite database,
which takes ~30 seconds. Caching the result so every evaluation reuses
the same .pkl file removes that cost from each training-loop epoch.

Usage:
    python cache_gt_records.py            # caches dev_gt_records.pkl
    python cache_gt_records.py --split train   # caches train as well
"""
import os
import argparse
import pickle

from utils import compute_records


RECORDS_DIR = os.path.join(os.path.dirname(__file__), 'records')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def cache_split(split: str) -> str:
    sql_path = os.path.join(DATA_DIR, f'{split}.sql')
    out_path = os.path.join(RECORDS_DIR, f'{split}_gt_records.pkl')
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f'No GT SQL for split={split}')
    os.makedirs(RECORDS_DIR, exist_ok=True)
    with open(sql_path, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    print(f'[{split}] computing records for {len(queries)} queries...')
    records, error_msgs = compute_records(queries)
    with open(out_path, 'wb') as f:
        pickle.dump((records, error_msgs), f)
    n_err = sum(1 for m in error_msgs if m)
    print(f'[{split}] cached -> {out_path}  ({n_err} GT queries errored)')
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=['dev', 'train', 'all'], default='dev')
    args = parser.parse_args()

    if args.split == 'all':
        for s in ['dev', 'train']:
            cache_split(s)
    else:
        cache_split(args.split)


if __name__ == '__main__':
    main()
