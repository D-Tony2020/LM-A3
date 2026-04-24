"""Generate A4_colab_gemma_ablation.ipynb — one-click Gemma-1B ablation sweep.

Designed to be opened AFTER the main A4_colab.ipynb session finishes. The
repo may already be cloned at /content/LM-A3 (from the main session) — the
first cell handles both the "fresh runtime" and "re-use runtime" cases.

Run once after editing the cell list:

    python colab/_build_ablation_notebook.py

Expected runtime on Colab H100: ~110 minutes end-to-end (5 Gemma-1B runs).
"""
import json
from pathlib import Path


def md(*lines: str) -> dict:
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [l if l.endswith('\n') else l + '\n' for l in lines],
    }


def code(*lines: str) -> dict:
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [l if l.endswith('\n') else l + '\n' for l in lines],
    }


CELLS = [
    md(
        '# A4 — Gemma-1B ablation sweep',
        '',
        'Five configurations that close the Task 3 hard requirements in the spec:',
        '- k = 0, 1, 3 coverage',
        '- example-selection comparison (random vs BM25)',
        '- prompt-component comparison (schema on/off)',
        '',
        '**Prerequisite**: run this AFTER `A4_colab.ipynb` has finished the main batch.',
        'Expected runtime on H100: ~110 min. Dependencies and HF login are re-done here',
        'so the notebook is self-contained; if the runtime is the same as the main session,',
        'the pip install and HF login cells will finish in seconds (cached).',
    ),

    md('## 1. Clone / re-use repo'),
    code(
        'import os, subprocess, getpass',
        '',
        'OWNER = \'D-Tony2020\'',
        'REPO  = \'LM-A3\'',
        'PROJECT_DIR = f\'/content/{REPO}\'',
        '',
        'if not os.path.exists(PROJECT_DIR):',
        '    gh_token = getpass.getpass(\'GitHub PAT (repo scope): \')',
        '    url = f\'https://{gh_token}@github.com/{OWNER}/{REPO}.git\'',
        '    subprocess.run([\'git\', \'clone\', url, PROJECT_DIR], check=True)',
        '    del gh_token, url',
        '',
        'os.chdir(PROJECT_DIR)',
        '!git pull --quiet',
        '!git log --oneline -3',
    ),

    md('## 2. Install dependencies (idempotent; fast if already installed)'),
    code(
        '!pip install -q transformers==4.51.3 accelerate==0.29.3 bitsandbytes==0.43.1 \\',
        '    sentencepiece==0.2.0 tokenizers==0.21.0 nltk==3.8.1 wandb==0.15.10 tqdm==4.66.1',
        'import torch',
        'print(\'torch\', torch.__version__, \'cuda\', torch.cuda.is_available())',
        '!nvidia-smi --query-gpu=name,memory.total --format=csv',
    ),

    md('## 3. HuggingFace login (needs Gemma-3-1B-it licence accepted)'),
    code(
        'from huggingface_hub import login',
        'import getpass, os',
        '# Skip re-login if already authenticated in this runtime',
        'if not os.path.exists(os.path.expanduser(\'~/.cache/huggingface/token\')):',
        '    tok = getpass.getpass(\'HF token (classic Read): \')',
        '    login(token=tok, add_to_git_credential=False)',
        '    del tok',
        'print(\'HF ok\')',
    ),

    md('## 4. Cache dev GT records (no-op if already cached)'),
    code(
        'import os',
        'if not os.path.exists(\'records/dev_gt_records.pkl\'):',
        '    !python cache_gt_records.py --split dev',
        'else:',
        '    print(\'dev GT cache already present\')',
    ),

    md(
        '## 5. Run the sweep (5 Gemma-1B configs, `--auto-submit`)',
        '',
        '| # | Config | k | Selection | Schema | Purpose |',
        '|---|---|---|---|---|---|',
        '| 1 | gemma1b_k0 | 0 | — | No | k=0 baseline |',
        '| 2 | gemma1b_k1_random | 1 | random | No | k=1 |',
        '| 3 | gemma1b_k3_random | 3 | random | No | k=3 + random arm |',
        '| 4 | gemma1b_k3_bm25 | 3 | BM25 | No | selection method ablation |',
        '| 5 | gemma1b_k3_bm25_schema | 3 | BM25 | Yes | schema ablation |',
        '',
        'After every successful run, `--auto-submit` regenerates canonical submission',
        'files and pushes to `origin/main`. If the session is preempted mid-sweep, whatever',
        'had finished is already on GitHub.',
    ),
    code(
        '!git config user.email "colab@runner"',
        '!git config user.name  "A4 Colab Runner"',
        '!python colab_train.py --task batch --auto-submit --config \\',
        '    "prompting:gemma1b_k0,\\',
        '     prompting:gemma1b_k1_random,\\',
        '     prompting:gemma1b_k3_random,\\',
        '     prompting:gemma1b_k3_bm25,\\',
        '     prompting:gemma1b_k3_bm25_schema"',
    ),

    md('## 6. Dashboard'),
    code('!python colab_train.py --task dashboard'),

    md('## 7. Final catch-all push (if auto-submit missed anything)'),
    code(
        '!python make_submission.py',
        '!git add results/ records/ experiments/registry.csv experiments/runs/',
        '!git commit -m "Gemma-1B ablation sweep: final wrap-up" || echo "(nothing to commit)"',
        '!git push origin main',
    ),
]


NOTEBOOK = {
    'cells': CELLS,
    'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.10'},
        'colab': {'provenance': [], 'gpuType': 'H100'},
        'accelerator': 'GPU',
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}


def main() -> None:
    out = Path(__file__).parent / 'A4_colab_gemma_ablation.ipynb'
    out.write_text(json.dumps(NOTEBOOK, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {out}  ({out.stat().st_size:,} bytes, {len(CELLS)} cells)')


if __name__ == '__main__':
    main()
