# Agent Iteration 002 — more training, new best lr
**Timestamp**: 2026-04-24 03:49 (run_001 finished at 04:09, this iter planned during eval tail)
**Registry state**: 1 run logged

## OBSERVE

iter 001 (`t5_ft_baseline`, 10 epochs, lr=1e-4, eff_bs=16, fp32 + grad_ckpt) completed:

| Epoch | train_loss | dev_loss | dev_F1 |
|---|---|---|---|
| 1 | 3.456 | 0.701 | 0.1180 |
| 4 | 0.185 | 0.106 | 0.3307 |
| 6 | 0.119 | 0.072 | 0.4421 |
| 9 | 0.078 | 0.051 | **0.5171** |
| 10 | 0.071 | 0.046 | 0.5169 |

Wall clock: 2h 45m (9889 s). Best at epoch 9 (patience=3 but epoch 10 was within tolerance).

Side metrics (epoch 10 eval): dev_record_em=0.4528, dev_sql_em=0.017, **dev_error_rate=0.386**.

## ANALYZE

- **Milestone**: cleared (0.30 bar hit at epoch 4, final 0.517 on dev).
- **Saturation**: F1 movement epoch-over-epoch: +0.075 → +0.104 → +0.068 → +0.044 → +0.024 → +0.019 → +0.032 → **-0.0002** (10 vs 9). The last step went down — textbook plateau / early onset of overfitting. train_loss still dropping, dev_loss dropping, but the proxy-target coupling (dev_loss → dev_F1) broke around epoch 9–10.
- **Error rate = 38.6% is the elephant in the room**. 180/466 dev queries produce SQL that throws on the database. Record F1 is computed from correctly-executing queries only — every syntax error is a lost 1.0 / N. If we can halve the error rate, dev_F1 probably rises to ~0.60.
- **Anomaly — dev_sql_em = 0.017**: only ~8 of 466 queries are surface-identical to the gold. This isn't a bug — natural SQL often has many spelling equivalents — but it tells us the model is *paraphrasing* a lot while still hitting Record F1=0.52. That's encouraging for beam search: many candidate beams may be semantically valid.
- **Checkpoint saved** at `experiments/checkpoints/t5_ft_baseline_best.pth` (epoch 9 weights).
- **Hardware**: confirmed 4 GB GPU is fine with bs=4, ga=4, fp32, grad_ckpt (3.7 GB used at peak during generation). bf16 crashed on this build; fp32 is the safe path.

### Hypotheses for next run
- **H1 (longer training)**: more epochs with a longer cosine schedule could push F1 past 0.52. Rationale: dev_loss was still monotonically decreasing, only dev_F1 plateaued — that's often a cosine-schedule artefact where the model hasn't annealed to a sharp minimum yet.
- **H2 (higher peak LR)**: lr=3e-4 peak with long warmup may reach a better minimum than lr=1e-4. Baseline lr was arguably too conservative given a full finetune.
- **H3 (beam search)**: num_beams=4 at inference likely reduces error rate (fewer degenerate decodes) and gains 2–5 pts F1, for free. This can be tested on the iter-001 checkpoint without retraining.

### Gap analysis
- T5 ft: 0.517 → realistic ceiling ~0.70 on dev. Room to grow.
- T5 scr: untried. Starts from random init, much harder; realistic ceiling on 4 GB = ~0.40.
- Gemma prompting: blocked on HF login.

## DECIDE

**Action (iter 002)**: launch `t5_ft_long` overnight. Updated config:
- bs=4, ga=4 (eff_bs=16, same as iter 001 — avoid destabilising what works)
- lr=3e-4 peak (H2), cosine with 1000 warmup steps
- max_epochs=15, patience=5 (H1)
- num_beams=1 during intra-training eval (keep per-epoch eval < 10 min)
- use_amp=False, gradient_checkpointing=True (local-GPU safe)

Expected wall clock: ~4 h.

Deferred to iter 003+:
- Beam-search-only re-evaluation on the best checkpoint of iter 001 and 002 (cheap win)
- `t5_ft_frozen_encoder` ablation
- T5 from scratch — better suited to Colab, handled separately

## EXECUTE

Updating `T5_CONFIGS['t5_ft_long']` in `colab_train.py` to the safe local-GPU profile, then launching.

Log: `experiments/agent_log/run_002.log`.

## VERIFY

*(to fill after completion)*

## NEXT DECISION

- If `t5_ft_long` > 0.52: lock its checkpoint as new best, rerun beam=4 on both ft runs, take max → iter 003.
- If `t5_ft_long` ≤ 0.52: the baseline lr was the right call; invest remaining time in (a) beam search re-eval (b) `t5_ft_frozen_encoder` ablation for the report.
- In either case, on wake-up prepare a Colab config for T5 from scratch so the user can kick it off on a fresh runtime while iterating locally.
