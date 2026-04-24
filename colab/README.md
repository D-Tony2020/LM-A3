# Colab Driver

Two files:

- **`A4_colab.ipynb`** — the notebook you actually open in Google Colab.
- **`_build_notebook.py`** — generator script. Edit the `CELLS` list and re-run with the local venv (`.venv/Scripts/python.exe colab/_build_notebook.py`) to regenerate the `.ipynb`. Keeping the source in Python avoids the JSON-escaping pain of editing notebooks by hand.

## Quick start (Colab)

1. **Sync the project to Drive.** Easiest: clone the repo into `MyDrive/A4/a4-D-Tony2020/` (or edit the `PROJECT_DIR` in cell 2).
2. **Open `colab/A4_colab.ipynb` in Colab.** GitHub → "Open in Colab" works once the repo is pushed.
3. **Switch runtime to GPU.** Runtime → Change runtime type → T4 (free) or A100 (Pro+).
4. **Run cells top-to-bottom.** Each section is independent — you can re-run only what you need.

## What the notebook drives

- T5 finetune configs: `t5_ft_baseline`, `t5_ft_long`, `t5_ft_frozen_encoder`
- T5 from-scratch configs: `t5_scr_baseline`, `t5_scr_long`
- Gemma prompting suite, batch mode: `gemma1b_k0` → `gemma1b_k3_bm25_schema`
- Optional big Gemma: `gemma27b_k3_bm25_schema_q4` (needs A100-class GPU + accepted licence)

Every run logs to `experiments/registry.csv` and `experiments/runs/{run_id}.json` — same registry as the local runs, so the dashboard merges Colab + local results.

## Running configs in batch

`colab_train.py` supports a comma-separated config list:

```bash
python colab_train.py --task batch --config \
  "prompting:gemma1b_k0,prompting:gemma1b_k3_bm25,t5:t5_ft_long"
```

The `kind:` prefix is optional — bare names are auto-routed by which dict contains them. Use `--strict` to abort on the first failure (default is to keep going so a single broken config doesn't waste a Colab session).

## Pulling Colab results back to your laptop

The repo lives on Drive, so artefacts (results/, records/, experiments/) are already on Drive. Two options for getting them locally:

1. Drive desktop client syncs the directory — wait a few minutes.
2. From Colab, `git add` + `git push` the result files (last cell of the notebook).

Don't push checkpoints (`experiments/checkpoints/*.pth`) — they're large and already in `.gitignore` if you've added the standard PyTorch entry.

## Updating the notebook

```bash
# Edit colab/_build_notebook.py, then:
.venv/Scripts/python.exe colab/_build_notebook.py
```

Always commit both files together so the `.ipynb` matches its source.
