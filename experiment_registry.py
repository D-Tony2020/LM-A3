"""
Experiment registry backed by an append-only CSV and a per-run JSON.

Tracks every training / prompting experiment with its config and metrics.
Queries by model_type (t5_ft, t5_scr, gemma_*) and surfaces the best
run per metric. Uses only the Python standard library, so it remains
compatible with the assignment's restricted dependency list.
"""
import os
import csv
import json
import hashlib
from datetime import datetime
from typing import Optional, Any, List, Dict


EXPERIMENTS_DIR = os.path.join(os.path.dirname(__file__), 'experiments')
REGISTRY_PATH = os.path.join(EXPERIMENTS_DIR, 'registry.csv')
RUNS_DIR = os.path.join(EXPERIMENTS_DIR, 'runs')
CHECKPOINTS_DIR = os.path.join(EXPERIMENTS_DIR, 'checkpoints')
ANALYSIS_DIR = os.path.join(EXPERIMENTS_DIR, 'analysis')
COLAB_OUTPUT_DIR = os.path.join(EXPERIMENTS_DIR, 'colab_output')
PROMPTING_LOGS_DIR = os.path.join(EXPERIMENTS_DIR, 'prompting_logs')


REGISTRY_COLUMNS = [
    'timestamp', 'run_id', 'model_type', 'experiment_name', 'config_hash',
    'dev_record_f1', 'dev_record_em', 'dev_sql_em', 'dev_error_rate', 'dev_loss',
    'test_record_f1', 'best_hyperparam', 'duration_sec', 'epochs_trained',
    'config_json',
]


class ExperimentRegistry:
    def __init__(self) -> None:
        for d in [EXPERIMENTS_DIR, RUNS_DIR, CHECKPOINTS_DIR, ANALYSIS_DIR,
                  COLAB_OUTPUT_DIR, PROMPTING_LOGS_DIR]:
            os.makedirs(d, exist_ok=True)

        if not os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS).writeheader()

    def _config_hash(self, config: dict) -> str:
        s = json.dumps(config, sort_keys=True, default=str)
        return hashlib.md5(s.encode()).hexdigest()[:8]

    def log_run(self, config: dict, results: dict) -> str:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        config_hash = self._config_hash(config)
        run_id = f"{config.get('experiment_name', 'run')}_{ts}"

        row = {
            'timestamp': ts,
            'run_id': run_id,
            'model_type': config.get('model_type', 'unknown'),
            'experiment_name': config.get('experiment_name', ''),
            'config_hash': config_hash,
            'dev_record_f1': results.get('dev_record_f1'),
            'dev_record_em': results.get('dev_record_em'),
            'dev_sql_em': results.get('dev_sql_em'),
            'dev_error_rate': results.get('dev_error_rate'),
            'dev_loss': results.get('dev_loss'),
            'test_record_f1': results.get('test_record_f1'),
            'best_hyperparam': results.get('best_hyperparam'),
            'duration_sec': results.get('duration_sec'),
            'epochs_trained': results.get('epochs_trained'),
            'config_json': json.dumps(config, default=str),
        }

        with open(REGISTRY_PATH, 'a', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS).writerow(row)

        run_detail = {'config': config, 'results': results, 'run_id': run_id}
        with open(os.path.join(RUNS_DIR, f'{run_id}.json'), 'w', encoding='utf-8') as f:
            json.dump(run_detail, f, indent=2, default=str)

        return run_id

    def get_all(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not os.path.exists(REGISTRY_PATH):
            return []
        with open(REGISTRY_PATH, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        if model_type:
            rows = [r for r in rows if r.get('model_type') == model_type]
        return rows

    @staticmethod
    def _to_float(v: Any) -> Optional[float]:
        if v is None or v == '':
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def get_best(self, model_type: str, metric: str = 'dev_record_f1',
                 maximize: bool = True) -> Optional[dict]:
        rows = self.get_all(model_type)
        rows = [r for r in rows if self._to_float(r.get(metric)) is not None]
        if not rows:
            return None
        key = lambda r: self._to_float(r[metric])
        return max(rows, key=key) if maximize else min(rows, key=key)

    def get_frontier(self, metric: str = 'dev_record_f1',
                     maximize: bool = True) -> Dict[str, Dict[str, Any]]:
        rows = self.get_all()
        if not rows:
            return {}
        types = sorted({r.get('model_type', 'unknown') for r in rows})
        frontier: Dict[str, Dict[str, Any]] = {}
        for mt in types:
            best = self.get_best(mt, metric, maximize)
            if best:
                frontier[mt] = {
                    'dev_record_f1': self._to_float(best.get('dev_record_f1')),
                    'dev_record_em': self._to_float(best.get('dev_record_em')),
                    'dev_sql_em': self._to_float(best.get('dev_sql_em')),
                    'best_hyperparam': best.get('best_hyperparam'),
                    'experiment_name': best.get('experiment_name'),
                }
        return frontier

    def count_runs(self, model_type: Optional[str] = None) -> int:
        return len(self.get_all(model_type))

    def dashboard(self) -> str:
        rows = self.get_all()
        if not rows:
            return 'No experiments recorded yet.'

        lines = [f'Experiment registry: {len(rows)} total runs']
        types = sorted({r.get('model_type', 'unknown') for r in rows})
        for mt in types:
            mt_rows = [
                r for r in rows
                if r.get('model_type') == mt
                and self._to_float(r.get('dev_record_f1')) is not None
            ]
            if not mt_rows:
                total = sum(1 for r in rows if r.get('model_type') == mt)
                lines.append(f'\n{mt}: {total} runs, no F1 data yet')
                continue

            mt_rows.sort(key=lambda r: self._to_float(r['dev_record_f1']), reverse=True)
            best = mt_rows[0]
            f1 = self._to_float(best['dev_record_f1'])
            em = self._to_float(best.get('dev_record_em')) or 0.0
            sql_em = self._to_float(best.get('dev_sql_em')) or 0.0
            lines.append(f'\n{mt}: {len(mt_rows)} runs with F1 data')
            lines.append(
                f'  best: F1={f1:.4f}  RecordEM={em:.4f}  SQL_EM={sql_em:.4f}  '
                f'name={best["experiment_name"]}'
            )
            for r in mt_rows[:5]:
                f1_r = self._to_float(r['dev_record_f1'])
                lines.append(f'    {r["experiment_name"]:35s}  F1={f1_r:.4f}')

        return '\n'.join(lines)


if __name__ == '__main__':
    reg = ExperimentRegistry()
    print(reg.dashboard())
