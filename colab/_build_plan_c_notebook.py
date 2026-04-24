"""Build `A4_colab_plan_c.ipynb` — a notebook designed to run in parallel
with the original `A4_colab.ipynb` session without stepping on its toes.

Differences from the base notebook:
    - Clones into `/content/LM-A3_v2` (distinct working directory).
    - Creates and pushes a new branch `plan-c`, so auto-submit commits
      do not race with the main branch that the other session is using.
    - Last cell pushes `plan-c` explicitly.

Run once after editing — `python colab/_build_plan_c_notebook.py`.
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
        '# A4 — Colab Driver (plan C / parallel session)',
        '',
        '**Read this first.** This notebook is designed to run *in parallel*',
        'with another Colab session on the main branch. To avoid clobbering',
        'the other session\'s pushes, this one:',
        '',
        '- Clones into a DISTINCT directory (`/content/LM-A3_v2`).',
        '- Works on a DISTINCT branch (`plan-c`).',
        '- Auto-submit commits and pushes only to `origin/plan-c`.',
        '',
        '**Goal**: produce a stronger LLM submission via **CodeGemma-7B-it**',
        'while tracks 1 and 2 are still going on the other session.',
        '',
        '**Prerequisites**:',
        '- License accepted at https://huggingface.co/google/codegemma-7b-it',
        '- License accepted at https://huggingface.co/google/gemma-3-1b-it (backup)',
        '- Runtime → Change runtime type → H100 (80 GB preferred).',
    ),

    md('## 1. Clone repo into a parallel working directory'),
    code(
        '# Uses the public personal mirror so no PAT is strictly needed, but',
        '# pushing back DOES need a PAT with `repo` scope. The token is held',
        '# in memory only.',
        'import os, subprocess, getpass',
        '',
        'OWNER = \'D-Tony2020\'',
        'REPO  = \'LM-A3\'',
        'PROJECT_DIR = f\'/content/{REPO}_v2\'  # distinct from the other session',
        '',
        'gh_token = getpass.getpass(\'GitHub PAT (repo scope) — needed for push: \')',
        '',
        'if not os.path.exists(PROJECT_DIR):',
        '    url = f\'https://{gh_token}@github.com/{OWNER}/{REPO}.git\'',
        '    subprocess.run([\'git\', \'clone\', url, PROJECT_DIR], check=True)',
        '    del url',
        '',
        'os.chdir(PROJECT_DIR)',
        '!git pull --quiet',
        '',
        '# Create / switch to the plan-c branch and push it up so the origin',
        '# tracks it. This is what isolates us from the main-branch session.',
        '!git checkout -B plan-c',
        '!git push -u origin plan-c',
        '',
        'del gh_token',
        '!ls --color=never',
    ),

    md('## 2. Install deps'),
    code(
        '!pip install -q transformers==4.51.3 accelerate==0.29.3 bitsandbytes==0.43.1 \\',
        '    sentencepiece==0.2.0 tokenizers==0.21.0 nltk==3.8.1 wandb==0.15.10 tqdm==4.66.1',
        'import torch, transformers',
        'print(\'torch\', torch.__version__, \'cuda\', torch.cuda.is_available())',
        '!nvidia-smi --query-gpu=name,memory.total --format=csv',
    ),

    md('## 3. HuggingFace login'),
    code(
        'from huggingface_hub import login',
        'import getpass',
        'tok = getpass.getpass(\'HF token (classic Read): \')',
        'login(token=tok, add_to_git_credential=False)',
        'del tok',
        'print(\'logged in OK\')',
    ),

    md('## 4. Cache dev GT records (one-off, ~40 s)'),
    code('!python cache_gt_records.py --split dev'),

    md(
        '## 5. FAST PATH — plan C (CodeGemma-7B)',
        '',
        '`--auto-submit` will now push to the `plan-c` branch we set up above.',
        'If the other session is also pushing to `main`, they will not conflict.',
    ),
    code(
        '!git config user.email "colab@runner"',
        '!git config user.name  "A4 Colab Runner (plan-c)"',
        '!python colab_train.py --task batch --auto-submit --config \\',
        '    "t5:t5_ft_h100,t5:t5_scr_h100,prompting:codegemma7b_k3_bm25_schema"',
    ),

    md('## 6. Dashboard + final push (manual, if you want to be explicit)'),
    code('!python colab_train.py --task dashboard'),
    code(
        '# Any stragglers not caught by auto-submit get pushed here.',
        '!python make_submission.py',
        '!git add results/ records/ experiments/registry.csv experiments/runs/',
        '!git commit -m "Final: plan-c session wrap-up" || echo "(no changes to commit)"',
        '!git push origin plan-c',
    ),

    md(
        '## 7. After both sessions finish — local reconciliation',
        '',
        'On your laptop, after both Colab sessions are done:',
        '',
        '```bash',
        'git fetch mirror main',
        'git fetch mirror plan-c',
        '# Inspect both: which track has higher dev_F1 on each',
        'python make_submission.py --dry-run',
        '# Typically the plan-c side wins the LLM track, main session wins t5_ft.',
        '# Merge the best submissions onto your local main, then push to the',
        '# classroom repo (origin).',
        '```',
    ),
]


NOTEBOOK = {
    'cells': CELLS,
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3',
        },
        'language_info': {'name': 'python', 'version': '3.10'},
        'colab': {'provenance': [], 'gpuType': 'H100'},
        'accelerator': 'GPU',
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}


def main() -> None:
    out = Path(__file__).parent / 'A4_colab_plan_c.ipynb'
    out.write_text(json.dumps(NOTEBOOK, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {out}  ({out.stat().st_size:,} bytes, {len(CELLS)} cells)')


if __name__ == '__main__':
    main()
