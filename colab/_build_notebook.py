"""Generate A4_colab.ipynb from a list of (kind, source) cells.

Run this once after editing the cell list below. The output notebook is
written to `colab/A4_colab.ipynb` and is the file you actually open in
Google Colab.
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
        '# A4 — Colab Driver',
        '',
        '**Goal**: produce two missing submission files that local 4 GB GPU cannot make:',
        '',
        '- `results/t5_scr_test.{sql,pkl}` — T5 trained from scratch (Task 2)',
        '- `results/test_test.{sql,pkl}` — Gemma prompting (Task 3)',
        '',
        '`results/t5_ft_test.{sql,pkl}` is already in the repo (dev F1 ≈ 0.52, produced locally).',
        '',
        '**Pre-flight**: Runtime → Change runtime type → **T4** (free) is enough; **A100** if you have Pro+.',
    ),

    md('## 1. Clone repo + install deps'),
    code(
        '# Clone the project from GitHub (fastest path; no Drive setup needed).',
        '# Replace the URL if your fork lives elsewhere.',
        'import os, subprocess',
        'REPO_URL = \'https://github.com/Cornell-Tech-CS5744-Spring-2026/a4-D-Tony2020.git\'',
        'PROJECT_DIR = \'/content/a4-D-Tony2020\'',
        '',
        'if not os.path.exists(PROJECT_DIR):',
        '    subprocess.run([\'git\', \'clone\', REPO_URL, PROJECT_DIR], check=True)',
        'os.chdir(PROJECT_DIR)',
        '!git pull --quiet',
        '!ls --color=never',
    ),
    code(
        '# Colab\'s base image already ships torch+CUDA; just add the project deps.',
        '!pip install -q transformers==4.51.3 accelerate==0.29.3 bitsandbytes==0.43.1 \\',
        '    sentencepiece==0.2.0 tokenizers==0.21.0 nltk==3.8.1 wandb==0.15.10 tqdm==4.66.1',
        'import torch, transformers',
        'print(\'torch\', torch.__version__, \'cuda\', torch.cuda.is_available())',
        'print(\'transformers\', transformers.__version__)',
        '!nvidia-smi --query-gpu=name,memory.total --format=csv',
    ),

    md('## 2. HuggingFace login (only required for Gemma)'),
    code(
        'from huggingface_hub import login',
        'import getpass',
        '',
        '# Use a *classic Read* token (https://huggingface.co/settings/tokens).',
        '# Fine-grained tokens need extra perms for gated repos.',
        '# License must already be accepted at https://huggingface.co/google/gemma-3-1b-it',
        'token = getpass.getpass(\'HF token: \')',
        'login(token=token, add_to_git_credential=False)',
        'print(\'logged in OK\')',
    ),

    md('## 3. Cache GT dev records (one-off, ~40 s)'),
    code(
        '!python cache_gt_records.py --split dev',
    ),

    md(
        '## 4. FAST PATH — close the two missing submissions',
        '',
        'Runs T5 from scratch + Gemma 1B 3-shot BM25-with-schema in sequence.',
        'On a T4 this is roughly 3 h training + 30 min prompting. The batch mode',
        'continues even if one config fails so you don\'t lose the night to a bug.',
    ),
    code(
        '!python colab_train.py --task batch --config \\',
        '    "t5:t5_scr_colab,prompting:gemma1b_k3_bm25_schema"',
    ),

    md(
        '## 5. (Optional) bonus — top the local T5 ft baseline',
        '',
        'iter 001 on a 4 GB local card hit dev_F1=0.5171. With Colab\'s 16 GB+ you',
        'can afford bigger batches and beam search at decode time, which often',
        'adds 1-3 F1 points. Skip if you only need the milestone.',
    ),
    code(
        '!python colab_train.py --task t5 --config t5_ft_colab',
    ),
    code(
        '# Aggressive 20-epoch finetune. Run only if the cheaper t5_ft_colab',
        '# already beat the local baseline.',
        '!python colab_train.py --task t5 --config t5_ft_colab_long',
    ),

    md('## 6. (Optional) prompting ablations for the report'),
    code(
        '# Sweep three configs in one go: zero-shot, 3-shot random, 3-shot BM25',
        '# (the schema-on variant was already covered in the FAST PATH).',
        '!python colab_train.py --task batch --config \\',
        '    "prompting:gemma1b_k0,prompting:gemma1b_k3_random,prompting:gemma1b_k3_bm25"',
    ),

    md(
        '## 7. (Optional, A100) — bigger Gemma',
        '',
        'On a T4 this will work but generate slowly. On an A100 it\'s painless.',
    ),
    code(
        '!python colab_train.py --task prompting --config gemma27b_k3_bm25_schema_q4',
    ),

    md('## 8. Pick best per track and rename to leaderboard files'),
    code(
        '!python make_submission.py',
    ),

    md('## 9. Dashboard + push results back to GitHub'),
    code(
        '!python colab_train.py --task dashboard',
    ),
    code(
        '# Configure git author once per Colab session.',
        '!git config user.email "your@email"',
        '!git config user.name "Your Name"',
        '',
        '# Verify the canonical submission files exist before pushing.',
        '!ls -la results/t5_ft_test.sql results/t5_scr_test.sql results/test_test.sql 2>/dev/null',
        '!ls -la records/t5_ft_test.pkl records/t5_scr_test.pkl records/test_test.pkl 2>/dev/null',
        '',
        '# Stage the artefacts the leaderboard needs + the registry.',
        '!git add results/ records/ experiments/registry.csv experiments/runs/',
        '!git status -s',
    ),
    code(
        '# Commit + push. Edit the message if you want.',
        'commit_msg = "Colab batch: t5_scr + gemma_1b prompting submissions"',
        '!git commit -m "$commit_msg"',
        '!git push origin main',
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
        'language_info': {
            'name': 'python',
            'version': '3.10',
        },
        'colab': {
            'provenance': [],
            'gpuType': 'T4',
        },
        'accelerator': 'GPU',
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}


def main() -> None:
    out = Path(__file__).parent / 'A4_colab.ipynb'
    out.write_text(json.dumps(NOTEBOOK, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {out}  ({out.stat().st_size:,} bytes, {len(CELLS)} cells)')


if __name__ == '__main__':
    main()
