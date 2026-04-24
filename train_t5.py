import os
import argparse

import torch
import torch.nn as nn
from tqdm import tqdm
import wandb

from t5_utils import (initialize_model, initialize_optimizer_and_scheduler,
                      save_model, load_model_from_checkpoint, setup_wandb)
from transformers import T5TokenizerFast
from load_data import load_t5_data
from utils import compute_metrics, save_queries_and_records

DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
PAD_IDX = 0


def get_args():
    parser = argparse.ArgumentParser(description='T5 training loop')

    parser.add_argument('--finetune', action='store_true', help='Whether to finetune T5 or not')

    parser.add_argument('--optimizer_type', type=str, default='AdamW', choices=['AdamW'])
    parser.add_argument('--learning_rate', type=float, default=1e-4)
    parser.add_argument('--weight_decay', type=float, default=0.0)

    parser.add_argument('--scheduler_type', type=str, default='cosine',
                        choices=['none', 'cosine', 'linear'])
    parser.add_argument('--num_warmup_epochs', type=int, default=0)
    parser.add_argument('--max_n_epochs', type=int, default=10)
    parser.add_argument('--patience_epochs', type=int, default=3)

    parser.add_argument('--use_wandb', action='store_true')
    parser.add_argument('--experiment_name', type=str, default='experiment')

    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--test_batch_size', type=int, default=32)

    parser.add_argument('--max_new_tokens', type=int, default=256)
    parser.add_argument('--num_beams', type=int, default=1)

    return parser.parse_args()


def train(args, model, train_loader, dev_loader, optimizer, scheduler):
    best_f1 = -1.0
    epochs_since_improvement = 0

    model_type = 'ft' if args.finetune else 'scr'
    checkpoint_dir = os.path.join('checkpoints', f'{model_type}_experiments', args.experiment_name)
    gt_sql_path = os.path.join('data', 'dev.sql')
    gt_record_path = os.path.join('records', 'dev_gt_records.pkl')
    model_sql_path = os.path.join('results', f't5_{model_type}_{args.experiment_name}_dev.sql')
    model_record_path = os.path.join('records', f't5_{model_type}_{args.experiment_name}_dev.pkl')

    tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')

    for epoch in range(args.max_n_epochs):
        tr_loss = train_epoch(args, model, train_loader, optimizer, scheduler)
        print(f'Epoch {epoch}: Average train loss was {tr_loss}')

        eval_loss, record_f1, record_em, sql_em, error_rate = eval_epoch(
            args, model, dev_loader, gt_sql_path, model_sql_path,
            gt_record_path, model_record_path, tokenizer=tokenizer,
        )
        print(f'Epoch {epoch}: Dev loss: {eval_loss}, Record F1: {record_f1}, '
              f'Record EM: {record_em}, SQL EM: {sql_em}')
        print(f'Epoch {epoch}: {error_rate*100:.2f}% of the generated outputs led to SQL errors')

        if args.use_wandb:
            wandb.log({
                'train/loss': tr_loss,
                'dev/loss': eval_loss,
                'dev/record_f1': record_f1,
                'dev/record_em': record_em,
                'dev/sql_em': sql_em,
                'dev/error_rate': error_rate,
            }, step=epoch)

        if record_f1 > best_f1:
            best_f1 = record_f1
            epochs_since_improvement = 0
        else:
            epochs_since_improvement += 1

        save_model(checkpoint_dir, model, best=False)
        if epochs_since_improvement == 0:
            save_model(checkpoint_dir, model, best=True)

        if epochs_since_improvement >= args.patience_epochs:
            print(f'Early stopping at epoch {epoch}')
            break


def train_epoch(args, model, train_loader, optimizer, scheduler):
    model.train()
    total_loss = 0.0
    total_tokens = 0
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)

    for encoder_input, encoder_mask, decoder_input, decoder_targets, _ in tqdm(train_loader):
        optimizer.zero_grad(set_to_none=True)
        encoder_input = encoder_input.to(DEVICE)
        encoder_mask = encoder_mask.to(DEVICE)
        decoder_input = decoder_input.to(DEVICE)
        decoder_targets = decoder_targets.to(DEVICE)

        logits = model(
            input_ids=encoder_input,
            attention_mask=encoder_mask,
            decoder_input_ids=decoder_input,
        )['logits']

        non_pad = decoder_targets != PAD_IDX
        loss = criterion(logits[non_pad], decoder_targets[non_pad])
        loss.backward()
        optimizer.step()
        if scheduler is not None:
            scheduler.step()

        with torch.no_grad():
            num_tokens = int(non_pad.sum().item())
            total_loss += loss.item() * num_tokens
            total_tokens += num_tokens

    return total_loss / max(total_tokens, 1)


def eval_epoch(args, model, dev_loader, gt_sql_pth, model_sql_path,
               gt_record_path, model_record_path, tokenizer=None):
    """Loss on the dev set + greedy generation + Record F1 / EM / error rate."""
    model.eval()
    if tokenizer is None:
        tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')

    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    total_loss = 0.0
    total_tokens = 0
    queries = []

    max_new_tokens = getattr(args, 'max_new_tokens', 256)
    num_beams = getattr(args, 'num_beams', 1)

    with torch.inference_mode():
        for batch in tqdm(dev_loader, desc='dev'):
            encoder_input, encoder_mask, decoder_input, decoder_targets, init_dec = \
                [t.to(DEVICE) if isinstance(t, torch.Tensor) else t for t in batch]

            logits = model(
                input_ids=encoder_input,
                attention_mask=encoder_mask,
                decoder_input_ids=decoder_input,
            )['logits']
            non_pad = decoder_targets != PAD_IDX
            loss = criterion(logits[non_pad], decoder_targets[non_pad])
            n_tok = int(non_pad.sum().item())
            total_loss += loss.item() * n_tok
            total_tokens += n_tok

            outputs = model.generate(
                input_ids=encoder_input,
                attention_mask=encoder_mask,
                decoder_input_ids=init_dec,
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                use_cache=True,
            )
            decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            queries.extend(s.strip() for s in decoded)

    eval_loss = total_loss / max(total_tokens, 1)

    os.makedirs(os.path.dirname(model_sql_path) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(model_record_path) or '.', exist_ok=True)
    save_queries_and_records(queries, model_sql_path, model_record_path)

    gt_rec_arg = gt_record_path if os.path.exists(gt_record_path) else None
    sql_em, record_em, record_f1, error_msgs = compute_metrics(
        gt_sql_pth, model_sql_path, gt_rec_arg, model_record_path)
    error_rate = sum(1 for m in error_msgs if m) / max(len(error_msgs), 1)
    return eval_loss, record_f1, record_em, sql_em, error_rate


def test_inference(args, model, test_loader, model_sql_path, model_record_path, tokenizer=None):
    """Generate test predictions and save in the leaderboard-required format."""
    model.eval()
    if tokenizer is None:
        tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')

    queries = []
    max_new_tokens = getattr(args, 'max_new_tokens', 256)
    num_beams = getattr(args, 'num_beams', 1)

    with torch.inference_mode():
        for batch in tqdm(test_loader, desc='test'):
            encoder_input = batch[0].to(DEVICE)
            encoder_mask = batch[1].to(DEVICE)
            init_dec = batch[2].to(DEVICE)

            outputs = model.generate(
                input_ids=encoder_input,
                attention_mask=encoder_mask,
                decoder_input_ids=init_dec,
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                use_cache=True,
            )
            decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            queries.extend(s.strip() for s in decoded)

    os.makedirs(os.path.dirname(model_sql_path) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(model_record_path) or '.', exist_ok=True)
    save_queries_and_records(queries, model_sql_path, model_record_path)


def main():
    args = get_args()
    if args.use_wandb:
        setup_wandb(args)

    train_loader, dev_loader, test_loader = load_t5_data(args.batch_size, args.test_batch_size)
    model = initialize_model(args)
    optimizer, scheduler = initialize_optimizer_and_scheduler(args, model, len(train_loader))

    train(args, model, train_loader, dev_loader, optimizer, scheduler)

    model = load_model_from_checkpoint(args, best=True)
    model.eval()

    experiment_name = args.experiment_name
    model_type = 'ft' if args.finetune else 'scr'
    gt_sql_path = os.path.join('data', 'dev.sql')
    gt_record_path = os.path.join('records', 'dev_gt_records.pkl')
    model_sql_path = os.path.join('results', f't5_{model_type}_{experiment_name}_dev.sql')
    model_record_path = os.path.join('records', f't5_{model_type}_{experiment_name}_dev.pkl')
    dev_loss, dev_record_f1, dev_record_em, dev_sql_em, dev_error_rate = eval_epoch(
        args, model, dev_loader, gt_sql_path, model_sql_path,
        gt_record_path, model_record_path,
    )
    print(f'Dev set results: Loss: {dev_loss}, Record F1: {dev_record_f1}, '
          f'Record EM: {dev_record_em}, SQL EM: {dev_sql_em}')
    print(f'Dev set results: {dev_error_rate*100:.2f}% of the generated outputs led to SQL errors')

    model_sql_path = os.path.join('results', f't5_{model_type}_{experiment_name}_test.sql')
    model_record_path = os.path.join('records', f't5_{model_type}_{experiment_name}_test.pkl')
    test_inference(args, model, test_loader, model_sql_path, model_record_path)


if __name__ == '__main__':
    main()
