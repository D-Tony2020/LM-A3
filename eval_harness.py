"""
Unified evaluation for A4 text-to-SQL.

Runs greedy or beam-search generation with a T5 model, saves predictions
in the exact format expected by the assignment leaderboard, and computes
Record F1 / Record EM / SQL EM / SQL error rate.

Callers provide a tokenizer (typically `T5TokenizerFast` from the
`google-t5/t5-small` checkpoint) so this harness stays agnostic to
whichever architecture variant is being evaluated.
"""
import os
import time
from typing import Optional

import torch
from tqdm import tqdm

from utils import compute_metrics, save_queries_and_records


DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
PAD_IDX = 0

ROOT = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')
DATA_DIR = os.path.join(ROOT, 'data')


def _ensure_dirs() -> None:
    for d in [RESULTS_DIR, RECORDS_DIR]:
        os.makedirs(d, exist_ok=True)


@torch.inference_mode()
def compute_dev_loss(model, dev_loader, criterion=None) -> float:
    if criterion is None:
        criterion = torch.nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    for batch in dev_loader:
        enc_ids, enc_mask, dec_in, dec_tgt = [t.to(DEVICE) for t in batch[:4]]
        logits = model(
            input_ids=enc_ids,
            attention_mask=enc_mask,
            decoder_input_ids=dec_in,
        )['logits']
        non_pad = dec_tgt != PAD_IDX
        loss = criterion(logits[non_pad], dec_tgt[non_pad])
        n_tok = int(non_pad.sum().item())
        total_loss += loss.item() * n_tok
        total_tokens += n_tok
    return total_loss / max(total_tokens, 1)


@torch.inference_mode()
def generate_sql(model, loader, tokenizer, max_new_tokens: int = 256,
                 num_beams: int = 1, use_cache: bool = True) -> list:
    """Greedy (num_beams=1) or beam-search generation over a loader.

    Supports both the dev collate (5-tuple) and the test collate
    (3-tuple). The initial decoder input is always batch[-1].
    """
    model.eval()
    predictions: list = []
    for batch in tqdm(loader, desc='generate', leave=False):
        enc_ids = batch[0].to(DEVICE)
        enc_mask = batch[1].to(DEVICE)
        init_dec = batch[-1].to(DEVICE) if isinstance(batch[-1], torch.Tensor) else None

        gen_kwargs = dict(
            input_ids=enc_ids,
            attention_mask=enc_mask,
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
            use_cache=use_cache,
        )
        if init_dec is not None:
            gen_kwargs['decoder_input_ids'] = init_dec

        outputs = model.generate(**gen_kwargs)
        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend(s.strip() for s in decoded)
    return predictions


def evaluate_t5(model, loader, config: dict, tokenizer=None,
                split: str = 'dev', save_predictions: bool = True) -> dict:
    """Full T5 evaluation on the given split.

    Predictions are always written to the canonical prediction/record
    paths because `compute_metrics` reads them back from disk. The
    `save_predictions` flag controls whether a temporary path is used
    for intra-training evals (so checkpoint scoring does not overwrite
    the final dev/test artefact while the model is still warming up).
    For `split='test'` the ground-truth labels are unavailable, so
    metric keys are set to None.
    """
    _ensure_dirs()
    model_type = config.get('model_type', 't5_ft')
    exp_name = config.get('experiment_name', 'run')
    prefix = f'{model_type}_{exp_name}'
    final_sql_path = os.path.join(RESULTS_DIR, f'{prefix}_{split}.sql')
    final_rec_path = os.path.join(RECORDS_DIR, f'{prefix}_{split}.pkl')
    if save_predictions:
        model_sql_path = final_sql_path
        model_rec_path = final_rec_path
    else:
        tmp_dir = os.path.join(RESULTS_DIR, '_tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        model_sql_path = os.path.join(tmp_dir, f'{prefix}_{split}.sql')
        model_rec_path = os.path.join(tmp_dir, f'{prefix}_{split}.pkl')

    t0 = time.time()

    dev_loss: Optional[float] = None
    if split != 'test':
        dev_loss = compute_dev_loss(model, loader)

    if tokenizer is None:
        from transformers import T5TokenizerFast
        tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')

    queries = generate_sql(
        model, loader, tokenizer,
        max_new_tokens=config.get('max_new_tokens', 256),
        num_beams=config.get('num_beams', 1),
    )

    save_queries_and_records(queries, model_sql_path, model_rec_path)

    if split == 'test':
        return {
            'dev_loss': None,
            'dev_record_f1': None,
            'dev_record_em': None,
            'dev_sql_em': None,
            'dev_error_rate': None,
            'eval_time_sec': time.time() - t0,
            'prediction_path': model_sql_path,
            'record_path': model_rec_path,
        }

    gt_sql = os.path.join(DATA_DIR, f'{split}.sql')
    gt_rec = os.path.join(RECORDS_DIR, f'{split}_gt_records.pkl')
    gt_rec_arg = gt_rec if os.path.exists(gt_rec) else None

    sql_em, record_em, record_f1, model_error_msgs = compute_metrics(
        gt_sql, model_sql_path, gt_rec_arg, model_rec_path)

    error_rate = sum(1 for m in model_error_msgs if m) / max(len(model_error_msgs), 1)

    return {
        'dev_loss': dev_loss,
        'dev_record_f1': record_f1,
        'dev_record_em': record_em,
        'dev_sql_em': sql_em,
        'dev_error_rate': error_rate,
        'eval_time_sec': time.time() - t0,
        'prediction_path': model_sql_path,
        'record_path': model_rec_path,
    }


def save_submission_copy(source_sql: str, source_rec: str, target_prefix: str) -> None:
    """Copy a prediction pair into the canonical submission name.

    The leaderboard expects files named exactly `{t5_ft|t5_scr|test}_test.sql`
    (and `.pkl`). Use this once you have decided which run to submit.
    """
    import shutil
    _ensure_dirs()
    tgt_sql = os.path.join(RESULTS_DIR, f'{target_prefix}_test.sql')
    tgt_rec = os.path.join(RECORDS_DIR, f'{target_prefix}_test.pkl')
    shutil.copyfile(source_sql, tgt_sql)
    shutil.copyfile(source_rec, tgt_rec)
    print(f'Copied submission -> {tgt_sql}\n                    {tgt_rec}')
