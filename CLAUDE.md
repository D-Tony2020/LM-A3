# Project: A4 — Cornell CS5744 Text-to-SQL

## Project Identity
- **Task**: Translate natural language to SQLite SQL queries against `data/flight_database.db` (a flight-booking schema).
- **Tracks**: Three independent systems, all benchmarked on the same dev/test split.
  1. **`t5_ft`** — Finetune `google-t5/t5-small` (encoder-decoder, ~60M params).
  2. **`t5_scr`** — Same architecture, trained from scratch (random init).
  3. **`gemma_*`** — Frozen Gemma instruction-tuned LLM with k-shot prompting (1B / 4B / 12B / CodeGemma-7B).
- **Primary metric**: **Record F1** (executes generated SQL and ground-truth SQL on the database, compares the result sets, takes F1 over the multiset of returned rows).
- **Secondary metrics**: Record EM, SQL EM, generation error rate (% queries that throw a SQLite error).
- **Deadlines** (all 11:59 PM):
  - Milestone (5 pt): T5 ft test F1 ≥ 0.30 by **2026-04-20** *(passed)*
  - Final report + leaderboard: **2026-04-24**
- **Spec**: [INFO/CS_5744_A4.pdf](INFO/CS_5744_A4.pdf). Always re-consult the source for tie-breakers — don't trust paraphrasing.

## !! Hard Constraints (from spec) !!

### Submission file naming (results/, records/)
- `results/t5_ft_test.sql` + `records/t5_ft_test.pkl` — finetune track
- `results/t5_scr_test.sql` + `records/t5_scr_test.pkl` — from-scratch track
- `results/test_test.sql` + `records/test_test.pkl` — LLM track (single chosen Gemma variant only)
- Each `.sql` line aligns with the corresponding line in `data/test.nl`.
- `.pkl` is `(records, error_msgs)` where each is a list of length `len(test.nl)`. Use `utils.save_queries_and_records`.

### Files NOT to modify (repo policy, see README.md)
- `tests/` (autograder)
- `.github/` (autograder)
- `pytest.ini`

### Allowed dependencies
Only what is in `pyproject.toml` plus the Python standard library:
`accelerate==0.29.3, bitsandbytes==0.43.1, matplotlib==3.8.0, nltk==3.8.1, numpy==1.26.0, plotly==5.18.0, seaborn==0.13.2, sentencepiece==0.2.0, tokenizers==0.21.0, torch==2.1.2, tqdm==4.66.1, transformers==4.51.3, wandb==0.15.10`. Dev: `hypothesis==6.96.1, pytest==7.4.4`.
- **No pandas** — registry uses csv + json from stdlib.
- Python **3.10.x only** (3.11+ disallowed).

### Scoring formula
Performance grade = `f(F1_best)*35 + f(F1_2nd)*5 + f(F1_3rd)*5`
where `f(x) = 3 * (sigmoid(2.5x) - 0.5)`. So one strong system dominates; the other two only need to be present.

### Leaderboard
- Refresh: every 24h at 8 PM, plus 8h before deadline. Whatever is in `main` at refresh time is what's evaluated.
- "If results go down, they go down." Validate on dev before pushing.

### Model rules
- T5 must use `google-t5/t5-small` checkpoint or its config (no T5-base/large variants).
- Gemma must be one of the listed instruction-tuned variants (1B / 4B / 12B / CodeGemma-7B).
- HuggingFace creds must NOT be committed. `huggingface_hub.login` from terminal once.

### Reproducibility
- Set seeds via `utils.set_random_seeds`.
- Default seed = 42 in registry; override per-experiment when needed.

## Hardware Profile

### Local (this machine)
- **GPU**: NVIDIA RTX 3050 Ti Laptop, **3.99 GB VRAM**, capability (8, 6).
- **Python**: 3.10.11 in `.venv` (uv-managed). `torch==2.1.2+cu121` installed via `--index-url https://download.pytorch.org/whl/cu121`.
- **uv cache**: `D:/tmp/uv-cache` (cross-disk; set `UV_CACHE_DIR=D:/tmp/uv-cache`).
- **Sweet spot for T5-small ft**: bs=16, max_len=256, AMP bf16. ~3 GB VRAM. ~40 min for 10 epochs.
- **Max for T5-small scr**: bs=32 with grad_accum, max_len=256. Tight on memory.
- **Gemma-1B prompting**: bf16 → ~2 GB. Works locally. Larger Gemmas need Colab.

### Colab (handled by user, parallel)
- For `t5_scr_long`, `gemma27b_q4`, beam-search variants. Configs already in [colab_train.py](colab_train.py).

## Baseline / Current Best (last updated 2026-04-24)

| Track | Run name | dev F1 | dev EM | dev SQL EM | err% | epochs | notes |
|---|---|---|---|---|---|---|---|
| smoke t5_ft | smoke_t5_ft (4 train batches) | 0.0625 | — | — | — | 1 | sanity only, not a real baseline |
| t5_ft | — | — | — | — | — | — | next: full `t5_ft_baseline` config |
| t5_scr | — | — | — | — | — | — | next: full `t5_scr_baseline` after t5_ft works |
| gemma_1b k0 | — | — | — | — | — | — | next: needs HF auth login first |

## Data
- **Source**: `data/{train,dev,test}.nl` and `data/{train,dev}.sql`. No `test.sql` (held out).
- **Sizes**: train 4225, dev 466, test 431.
- **Schema**: `data/flight_database.schema` — JSON-like, 23 KB. 25 entity tables (airline, airport, flight, …). Read with `prompting_utils.read_schema` as raw string.
- **Database**: `data/flight_database.db` — SQLite. Path is hardcoded in `utils.DB_PATH`.
- **Tokenizer**: `T5TokenizerFast.from_pretrained('google-t5/t5-small')` for T5; auto-tokenizer per Gemma variant.
- **Decoder BOS**: `<extra_id_0>` (id 32099). PAD = 0. EOS = 1.
- **GT records cache**: `records/dev_gt_records.pkl` already built (40 s, 0 errors). Re-run `python cache_gt_records.py --split dev` if it goes stale.

## Repo Layout

```
a4-D-Tony2020/
├── INFO/CS_5744_A4.pdf          # Source spec — always defer to this
├── data/                         # train/dev/test .nl/.sql + schema + .db
├── tests/                        # DO NOT MODIFY — autograder
├── results/                      # SQL submission files
├── records/                      # .pkl record files (incl. dev_gt_records.pkl cache)
├── experiments/                  # Built by ExperimentRegistry on first run
│   ├── registry.csv              # Append-only run log
│   ├── runs/{run_id}.json        # Per-run detail
│   ├── checkpoints/              # T5 model weights
│   ├── colab_output/             # Colab predictions kept separate from local
│   └── prompting_logs/           # Full prompt/response trajectories per ICL run
│
├── load_data.py                  # T5Dataset, collate fns, load_prompting_data  [STUDENT]
├── t5_utils.py                   # initialize_model, save/load ckpt, wandb       [STUDENT]
├── prompting.py                  # create_prompt, exp_kshot, eval_outputs        [STUDENT]
├── prompting_utils.py            # read_schema, extract_sql_query                [STUDENT]
├── train_t5.py                   # eval_epoch, test_inference                    [STUDENT]
├── utils.py                      # PROVIDED + utf-8 encoding patch
├── evaluate.py                   # PROVIDED — dev set F1 score CLI
│
├── experiment_registry.py        # Append-only CSV + per-run JSON                [HARNESS]
├── training_harness.py           # T5 train loop with AMP / early stop / cosine  [HARNESS]
├── eval_harness.py               # F1/EM/error_rate eval + greedy/beam generate  [HARNESS]
├── prompting_harness.py          # k-shot orchestration + ICL example selection  [HARNESS]
├── colab_train.py                # CONFIGS + CLI orchestrator (T5 / prompting)   [HARNESS]
└── cache_gt_records.py           # One-off helper for dev_gt_records.pkl cache
```

## Workflow Status (as of 2026-04-24)

### Done
- Harness scaffolded (5 modules)
- All student TODOs implemented
- `pytest tests/` 5/5 passing
- GT dev records cached
- T5 ft smoke test green on GPU (4 train batches, dev_F1=0.0625, 23 s)
- `utils.py` patched with `encoding='utf-8'` (Windows GBK locale would fail)

### Next (recommended order)
1. Run `t5_ft_baseline` end-to-end on local GPU. Target dev F1 ≥ 0.3 (milestone bar).
2. While T5 trains, set up HF auth and run `gemma1b_k0` smoke.
3. Sweep T5 ft configs (`t5_ft_long`, `t5_ft_frozen_encoder`).
4. Pick the best dev F1 per track and copy to canonical submission paths via `eval_harness.save_submission_copy`.
5. Iterate prompting (k=0/1/3, schema on/off, BM25 vs random). Log every run to registry.
6. T5 from scratch as separate Colab run (long). Pull back via `experiments/colab_output/`.
7. Final report — refer back to `experiments/registry.csv` for ablation tables.

## Common Commands

```bash
# All commands assume cwd = repo root and use the local .venv
PY=".venv/Scripts/python.exe"

# Pytest
$PY -m pytest tests/ -v

# Cache dev GT records (only once)
$PY cache_gt_records.py --split dev

# T5 baseline (full)
$PY colab_train.py --task t5 --config t5_ft_baseline

# Prompting (after `huggingface-cli login`)
$PY colab_train.py --task prompting --config gemma1b_k0

# Registry dashboard
$PY colab_train.py --task dashboard

# List configs
$PY colab_train.py --task list
```

## Reference Numbers
- **Random/empty SQL F1**: ~0 (most queries return non-empty multisets, mismatch).
- **Smoke after 4 batches**: dev_F1 ≈ 0.06 (memorizes BOS+SELECT prefix only).
- **Milestone bar**: 0.30 (test F1 with T5 ft).
- **CS5740 SOTA Sp24**: 81.06 — aspirational, not expected.
- **"Something is broken" threshold**: dev_F1 < 0.05 after 5+ epochs of full ft.

## Gotchas (already hit, won't hit again)
- `compute_metrics` reads SQL/PKL from disk → must save predictions before calling it. `evaluate_t5` now always writes (uses `_tmp/` for non-final eval).
- `utils.save_queries_and_records` opened files without `encoding='utf-8'` → crashed on T5 outputs containing non-GBK chars on Windows. Patched.
- `uv pip install` defaults to *global* Python, not the project `.venv`. Always pass `--python .venv/Scripts/python.exe`.
- `uv run` re-syncs the lock and reverts torch+cu121 → use the venv `python.exe` directly.
- T5 `generate(decoder_input_ids=init_dec)` requires `init_dec` shape `[B, 1]`, value `<extra_id_0>` (id 32099). Already handled by `test_collate_fn` and the dev collate's `initial_decoder_inputs`.
