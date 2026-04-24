"""Re-evaluate a saved T5 checkpoint with a different decoding strategy.

Every training run keeps only one set of predictions — the one produced
by its configured `num_beams` and `max_new_tokens`. Swapping those at
inference time is essentially free (~10 min on dev, ~5 min on test) but
routinely buys a few points of Record F1. This script loads a best
checkpoint and writes a new prediction file + registry entry without
retraining.

Typical use:
    # beam=4 dev eval of iter 001
    python eval_from_checkpoint.py --exp_name t5_ft_baseline \\
        --model_type t5_ft --split dev --num_beams 4

    # emit the matching test predictions once you like the dev number
    python eval_from_checkpoint.py --exp_name t5_ft_baseline \\
        --model_type t5_ft --split test --num_beams 4
"""
import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import load_t5_data
from t5_utils import initialize_model
from eval_harness import evaluate_t5
from experiment_registry import ExperimentRegistry
from transformers import T5TokenizerFast


CHECKPOINTS_DIR = os.path.join(os.path.dirname(__file__), 'experiments', 'checkpoints')


def _load_model(exp_name: str, model_type: str):
    ckpt_path = os.path.join(CHECKPOINTS_DIR, f'{exp_name}_best.pth')
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f'No checkpoint at {ckpt_path} — did training finish and save '
            f'a "best" snapshot? Check experiments/checkpoints/.'
        )

    class _Args:
        pass
    args = _Args()
    args.finetune = model_type == 't5_ft'
    model = initialize_model(args)

    ckpt = torch.load(ckpt_path, map_location='cuda' if torch.cuda.is_available() else 'cpu')
    if isinstance(ckpt, dict) and 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'])
        print(f"Loaded {exp_name} (best, epoch={ckpt.get('epoch')}) — "
              f"training-time best_f1={ckpt.get('best_f1')}")
    else:
        model.load_state_dict(ckpt)
        print(f'Loaded {exp_name} (legacy format, state_dict only)')
    model.eval()
    return model


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--exp_name', required=True,
                   help='Name of a prior training run — must match '
                        'experiments/checkpoints/{exp_name}_best.pth')
    p.add_argument('--model_type', required=True, choices=['t5_ft', 't5_scr'])
    p.add_argument('--num_beams', type=int, default=4)
    p.add_argument('--max_new_tokens', type=int, default=256)
    p.add_argument('--split', default='dev', choices=['dev', 'test'])
    p.add_argument('--tag', default=None,
                   help='Suffix added to experiment_name for the new artefacts '
                        '(default: beam{num_beams})')
    p.add_argument('--log', action='store_true',
                   help='Record this eval as a new row in the registry '
                        '(dev splits only; test has no ground truth)')
    args = p.parse_args()

    tag = args.tag or f'beam{args.num_beams}'
    derived_name = f'{args.exp_name}_{tag}'

    model = _load_model(args.exp_name, args.model_type)

    _, dev_loader, test_loader = load_t5_data(batch_size=1, test_batch_size=8)
    loader = dev_loader if args.split == 'dev' else test_loader

    tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')
    cfg = {
        'model_type': args.model_type,
        'experiment_name': derived_name,
        'num_beams': args.num_beams,
        'max_new_tokens': args.max_new_tokens,
        'source_run': args.exp_name,
        'derived_from_checkpoint': True,
    }

    print(f'\n=== {args.split} eval — beam={args.num_beams}, '
          f'max_new={args.max_new_tokens} ===')
    result = evaluate_t5(model, loader, cfg, tokenizer=tokenizer,
                         split=args.split, save_predictions=True)

    if args.split == 'dev':
        print(f"Record F1:  {result['dev_record_f1']:.4f}")
        print(f"Record EM:  {result['dev_record_em']:.4f}")
        print(f"SQL EM:     {result['dev_sql_em']:.4f}")
        print(f"Err rate:   {result['dev_error_rate']*100:.2f}%")
    print(f"Saved:      {result['prediction_path']}")
    print(f"            {result['record_path']}")

    if args.log and args.split == 'dev':
        reg = ExperimentRegistry()
        reg_results = {
            'dev_record_f1': result['dev_record_f1'],
            'dev_record_em': result['dev_record_em'],
            'dev_sql_em': result['dev_sql_em'],
            'dev_error_rate': result['dev_error_rate'],
            'dev_loss': result['dev_loss'],
            'duration_sec': result.get('eval_time_sec'),
            'best_hyperparam': f'beam={args.num_beams}',
            'epochs_trained': 0,
        }
        rid = reg.log_run(cfg, reg_results)
        print(f'Logged as: {rid}')


if __name__ == '__main__':
    main()
