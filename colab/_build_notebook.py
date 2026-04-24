"""Generate A4_colab.ipynb from a list of (kind, source) cells.

Run this once after editing the cell list below. The output notebook is
written to `colab/A4_colab.ipynb` and is the file you actually open in
Google Colab.
"""
import json
import os
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
        '# A4 Colab Driver — Text-to-SQL Experiment Engine',
        '',
        'Drives the long-running experiments that don\'t fit on the local 4 GB GPU.',
        'Each section is self-contained: re-run only the cells you need.',
        '',
        'Pre-flight checklist:',
        '- The repo is on Google Drive at `MyDrive/A4/a4-D-Tony2020/` (edit `PROJECT_DIR` below if different).',
        '- Runtime → Change runtime type → GPU (T4 free / A100 Pro+).',
        '- HuggingFace token is needed for Gemma. Get one at https://huggingface.co/settings/tokens and accept the licence at https://huggingface.co/google/gemma-3-1b-it.',
    ),

    md('## 1. Mount Drive and enter the project'),
    code(
        'from google.colab import drive',
        'drive.mount(\'/content/drive\')',
        '',
        '# Edit this if your repo lives elsewhere on Drive.',
        'PROJECT_DIR = \'/content/drive/MyDrive/A4/a4-D-Tony2020\'',
        '',
        'import os, sys',
        'os.chdir(PROJECT_DIR)',
        'sys.path.insert(0, PROJECT_DIR)',
        '!pwd && ls --color=never',
    ),

    md('## 2. Install dependencies (skip if already in venv)'),
    code(
        '# Colab\'s base image already ships torch+CUDA; just add the project deps.',
        '!pip install -q transformers==4.51.3 accelerate==0.29.3 bitsandbytes==0.43.1 \\',
        '    sentencepiece==0.2.0 tokenizers==0.21.0 nltk==3.8.1 wandb==0.15.10 tqdm==4.66.1',
        '!python -c "import torch, transformers; print(\'torch\', torch.__version__, \'cuda\', torch.cuda.is_available()); print(\'transformers\', transformers.__version__)"',
    ),

    md('## 3. HuggingFace login (only required for Gemma)'),
    code(
        'from huggingface_hub import login',
        'import getpass',
        '',
        '# Paste your token here. It is NEVER written to disk.',
        'token = getpass.getpass(\'HF token: \')',
        'login(token=token, add_to_git_credential=False)',
        '',
        '# Sanity: confirm we can see Gemma-3-1B (will fail if licence not accepted)',
        '!python -c "from huggingface_hub import HfApi; print(HfApi().model_info(\'google/gemma-3-1b-it\').siblings[0])"',
    ),

    md('## 4. GPU + dataset sanity'),
    code(
        '!nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv',
        '!python -c "from load_data import load_t5_data; t,d,e=load_t5_data(8,16); print(\'train\', len(t), \'dev\', len(d), \'test\', len(e))"',
    ),

    md('## 5. Cache GT dev records (one-off, ~40 s)'),
    code(
        '!python cache_gt_records.py --split dev',
    ),

    md(
        '## 6. T5 finetune — full run',
        '',
        'On a T4 (16 GB) you can use the un-shrunk batch sizes. The local-tuned',
        '4 GB-friendly settings still work, just slower per epoch.',
    ),
    code(
        '# Quick milestone-clearing baseline.',
        '!python colab_train.py --task t5 --config t5_ft_baseline',
    ),
    code(
        '# Longer / aggressive finetune.',
        '!python colab_train.py --task t5 --config t5_ft_long',
    ),
    code(
        '# Frozen-encoder ablation (cheap, useful for the report).',
        '!python colab_train.py --task t5 --config t5_ft_frozen_encoder',
    ),

    md('## 7. T5 from scratch — long run on Colab GPU'),
    code(
        '!python colab_train.py --task t5 --config t5_scr_baseline',
    ),
    code(
        '# Push for max F1 — bigger batch, more epochs. Best on A100 / V100.',
        '!python colab_train.py --task t5 --config t5_scr_long',
    ),

    md(
        '## 8. Gemma prompting suite (batch mode)',
        '',
        'Sweeps the four most informative ICL configs in one go and dashboards the',
        'best Record F1 per config.',
    ),
    code(
        '!python colab_train.py --task batch --config \\',
        '    "prompting:gemma1b_k0,prompting:gemma1b_k0_schema,prompting:gemma1b_k1_random,prompting:gemma1b_k3_random,prompting:gemma1b_k3_bm25,prompting:gemma1b_k3_bm25_schema"',
    ),

    md('## 9. Optional — large Gemma with 4-bit quantization'),
    code(
        '# Needs A100 ideally; on T4 will be slow but feasible thanks to bitsandbytes nf4.',
        '!python colab_train.py --task prompting --config gemma27b_k3_bm25_schema_q4',
    ),

    md('## 10. Dashboard + housekeeping'),
    code(
        '!python colab_train.py --task dashboard',
    ),
    code(
        '# All artefacts already live on Drive (project is mounted there), so',
        '# nothing to copy — just confirm what was saved.',
        '!ls -la results/ | head',
        '!ls -la records/ | head',
        '!tail -n 5 experiments/registry.csv',
    ),

    md(
        '## 11. (Optional) git push from Colab',
        '',
        'Only run if you want to commit Colab-produced submissions back to GitHub.',
        'Substitute the actual remote URL.',
    ),
    code(
        '!git -C $PROJECT_DIR status -s',
        '# !git -C $PROJECT_DIR add results/ records/ experiments/registry.csv experiments/runs/',
        '# !git -C $PROJECT_DIR commit -m "Colab batch run"',
        '# !git -C $PROJECT_DIR push origin main',
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
