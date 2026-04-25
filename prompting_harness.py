"""
Prompting harness for A4 Task 3.

Wraps k-shot orchestration for instruction-tuned Gemma models:
    - ICL example selection (random / first_k / token_overlap / bm25)
    - Optional schema injection from flight_database.schema
    - Chat-template based prompt construction
    - SQL extraction and logging of full prompting trajectories

Every prompting run logs a trajectory JSON under
experiments/prompting_logs/, which is essential for the ablations the
assignment report asks for (prompt wording, k, example selection).
"""
import os
import re
import json
import math
import time
import random
from typing import List, Tuple, Optional

import torch
from tqdm import tqdm

from utils import save_queries_and_records, compute_metrics
from prompting_utils import extract_sql_query


DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
ROOT = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(ROOT, 'results')
RECORDS_DIR = os.path.join(ROOT, 'records')
DATA_DIR = os.path.join(ROOT, 'data')
PROMPTING_LOGS_DIR = os.path.join(ROOT, 'experiments', 'prompting_logs')


DEFAULT_SYSTEM = (
    'You translate natural-language instructions into SQLite queries for a '
    'flight-booking database. Conventions to follow strictly:\n'
    '- Always start with SELECT DISTINCT.\n'
    '- Alias every table with a numeric suffix (flight_1, airport_service_1, etc.).\n'
    '- Join cities to flights through the airport_service table.\n'
    '- City names are uppercase string literals (e.g., \'BOSTON\').\n'
    '- Default year is 1991 unless stated otherwise.\n'
    'Output only the SQL on a single line — no explanation, no markdown fences.'
)


def _tokenize(s: str) -> List[str]:
    return re.findall(r'\w+', s.lower())


def _token_overlap_top_k(query: str, corpus: List[str], k: int) -> List[int]:
    q_toks = set(_tokenize(query))
    scored = []
    for i, doc in enumerate(corpus):
        d_toks = set(_tokenize(doc))
        denom = max(len(q_toks | d_toks), 1)
        scored.append((len(q_toks & d_toks) / denom, i))
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]]


def _bm25_top_k(query: str, corpus: List[str], k: int,
                k1: float = 1.5, b: float = 0.75) -> List[int]:
    tokenized = [_tokenize(d) for d in corpus]
    doc_lens = [len(d) for d in tokenized]
    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(corpus)

    df: dict = {}
    for doc in tokenized:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1

    q_toks = _tokenize(query)
    scored = []
    for i, doc in enumerate(tokenized):
        tf: dict = {}
        for t in doc:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for t in q_toks:
            if t not in tf:
                continue
            idf = math.log((n_docs - df[t] + 0.5) / (df[t] + 0.5) + 1.0)
            num = tf[t] * (k1 + 1)
            denom = tf[t] + k1 * (1 - b + b * doc_lens[i] / avgdl)
            score += idf * num / denom
        scored.append((score, i))
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]]


def select_examples(query: str, train_x: List[str], train_y: List[str],
                    k: int, strategy: str = 'random',
                    seed: int = 42) -> List[Tuple[str, str]]:
    if k == 0 or not train_x:
        return []
    rng = random.Random(seed + (hash(query) & 0xFFFF))

    if strategy == 'random':
        idxs = rng.sample(range(len(train_x)), min(k, len(train_x)))
    elif strategy == 'first_k':
        idxs = list(range(min(k, len(train_x))))
    elif strategy == 'token_overlap':
        idxs = _token_overlap_top_k(query, train_x, k)
    elif strategy == 'bm25':
        idxs = _bm25_top_k(query, train_x, k)
    else:
        raise ValueError(f'Unknown example-selection strategy: {strategy}')

    return [(train_x[i], train_y[i]) for i in idxs]


def build_prompt(query: str, examples: List[Tuple[str, str]],
                 schema: Optional[str] = None) -> str:
    parts: List[str] = []
    if schema:
        parts.append(f'Database schema:\n{schema}')
    if examples:
        parts.append(
            'Here are examples of natural-language instructions and the '
            'corresponding SQL queries:'
        )
        for nl, sql in examples:
            parts.append(f'NL: {nl}\nSQL: {sql}')
    parts.append(
        'Now generate the SQL query for the following instruction. '
        'Return only the SQL query on a single line.\n'
        f'NL: {query}\nSQL:'
    )
    return '\n\n'.join(parts)


def _supports_system_role(tokenizer) -> bool:
    """Return True if the tokenizer's chat template renders a 'system' role.

    CodeGemma-7B-it (Gemma-1 architecture) and a few other instruction-tuned
    chat templates only accept user/assistant roles and raise a Jinja
    TemplateError on system. Gemma-3-* and most modern templates do support
    it. Probe once at the start of a run instead of guessing.
    """
    try:
        tokenizer.apply_chat_template(
            [{'role': 'system', 'content': 'x'},
             {'role': 'user', 'content': 'y'}],
            tokenize=False, add_generation_prompt=False,
        )
        return True
    except Exception:
        return False


def run_kshot(tokenizer, model, eval_x: List[str],
              train_x: List[str], train_y: List[str],
              k: int, strategy: str = 'random',
              schema: Optional[str] = None,
              max_new_tokens: int = 256,
              system_instruction: Optional[str] = None,
              seed: int = 42) -> Tuple[List[str], List[str]]:
    """Run k-shot prompting over all eval inputs.

    Returns (raw_outputs, extracted_queries). The continuation after the
    chat prompt is decoded and handed to ``extract_sql_query`` so both
    chat-tagged and plain-text responses are handled uniformly.
    """
    sys_msg = system_instruction or DEFAULT_SYSTEM
    supports_system = _supports_system_role(tokenizer)

    raw_outputs: List[str] = []
    extracted: List[str] = []

    for sentence in tqdm(eval_x, desc=f'{k}-shot-{strategy}'):
        examples = select_examples(sentence, train_x, train_y, k, strategy, seed=seed)
        user_prompt = build_prompt(sentence, examples, schema=schema)
        if supports_system:
            messages = [
                {'role': 'system', 'content': sys_msg},
                {'role': 'user', 'content': user_prompt},
            ]
        else:
            # Templates without a system role (e.g. CodeGemma) — prepend
            # the system text to the user turn so no information is lost.
            messages = [
                {'role': 'user', 'content': f'{sys_msg}\n\n{user_prompt}'},
            ]
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors='pt'
        ).to(model.device)

        with torch.inference_mode():
            outputs = model.generate(
                **inputs, max_new_tokens=max_new_tokens, use_cache=True,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        prompt_len = inputs['input_ids'].shape[1]
        continuation = outputs[0][prompt_len:]
        response = tokenizer.decode(continuation, skip_special_tokens=True)
        raw_outputs.append(response)
        extracted.append(extract_sql_query(response))

    return raw_outputs, extracted


def evaluate_prompting(config: dict, tokenizer, model,
                       train_x, train_y, dev_x, dev_y, test_x,
                       schema: Optional[str] = None) -> dict:
    """Run dev (with metrics) and test (predictions only), log trajectory.

    Returns a results dict compatible with the experiment registry.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(RECORDS_DIR, exist_ok=True)
    os.makedirs(PROMPTING_LOGS_DIR, exist_ok=True)

    k = config.get('k', 0)
    strategy = config.get('example_selection', 'random')
    exp_name = config.get('experiment_name', 'prompt')
    model_type = config.get('model_type', 'gemma')
    prefix = f'{model_type}_{exp_name}'
    max_new_tokens = config.get('max_new_tokens', 256)
    seed = config.get('seed', 42)
    sys_msg = config.get('system_instruction')

    t0 = time.time()

    dev_raw, dev_queries = run_kshot(
        tokenizer, model, dev_x, train_x, train_y, k, strategy,
        schema=schema, max_new_tokens=max_new_tokens,
        system_instruction=sys_msg, seed=seed,
    )
    dev_sql_path = os.path.join(RESULTS_DIR, f'{prefix}_dev.sql')
    dev_rec_path = os.path.join(RECORDS_DIR, f'{prefix}_dev.pkl')
    save_queries_and_records(dev_queries, dev_sql_path, dev_rec_path)

    gt_sql = os.path.join(DATA_DIR, 'dev.sql')
    gt_rec = os.path.join(RECORDS_DIR, 'dev_gt_records.pkl')
    gt_rec_arg = gt_rec if os.path.exists(gt_rec) else None
    sql_em, record_em, record_f1, err_msgs = compute_metrics(
        gt_sql, dev_sql_path, gt_rec_arg, dev_rec_path)
    error_rate = sum(1 for m in err_msgs if m) / max(len(err_msgs), 1)

    trajectory_path = os.path.join(PROMPTING_LOGS_DIR, f'{prefix}.json')
    with open(trajectory_path, 'w', encoding='utf-8') as f:
        json.dump({
            'config': config,
            'dev_raw_outputs': dev_raw,
            'dev_extracted_queries': dev_queries,
            'dev_metrics': {
                'record_f1': record_f1, 'record_em': record_em,
                'sql_em': sql_em, 'error_rate': error_rate,
            },
        }, f, indent=2, default=str)

    if test_x:
        _, test_queries = run_kshot(
            tokenizer, model, test_x, train_x, train_y, k, strategy,
            schema=schema, max_new_tokens=max_new_tokens,
            system_instruction=sys_msg, seed=seed,
        )
        test_sql_path = os.path.join(RESULTS_DIR, f'{prefix}_test.sql')
        test_rec_path = os.path.join(RECORDS_DIR, f'{prefix}_test.pkl')
        save_queries_and_records(test_queries, test_sql_path, test_rec_path)

    return {
        'dev_record_f1': record_f1,
        'dev_record_em': record_em,
        'dev_sql_em': sql_em,
        'dev_error_rate': error_rate,
        'dev_loss': None,
        'duration_sec': time.time() - t0,
        'best_hyperparam': f'k={k},sel={strategy}',
        'epochs_trained': 0,
    }
