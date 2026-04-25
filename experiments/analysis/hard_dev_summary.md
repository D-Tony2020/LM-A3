# Hard-dev F1 (Jaccard < 0.80 with train.nl)

- dev split size: 466
- hard subset (low train similarity): 302 (64.8%)
- easy subset (high train similarity): 164 (35.2%)

Hard-dev F1 is a more test-aligned signal: only 11.1% of *test* queries have Jaccard >= 0.80 with train, vs 35.2% of dev. Use hard-dev F1 when choosing among prompting/finetuning configurations.

| run | overall F1 | hard F1 | easy F1 | hard−overall Δ |
|---|---:|---:|---:|---:|
| `codegemma_7b/codegemma7b_k3_bm25_schema_pp` | 0.6969 | **0.6507** | 0.7820 | -0.0462 |
| `codegemma_7b/codegemma7b_k3_bm25_schema` | 0.5678 | **0.5144** | 0.6661 | -0.0534 |
| `t5_ft/t5_ft_baseline_pp` | 0.5438 | **0.5120** | 0.6025 | -0.0319 |
| `t5_ft/t5_ft_baseline` | 0.5171 | **0.4757** | 0.5933 | -0.0414 |
| `t5_ft/t5_ft_baseline_beam4` | 0.5135 | **0.4690** | 0.5956 | -0.0446 |
| `gemma_1b/gemma1b_k3_bm25` | 0.4565 | **0.4055** | 0.5504 | -0.0510 |
| `t5_ft/t5_ft_frozen_encoder_beam4` | 0.4474 | **0.3959** | 0.5423 | -0.0515 |
| `gemma_1b/gemma1b_k3_random` | 0.1968 | **0.2164** | 0.1608 | +0.0196 |
| `gemma_1b/gemma1b_k1_random` | 0.1779 | **0.2064** | 0.1256 | +0.0284 |
| `t5_scr/t5_scr_h100` | 0.1180 | **0.1424** | 0.0732 | +0.0244 |
| `gemma_1b/gemma1b_k0` | 0.1180 | **0.1424** | 0.0732 | +0.0244 |

> A large negative Δ means the run benefits disproportionately from BM25 retrieval finding near-duplicates and is therefore at risk of over-estimating test F1.
