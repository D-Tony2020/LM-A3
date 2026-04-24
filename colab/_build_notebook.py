"""Generate A4_colab.ipynb — one linear path, "Run all" friendly.

No branches, no optional cells. Edit the CELLS list and re-run:

    python colab/_build_notebook.py

Expected runtime on Colab H100: roughly 90 minutes end-to-end.
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
        '# A4 — Colab driver',
        '',
        '"Runtime → Run all". One linear path. Expected total on H100: ~90 min.',
        '',
        'Pre-flight:',
        '- Runtime → Change runtime type → **H100** GPU.',
        '- Accept licences at https://huggingface.co/google/codegemma-7b-it and https://huggingface.co/google/gemma-3-1b-it.',
        '- Have a GitHub classic PAT (`repo` scope) and an HF classic Read token handy.',
    ),

    md('## 1. Clone repo'),
    code(
        'import os, subprocess, getpass',
        '',
        'OWNER = \'D-Tony2020\'',
        'REPO  = \'LM-A3\'',
        'PROJECT_DIR = f\'/content/{REPO}\'',
        '',
        'gh_token = getpass.getpass(\'GitHub PAT (repo scope): \')',
        'if not os.path.exists(PROJECT_DIR):',
        '    url = f\'https://{gh_token}@github.com/{OWNER}/{REPO}.git\'',
        '    subprocess.run([\'git\', \'clone\', url, PROJECT_DIR], check=True)',
        '    del url',
        '',
        'os.chdir(PROJECT_DIR)',
        '!git pull --quiet',
        '',
        '# Keep the token in the remote URL so auto-submit can push back.',
        '# Clear the local variable so it does not linger in notebook state.',
        'del gh_token',
        '!git log --oneline -3',
    ),

    md('## 2. Install dependencies'),
    code(
        '!pip install -q transformers==4.51.3 accelerate==0.29.3 bitsandbytes==0.43.1 \\',
        '    sentencepiece==0.2.0 tokenizers==0.21.0 nltk==3.8.1 wandb==0.15.10 tqdm==4.66.1',
        'import torch',
        'print(\'torch\', torch.__version__, \'cuda\', torch.cuda.is_available())',
        '!nvidia-smi --query-gpu=name,memory.total --format=csv',
    ),

    md('## 3. HuggingFace login'),
    code(
        'from huggingface_hub import login',
        'import getpass',
        'hf_tok = getpass.getpass(\'HF token (classic Read): \')',
        'login(token=hf_tok, add_to_git_credential=False)',
        'del hf_tok',
        'print(\'HF logged in OK\')',
    ),

    md('## 4. Cache dev ground-truth records (~40 s)'),
    code('!python cache_gt_records.py --split dev'),

    md(
        '## 5. Run the two missing tracks (slim batch)',
        '',
        'T5 ft is NOT in this batch — we already have a real local run',
        '(`results/t5_ft_test.sql`, dev_F1=0.5171) committed. `make_submission.py`',
        'in cell 7 will pick the right one.',
        '',
        'This batch handles the two tracks the local 4 GB GPU cannot do well:',
        '- **t5_scr_h100**: ~20 min — T5 from scratch on H100',
        '- **codegemma7b_k3_bm25_schema**: ~60 min — best single LLM submission',
        '',
        '`--auto-submit` commits and pushes after **each** successful track,',
        'so even if the second one is preempted, the first lands on GitHub.',
    ),
    code(
        '!git config user.email "colab@runner"',
        '!git config user.name  "A4 Colab Runner"',
        '!python colab_train.py --task batch --auto-submit --config \\',
        '    "t5:t5_scr_h100,prompting:codegemma7b_k3_bm25_schema"',
    ),

    md('## 6. Dashboard'),
    code('!python colab_train.py --task dashboard'),

    md('## 7. Final make_submission + push (catches anything auto-submit missed)'),
    code(
        '!python make_submission.py',
        '!git add results/ records/ experiments/registry.csv experiments/runs/',
        '!git commit -m "Final: Colab session wrap-up" || echo "(nothing to commit)"',
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
        'language_info': {'name': 'python', 'version': '3.10'},
        'colab': {'provenance': [], 'gpuType': 'H100'},
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
