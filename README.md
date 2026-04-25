# Assignment 4

## Virtual environment creation

It's highly recommended to use a virtual environment for each assignment.
You may use environment manager like uv, conda, venv etc.
Here is how you can create an environment with uv and install dependencies.

To install uv
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

To download required dependencies using uv
```sh
cd a4/
uv sync
```

To run python programs using the new environment
```sh
uv run evaluate.py
```

## Unit tests commands

It's recommended to ensure that your completed implementation passes the unit tests before submitting it.
The commands can be run from the root directory of the project.

```sh
uv run pytest
```

This starter repository is intentionally incomplete, so some tests will fail until students implement the TODOs.

Please do NOT commit any code that changes the following files and directories:

- tests/
- .github/
- pytest.ini

Otherwise, your submission may be flagged by GitHub Classroom autograder.

## Evaluation commands

If you have saved predicted SQL queries and associated database records, you can compute F1 scores using:
```sh
uv run evaluate.py \
  --predicted_sql results/t5_ft_dev.sql \
  --predicted_records records/t5_ft_dev.pkl \
  --development_sql data/dev.sql \
  --development_records records/ground_truth_dev.pkl
```

## Submission

Please DO commit your final output files in `results/` and `records/` following the required names and formats.
Please only submit your final files corresponding to the test set.

For SQL queries, ensure that the name of the submission files (in the `results/` subfolder) are:

- `{t5_ft, t5_scr, test}_test.sql`

For database records, ensure that the name of the submission files (in the `records/` subfolder) are:

- `{t5_ft, t5_scr, test}_test.pkl`

Note that the predictions in each line of the `.sql` file or in each index of the list within the `.pkl` file must match each natural language query in `data/test.nl` in the order they appear.

For the LLM, even if you experimented with both models, you should submit only one `.sql` file and one `.pkl` file, corresponding to the model of your choice. Do not submit separate result files for each model.

The leaderboard is available here: <https://github.com/Cornell-Tech-CS5744-Spring-2026/leaderboards/>.

---

## Reproducing the submitted results

Every command below assumes the venv is active (`uv sync` has been run) and the working directory is the repository root.

### Reproduce the T5 finetune submission (best on dev so far)

```sh
# 1. cache the dev ground-truth records once (~40 s)
uv run python cache_gt_records.py --split dev

# 2. train + evaluate
uv run python colab_train.py --task t5 --config t5_ft_baseline

# 3. copy the best run's predictions onto the canonical submission paths
uv run python make_submission.py
```

`results/t5_ft_test.sql` and `records/t5_ft_test.pkl` are written by step 3.

### Reproduce the T5-from-scratch and LLM submissions

T5 from scratch on a 16 GB+ GPU (Colab T4 / A100 / H100):

```sh
uv run python colab_train.py --task t5 --config t5_scr_h100
```

LLM (CodeGemma-7B-it, ICL with 3 BM25-retrieved examples + schema):

```sh
uv run python colab_train.py --task prompting --config codegemma7b_k3_bm25_schema
```

Both write per-run predictions; `make_submission.py` then promotes the best dev_F1 run into the canonical submission paths.

### Run all three tracks in one batch

`--auto-submit` commits + pushes after each successful run, so a later failure cannot lose earlier results:

```sh
uv run python colab_train.py --task batch --auto-submit --config \
  "t5:t5_ft_h100,t5:t5_scr_h100,prompting:codegemma7b_k3_bm25_schema"
```

### Required ablations (Task 3)

```sh
uv run python colab_train.py --task batch --auto-submit --config \
  "prompting:gemma1b_k0,\
   prompting:gemma1b_k1_random,\
   prompting:gemma1b_k3_random,\
   prompting:gemma1b_k3_bm25,\
   prompting:gemma1b_k3_bm25_schema"
```

This covers k = 0 / 1 / 3, random vs BM25 example selection, and schema on/off.

### Inspect / list configs

```sh
uv run python colab_train.py --task list        # all available config names
uv run python colab_train.py --task dashboard   # registry summary
```

## Repository layout

| Path | Purpose |
|---|---|
| `train_t5.py` | Student-facing T5 training entry point (the `eval_epoch` / `test_inference` skeleton) |
| `prompting.py` | Student-facing Gemma prompting entry point |
| `load_data.py`, `t5_utils.py`, `prompting_utils.py`, `utils.py` | Data loaders and helpers |
| `experiment_registry.py` | Append-only CSV + per-run JSON tracking |
| `training_harness.py` | T5 training loop with AMP, gradient checkpointing, label smoothing, early stopping |
| `eval_harness.py` | Greedy/beam SQL generation, F1 / EM / SQL-EM / error rate, submission helpers |
| `prompting_harness.py` | k-shot orchestration, BM25 / token-overlap / random / first_k example selection |
| `colab_train.py` | Orchestrator (`T5_CONFIGS`, `PROMPT_CONFIGS`, `--task batch`) |
| `make_submission.py` | Picks best dev F1 per `model_type`, writes the canonical leaderboard files |
| `eval_from_checkpoint.py` | Re-evaluate a saved checkpoint with different decoding (e.g. beam=4) |
| `cache_gt_records.py` | One-off: pre-compute `records/dev_gt_records.pkl` |
| `tools/error_analysis.py` | Categorise per-query SQLite errors → markdown |
| `tools/report_draft.py` | Render the report's data sections from `experiments/registry.csv` |
| `colab/A4_colab.ipynb` | Optional Colab launcher (the *code* is the .py files; the notebook only runs them) |
| `colab/A4_colab_gemma_ablation.ipynb` | Optional Colab launcher for the 5-config Gemma-1B sweep |
| `experiments/registry.csv` | One row per experiment |
| `experiments/runs/{run_id}.json` | Full config + per-epoch log per experiment |
| `experiments/analysis/*.md` | Generated error analysis + report draft |

## Reading the artefacts

```sh
uv run python tools/error_analysis.py --all --split dev      # one .md per registered run
uv run python tools/report_draft.py                          # combined report sections .md
```

Both scripts are read-only — they never modify registry / results / records.
