"""
T5 training harness with AMP, gradient clipping, early stopping, and
cosine/linear learning-rate schedules. Intended to be called from
colab_train.py so the same training recipe runs on a local GPU or on
Colab without code changes. Evaluation is delegated to an `eval_fn`
passed in by the caller to avoid a circular import with eval_harness.
"""
import os
import math
import time
from typing import Callable, Optional

import torch
import torch.nn as nn
from tqdm import tqdm


DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
CHECKPOINTS_DIR = os.path.join(os.path.dirname(__file__), 'experiments', 'checkpoints')
PAD_IDX = 0


class EarlyStopping:
    """Early stopping on a maximizing metric (Record F1)."""

    def __init__(self, patience: int = 5, min_delta: float = 0.0,
                 maximize: bool = True) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.maximize = maximize
        self.counter = 0
        self.best_score: Optional[float] = None

    def should_stop(self, score: float) -> bool:
        if self.best_score is None:
            self.best_score = score
            return False
        if self.maximize:
            improved = score > self.best_score + self.min_delta
        else:
            improved = score < self.best_score - self.min_delta
        if improved:
            self.best_score = score
            self.counter = 0
            return False
        self.counter += 1
        return self.counter >= self.patience


def _build_lr_lambda(schedule: str, warmup_steps: int, total_steps: int):
    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        if schedule == 'cosine':
            progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
            return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))
        if schedule == 'linear':
            progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
            return max(0.0, 1.0 - progress)
        return 1.0
    return lr_lambda


def train_t5(model, config: dict, train_loader, dev_loader,
             eval_fn: Optional[Callable] = None) -> dict:
    """T5 training loop driven entirely by `config`.

    Supported config keys:
        lr, weight_decay, max_epochs, patience, warmup_steps, lr_schedule,
        grad_clip, grad_accumulation_steps, use_amp, freeze_encoder,
        experiment_name, model_type.

    eval_fn(model, dev_loader, config) -> dict with at least
    'dev_record_f1' and optionally 'dev_loss'. If None, the loop trains
    for the full budget and only tracks training loss.
    """
    lr = config.get('lr', 1e-4)
    weight_decay = config.get('weight_decay', 0.01)
    max_epochs = config.get('max_epochs', 10)
    patience = config.get('patience', 3)
    warmup_steps = config.get('warmup_steps', 500)
    schedule = config.get('lr_schedule', 'cosine')
    grad_clip = config.get('grad_clip', 1.0)
    grad_accum = config.get('grad_accumulation_steps', 1)
    use_amp = config.get('use_amp', True) and DEVICE.type == 'cuda'
    amp_dtype_name = config.get('amp_dtype', 'bf16')
    amp_dtype = torch.bfloat16 if amp_dtype_name == 'bf16' else torch.float16
    exp_name = config.get('experiment_name', 't5_run')

    if config.get('freeze_encoder'):
        for p in model.get_encoder().parameters():
            p.requires_grad = False

    if config.get('gradient_checkpointing'):
        # Drops activation memory ~50% at the cost of extra backward compute.
        # Essential on the local 4 GB GPU; harmless on Colab.
        if hasattr(model, 'gradient_checkpointing_enable'):
            try:
                model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            except TypeError:
                model.gradient_checkpointing_enable()
        if hasattr(model, 'config'):
            model.config.use_cache = False  # incompatible with gradient checkpointing

    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    ckpt_path = os.path.join(CHECKPOINTS_DIR, f'{exp_name}_best.pth')

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=lr, weight_decay=weight_decay,
                                  eps=1e-8, betas=(0.9, 0.999))
    label_smoothing = config.get('label_smoothing', 0.0)
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX,
                                    label_smoothing=label_smoothing)
    # GradScaler is only needed for fp16; bf16 has the full fp32 range.
    use_scaler = use_amp and amp_dtype == torch.float16
    scaler = torch.cuda.amp.GradScaler(enabled=use_scaler)

    steps_per_epoch = max(len(train_loader), 1)
    total_steps = steps_per_epoch * max_epochs
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer, _build_lr_lambda(schedule, warmup_steps, total_steps))

    early_stop = EarlyStopping(patience=patience, maximize=True)
    best_f1 = -1.0
    training_log = []
    t0 = time.time()

    for epoch in range(max_epochs):
        model.train()
        total_loss = 0.0
        total_tokens = 0
        optimizer.zero_grad(set_to_none=True)

        pbar = tqdm(train_loader, desc=f'[{exp_name}] Epoch {epoch+1}/{max_epochs}',
                    leave=False)
        for batch_idx, batch in enumerate(pbar):
            enc_ids, enc_mask, dec_in, dec_tgt = [t.to(DEVICE) for t in batch[:4]]

            with torch.cuda.amp.autocast(enabled=use_amp, dtype=amp_dtype):
                logits = model(
                    input_ids=enc_ids,
                    attention_mask=enc_mask,
                    decoder_input_ids=dec_in,
                )['logits']
                non_pad = dec_tgt != PAD_IDX
                loss = criterion(logits[non_pad], dec_tgt[non_pad])
                loss = loss / grad_accum

            if use_scaler:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            if (batch_idx + 1) % grad_accum == 0:
                if grad_clip > 0:
                    if use_scaler:
                        scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(trainable_params, grad_clip)
                if use_scaler:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()

            with torch.no_grad():
                n_tok = int(non_pad.sum().item())
                total_loss += loss.item() * grad_accum * n_tok
                total_tokens += n_tok
            pbar.set_postfix({'loss': f'{loss.item()*grad_accum:.4f}'})

        avg_train_loss = total_loss / max(total_tokens, 1)

        dev_loss = float('nan')
        f1 = -1.0
        eval_result: dict = {}
        if eval_fn is not None:
            eval_result = eval_fn(model, dev_loader, config)
            f1 = float(eval_result.get('dev_record_f1') or 0.0)
            dl = eval_result.get('dev_loss')
            if dl is not None:
                dev_loss = float(dl)

        current_lr = optimizer.param_groups[0]['lr']
        elapsed = time.time() - t0
        epoch_log = {
            'epoch': epoch + 1,
            'train_loss': avg_train_loss,
            'dev_loss': dev_loss,
            'dev_record_f1': f1,
            'lr': current_lr,
            'elapsed_sec': elapsed,
        }
        training_log.append(epoch_log)
        print(f'  Epoch {epoch+1}: train_loss={avg_train_loss:.4f} | '
              f'dev_loss={dev_loss:.4f} | dev_F1={f1:.4f} | lr={current_lr:.2e}')

        if eval_fn is not None and f1 > best_f1:
            best_f1 = f1
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'best_f1': best_f1,
                'config': config,
            }, ckpt_path)

        if eval_fn is not None and early_stop.should_stop(f1):
            print(f'  Early stopping at epoch {epoch+1} (patience={patience})')
            break

    if os.path.exists(ckpt_path):
        ckpt = torch.load(ckpt_path, map_location=DEVICE)
        model.load_state_dict(ckpt['model_state_dict'])

    total_time = time.time() - t0
    print(f'  Training complete: {total_time:.1f}s  best_dev_F1={best_f1:.4f}')
    return {
        'best_dev_record_f1': best_f1,
        'training_log': training_log,
        'total_time': total_time,
        'epochs_trained': len(training_log),
    }
