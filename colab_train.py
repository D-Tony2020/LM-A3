"""
A4 experiment orchestrator. Drives T5 training (finetune / from-scratch)
and Gemma prompting from a single command-line interface. Usable both
locally and on Colab.

Examples
--------
    # Milestone run (T5 finetune, target dev F1 >= 0.3)
    python colab_train.py --task t5 --config t5_ft_baseline

    # Prompting with Gemma-1B, k=3, BM25 example selection
    python colab_train.py --task prompting --config gemma1b_k3_bm25

    # Registry dashboard
    python colab_train.py --task dashboard

Colab usage
-----------
    from google.colab import drive
    drive.mount('/content/drive')
    %cd /content/drive/MyDrive/<path_to_repo>
    !python colab_train.py --task t5 --config t5_ft_long
"""
import os
import sys
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiment_registry import ExperimentRegistry


T5_CONFIGS = {
    # Milestone-targeted finetune baseline. Sized for a 4 GB local GPU:
    # micro-batch 4 with grad accumulation 4 -> effective bs 16, plus
    # gradient checkpointing to halve activation memory. AMP is disabled
    # here because bf16 triggered CUBLAS errors on this specific card +
    # torch build; fp32 is stable and the run still finishes in ~1 hour.
    't5_ft_baseline': {
        'model_type': 't5_ft', 'finetune': True,
        'lr': 1e-4, 'weight_decay': 0.01,
        'max_epochs': 10, 'patience': 3, 'warmup_steps': 500,
        'lr_schedule': 'cosine', 'grad_clip': 1.0,
        'grad_accumulation_steps': 4, 'use_amp': False,
        'gradient_checkpointing': True,
        'batch_size': 4, 'test_batch_size': 8,
        'max_new_tokens': 256, 'num_beams': 1,
        'freeze_encoder': False,
        'experiment_name': 't5_ft_baseline',
    },

    # Longer finetune with higher peak LR. Local-GPU safe: bs=2, ga=8 to
    # keep the same effective batch (16) as the baseline but halve peak
    # activation memory — bs=4 tripped OOM on an outlier-long sequence at
    # batch 21 on the RTX 3050 Ti with grad_ckpt + fp32. bs=2 leaves a
    # comfortable margin. Takes ~5 h on this GPU.
    't5_ft_long': {
        'model_type': 't5_ft', 'finetune': True,
        'lr': 3e-4, 'weight_decay': 0.01,
        'max_epochs': 15, 'patience': 5, 'warmup_steps': 1000,
        'lr_schedule': 'cosine', 'grad_clip': 1.0,
        'grad_accumulation_steps': 8, 'use_amp': False,
        'gradient_checkpointing': True,
        'batch_size': 2, 'test_batch_size': 8,
        'max_new_tokens': 256, 'num_beams': 1,
        'freeze_encoder': False,
        'experiment_name': 't5_ft_long',
    },

    # Finetune with frozen encoder. Ablation target for the report.
    't5_ft_frozen_encoder': {
        'model_type': 't5_ft', 'finetune': True,
        'lr': 1e-3, 'weight_decay': 0.01,
        'max_epochs': 15, 'patience': 4, 'warmup_steps': 500,
        'lr_schedule': 'cosine', 'grad_clip': 1.0,
        'grad_accumulation_steps': 2, 'use_amp': True,
        'batch_size': 8, 'test_batch_size': 16,
        'max_new_tokens': 256, 'num_beams': 1,
        'freeze_encoder': True,
        'experiment_name': 't5_ft_frozen_encoder',
    },

    # From-scratch baseline. Smaller LR, longer warmup, more epochs than
    # finetuning because the weights start random. Local-GPU sized.
    't5_scr_baseline': {
        'model_type': 't5_scr', 'finetune': False,
        'lr': 5e-4, 'weight_decay': 0.01,
        'max_epochs': 30, 'patience': 5, 'warmup_steps': 2000,
        'lr_schedule': 'cosine', 'grad_clip': 1.0,
        'grad_accumulation_steps': 4, 'use_amp': True,
        'batch_size': 8, 'test_batch_size': 16,
        'max_new_tokens': 256, 'num_beams': 1,
        'freeze_encoder': False,
        'experiment_name': 't5_scr_baseline',
    },

    # From-scratch long run for pushing the leaderboard. Designed for Colab.
    't5_scr_long': {
        'model_type': 't5_scr', 'finetune': False,
        'lr': 7e-4, 'weight_decay': 0.01,
        'max_epochs': 60, 'patience': 8, 'warmup_steps': 4000,
        'lr_schedule': 'cosine', 'grad_clip': 1.0,
        'grad_accumulation_steps': 2, 'use_amp': True,
        'batch_size': 64, 'test_batch_size': 64,
        'max_new_tokens': 256, 'num_beams': 4,
        'freeze_encoder': False,
        'experiment_name': 't5_scr_long',
    },
}


PROMPT_CONFIGS = {
    # Zero-shot Gemma-1B, no schema. Establishes the absolute floor.
    'gemma1b_k0': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 0, 'example_selection': 'random', 'include_schema': False,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k0',
    },
    # Zero-shot Gemma-1B with schema.
    'gemma1b_k0_schema': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 0, 'example_selection': 'random', 'include_schema': True,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k0_schema',
    },
    # One-shot, random example.
    'gemma1b_k1_random': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 1, 'example_selection': 'random', 'include_schema': False,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k1_random',
    },
    # Three-shot, random examples.
    'gemma1b_k3_random': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 3, 'example_selection': 'random', 'include_schema': False,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k3_random',
    },
    # Three-shot, BM25 nearest neighbours. The strategy expected to win
    # among 1B configs.
    'gemma1b_k3_bm25': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 3, 'example_selection': 'bm25', 'include_schema': False,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k3_bm25',
    },
    # Three-shot BM25 with schema. Combines both wins.
    'gemma1b_k3_bm25_schema': {
        'model_type': 'gemma_1b', 'model_name': 'gemma-1b',
        'k': 3, 'example_selection': 'bm25', 'include_schema': True,
        'quantization': False, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma1b_k3_bm25_schema',
    },
    # Same as k3_bm25_schema but using a larger Gemma for the final push.
    'gemma27b_k3_bm25_schema_q4': {
        'model_type': 'gemma_27b', 'model_name': 'gemma-27b',
        'k': 3, 'example_selection': 'bm25', 'include_schema': True,
        'quantization': True, 'max_new_tokens': 256, 'seed': 42,
        'experiment_name': 'gemma27b_k3_bm25_schema_q4',
    },
}


def _print_device_info() -> None:
    if torch.cuda.is_available():
        print(f'  device: {torch.cuda.get_device_name(0)}')
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f'  vram:   {vram:.1f} GB')
    else:
        print('  device: CPU')


def _config_to_args(cfg: dict):
    """Project the config dict onto the attribute interface that t5_utils expects."""
    class _Args:
        pass
    args = _Args()
    for k, v in cfg.items():
        setattr(args, k, v)
    args.finetune = cfg['finetune']
    args.learning_rate = cfg['lr']
    args.weight_decay = cfg['weight_decay']
    args.optimizer_type = 'AdamW'
    args.scheduler_type = 'none'
    args.max_n_epochs = cfg['max_epochs']
    args.num_warmup_epochs = 0
    return args


def run_t5(config_name: str) -> None:
    if config_name not in T5_CONFIGS:
        print(f"Unknown T5 config '{config_name}'. "
              f"Available: {list(T5_CONFIGS.keys())}", file=sys.stderr)
        sys.exit(1)

    cfg = T5_CONFIGS[config_name].copy()
    cfg['colab'] = bool(os.environ.get('COLAB_GPU'))

    print(f"== T5 experiment: {cfg['experiment_name']} ==")
    _print_device_info()
    print(f"  model_type: {cfg['model_type']}")
    print(f"  budget:     {cfg['max_epochs']} epochs, "
          f"bs={cfg['batch_size']}, lr={cfg['lr']}, amp={cfg['use_amp']}\n")

    from load_data import load_t5_data
    from t5_utils import initialize_model
    from training_harness import train_t5
    from eval_harness import evaluate_t5
    from transformers import T5TokenizerFast

    args = _config_to_args(cfg)

    train_loader, dev_loader, test_loader = load_t5_data(
        cfg['batch_size'], cfg['test_batch_size'])
    model = initialize_model(args)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')

    def eval_fn(m, loader, c):
        return evaluate_t5(m, loader, c, tokenizer=tokenizer,
                           split='dev', save_predictions=False)

    t0 = time.time()
    train_result = train_t5(model, cfg, train_loader, dev_loader, eval_fn=eval_fn)

    print('\nFinal dev evaluation...')
    dev_result = evaluate_t5(model, dev_loader, cfg, tokenizer=tokenizer,
                             split='dev', save_predictions=True)
    print('Test inference...')
    test_result = evaluate_t5(model, test_loader, cfg, tokenizer=tokenizer,
                              split='test', save_predictions=True)

    results = {
        **dev_result,
        'duration_sec': time.time() - t0,
        'epochs_trained': train_result['epochs_trained'],
        'test_prediction_path': test_result['prediction_path'],
        'test_record_path': test_result['record_path'],
        'training_log': train_result['training_log'],
    }

    reg = ExperimentRegistry()
    run_id = reg.log_run(cfg, results)
    print(f'\nLogged run: {run_id}')
    print(f"  Dev F1:      {results['dev_record_f1']:.4f}")
    print(f"  Dev EM:      {results['dev_record_em']:.4f}")
    print(f"  Dev SQL EM:  {results['dev_sql_em']:.4f}")
    print(f"  Err rate:    {results['dev_error_rate']*100:.2f}%")
    print(f"  Dev SQL:     {results['prediction_path']}")
    print(f"  Test SQL:    {results['test_prediction_path']}")


def run_prompting(config_name: str) -> None:
    if config_name not in PROMPT_CONFIGS:
        print(f"Unknown prompt config '{config_name}'. "
              f"Available: {list(PROMPT_CONFIGS.keys())}", file=sys.stderr)
        sys.exit(1)

    cfg = PROMPT_CONFIGS[config_name].copy()

    print(f"== Prompting experiment: {cfg['experiment_name']} ==")
    _print_device_info()
    print(f"  model:  {cfg['model_name']}, quant={cfg['quantization']}")
    print(f"  k:      {cfg['k']}, selection={cfg['example_selection']}, "
          f"schema={cfg['include_schema']}\n")

    from load_data import load_prompting_data
    from prompting import initialize_model_and_tokenizer
    from prompting_utils import read_schema
    from prompting_harness import evaluate_prompting
    from utils import set_random_seeds

    set_random_seeds(cfg.get('seed', 42))

    train_x, train_y, dev_x, dev_y, test_x = load_prompting_data('data')

    schema = None
    if cfg.get('include_schema'):
        schema = read_schema(os.path.join('data', 'flight_database.schema'))

    tokenizer, model = initialize_model_and_tokenizer(
        cfg['model_name'], cfg.get('quantization', False))

    results = evaluate_prompting(
        cfg, tokenizer, model, train_x, train_y, dev_x, dev_y, test_x,
        schema=schema,
    )

    reg = ExperimentRegistry()
    run_id = reg.log_run(cfg, results)
    print(f'\nLogged run: {run_id}')
    print(f"  Dev F1:      {results['dev_record_f1']:.4f}")
    print(f"  Dev EM:      {results['dev_record_em']:.4f}")
    print(f"  Dev SQL EM:  {results['dev_sql_em']:.4f}")
    print(f"  Err rate:    {results['dev_error_rate']*100:.2f}%")


def run_batch(spec: str, continue_on_error: bool = True) -> None:
    """Run a comma-separated list of configs in sequence.

    Each entry is `kind:config_name` where kind in {t5, prompting}.
    Example: `t5:t5_ft_baseline,prompting:gemma1b_k0,t5:t5_ft_long`.
    Bare names without the prefix are inferred from the config dicts.
    """
    items: list = []
    for raw in spec.split(','):
        raw = raw.strip()
        if not raw:
            continue
        if ':' in raw:
            kind, name = raw.split(':', 1)
        elif raw in T5_CONFIGS:
            kind, name = 't5', raw
        elif raw in PROMPT_CONFIGS:
            kind, name = 'prompting', raw
        else:
            print(f"[batch] skipping unknown config '{raw}'", file=sys.stderr)
            continue
        items.append((kind.strip(), name.strip()))

    if not items:
        print('[batch] no valid configs to run', file=sys.stderr)
        sys.exit(1)

    print(f'\n=== BATCH RUN: {len(items)} experiments ===')
    for i, (k, n) in enumerate(items, 1):
        print(f'  [{i}/{len(items)}] {k}:{n}')
    print()

    failures = []
    for i, (kind, name) in enumerate(items, 1):
        bar = '#' * 70
        print(f'\n{bar}\n# [{i}/{len(items)}] {kind}:{name}\n{bar}')
        try:
            if kind == 't5':
                run_t5(name)
            elif kind == 'prompting':
                run_prompting(name)
            else:
                raise ValueError(f'unknown kind: {kind}')
        except SystemExit:
            raise
        except Exception as e:  # pragma: no cover
            failures.append((kind, name, str(e)))
            print(f'\n!! [{kind}:{name}] FAILED: {e!r}', file=sys.stderr)
            import traceback
            traceback.print_exc()
            if not continue_on_error:
                sys.exit(1)

    print(f'\n=== BATCH COMPLETE: {len(items) - len(failures)}/{len(items)} succeeded ===')
    if failures:
        print('Failures:')
        for k, n, e in failures:
            print(f'  - {k}:{n} -> {e}')
    print(ExperimentRegistry().dashboard())


def main() -> None:
    parser = argparse.ArgumentParser(description='A4 experiment orchestrator')
    parser.add_argument('--task', choices=['t5', 'prompting', 'batch', 'dashboard', 'list'],
                        required=True)
    parser.add_argument('--config', default=None,
                        help='Config name (for t5/prompting) or comma-separated list (for batch)')
    parser.add_argument('--strict', action='store_true',
                        help='In batch mode, stop on first failure instead of continuing')
    args = parser.parse_args()

    if args.task == 'dashboard':
        print(ExperimentRegistry().dashboard())
        return
    if args.task == 'list':
        print('T5 configs:')
        for name in T5_CONFIGS:
            print(f'  {name}')
        print('Prompting configs:')
        for name in PROMPT_CONFIGS:
            print(f'  {name}')
        return

    if args.config is None:
        print('--config is required for t5 / prompting / batch tasks', file=sys.stderr)
        sys.exit(1)

    if args.task == 't5':
        run_t5(args.config)
    elif args.task == 'prompting':
        run_prompting(args.config)
    else:  # batch
        run_batch(args.config, continue_on_error=not args.strict)


if __name__ == '__main__':
    main()
