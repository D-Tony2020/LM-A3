import os
import argparse
import random

from tqdm import tqdm
import torch
from transformers import (AutoTokenizer, AutoProcessor,
                          Gemma3ForCausalLM, Gemma3ForConditionalGeneration)
from transformers import BitsAndBytesConfig

from utils import (set_random_seeds, compute_metrics, save_queries_and_records,
                   compute_records)
from prompting_utils import read_schema, extract_sql_query, save_logs
from load_data import load_prompting_data

DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
MAX_NEW_TOKENS = 256


def get_args():
    parser = argparse.ArgumentParser(description='Text-to-SQL experiments with prompting.')
    parser.add_argument('-s', '--shot', type=int, default=0)
    parser.add_argument('-m', '--model', type=str, default='gemma-1b')
    parser.add_argument('-q', '--quantization', action='store_true')
    parser.add_argument('--include_schema', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--experiment_name', type=str, default='experiment')
    return parser.parse_args()


def create_prompt(sentence, k, train_x=None, train_y=None, schema=None, seed=42):
    """Build the user-turn prompt: optional schema, k example pairs, then the query."""
    parts = []
    if schema:
        parts.append(f'Database schema:\n{schema}')

    if k > 0 and train_x is not None and train_y is not None:
        rng = random.Random(seed + (hash(sentence) & 0xFFFF))
        idxs = rng.sample(range(len(train_x)), min(k, len(train_x)))
        parts.append('Examples:')
        for i in idxs:
            parts.append(f'NL: {train_x[i]}\nSQL: {train_y[i]}')

    parts.append(
        'Now write the SQLite SQL query for the following instruction. '
        'Output only the SQL on a single line.\n'
        f'NL: {sentence}\nSQL:'
    )
    return '\n\n'.join(parts)


def exp_kshot(tokenizer, model, inputs, k, train_x=None, train_y=None, schema=None,
              system_instruction=None, seed=42):
    """Run k-shot prompting over a list of natural-language inputs."""
    sys_msg = system_instruction or (
        'You are an assistant that translates natural-language instructions into '
        'SQLite SQL queries for a flight-booking database. Output only the SQL '
        'query, with no explanation and no markdown fences.'
    )

    raw_outputs = []
    extracted_queries = []

    for sentence in tqdm(inputs):
        prompt = create_prompt(sentence, k, train_x=train_x, train_y=train_y,
                               schema=schema, seed=seed)
        messages = [
            {'role': 'system', 'content': sys_msg},
            {'role': 'user', 'content': prompt},
        ]
        input_tokenized = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors='pt',
        ).to(model.device)

        with torch.inference_mode():
            outputs = model.generate(
                **input_tokenized, max_new_tokens=MAX_NEW_TOKENS, use_cache=True,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        prompt_len = input_tokenized['input_ids'].shape[1]
        continuation = outputs[0][prompt_len:]
        response = tokenizer.decode(continuation, skip_special_tokens=True)
        raw_outputs.append(response)
        extracted_queries.append(extract_sql_query(response))

    return raw_outputs, extracted_queries


def eval_outputs(eval_x, eval_y, gt_sql_path, model_sql_path,
                 gt_record_path, model_record_path):
    """Compute Record F1 / Record EM / SQL EM and the error rate."""
    gt_rec_arg = gt_record_path if os.path.exists(gt_record_path) else None
    sql_em, record_em, record_f1, model_error_msgs = compute_metrics(
        gt_sql_path, model_sql_path, gt_rec_arg, model_record_path)
    error_rate = sum(1 for m in model_error_msgs if m) / max(len(model_error_msgs), 1)
    return sql_em, record_em, record_f1, model_error_msgs, error_rate


def initialize_model_and_tokenizer(model_name, to_quantize=False):
    """Build (tokenizer, model) for the supported Gemma variants."""
    if model_name == 'gemma-1b':
        model_id = 'google/gemma-3-1b-it'
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        if to_quantize:
            nf4_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4')
            model = Gemma3ForCausalLM.from_pretrained(
                model_id, quantization_config=nf4_config, torch_dtype=torch.bfloat16,
            )
        else:
            model = Gemma3ForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.bfloat16,
            ).to(DEVICE)
        return tokenizer, model

    if model_name in {'gemma-4b', 'gemma-12b', 'gemma-27b', 'codegemma-7b'}:
        size_to_id = {
            'gemma-4b': 'google/gemma-3-4b-it',
            'gemma-12b': 'google/gemma-3-12b-it',
            'gemma-27b': 'google/gemma-3-27b-it',
            'codegemma-7b': 'google/codegemma-7b-it',
        }
        model_id = size_to_id[model_name]
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        kwargs = {'device_map': 'auto', 'torch_dtype': torch.bfloat16}
        if to_quantize:
            kwargs['quantization_config'] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type='nf4')
        model = Gemma3ForConditionalGeneration.from_pretrained(model_id, **kwargs).eval()
        return tokenizer, model

    raise NotImplementedError(f"Model '{model_name}' is not implemented in this template.")


def main():
    args = get_args()
    set_random_seeds(args.seed)

    train_x, train_y, dev_x, dev_y, test_x = load_prompting_data('data')

    schema = None
    if args.include_schema:
        schema = read_schema(os.path.join('data', 'flight_database.schema'))

    tokenizer, model = initialize_model_and_tokenizer(args.model, args.quantization)

    for eval_split in ['dev', 'test']:
        eval_x, eval_y = (dev_x, dev_y) if eval_split == 'dev' else (test_x, None)

        raw_outputs, extracted_queries = exp_kshot(
            tokenizer, model, eval_x, args.shot,
            train_x=train_x, train_y=train_y, schema=schema, seed=args.seed,
        )

        gt_sql_path = os.path.join('data', f'{eval_split}.sql')
        gt_record_path = os.path.join('records', f'{eval_split}_gt_records.pkl')
        model_sql_path = os.path.join('results', f'gemma_{args.experiment_name}_{eval_split}.sql')
        model_record_path = os.path.join('records', f'gemma_{args.experiment_name}_{eval_split}.pkl')

        os.makedirs(os.path.dirname(model_sql_path) or '.', exist_ok=True)
        os.makedirs(os.path.dirname(model_record_path) or '.', exist_ok=True)
        save_queries_and_records(extracted_queries, model_sql_path, model_record_path)

        if eval_split == 'dev':
            sql_em, record_em, record_f1, model_error_msgs, error_rate = eval_outputs(
                eval_x, eval_y, gt_sql_path, model_sql_path,
                gt_record_path, model_record_path,
            )
            print(f'{eval_split} set results: '
                  f'Record F1: {record_f1}, Record EM: {record_em}, SQL EM: {sql_em}')
            print(f'{eval_split} set: {error_rate*100:.2f}% of outputs led to SQL errors')

            log_path = os.path.join('experiments', 'prompting_logs',
                                    f'{args.experiment_name}_{eval_split}.log')
            save_logs(log_path, sql_em, record_em, record_f1, model_error_msgs)


if __name__ == '__main__':
    main()
