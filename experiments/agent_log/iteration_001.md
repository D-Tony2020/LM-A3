# Agent Iteration 001 — first real T5 finetune baseline
**Timestamp**: 2026-04-24 00:50
**Registry state**: 0 runs (header only)

## OBSERVE
- Registry is empty — no real runs logged. Only artifact is the smoke test (4 train batches, dev_F1=0.0625) which was a sanity check, not a registered experiment.
- Three tracks waiting: `t5_ft`, `t5_scr`, `gemma_*`.
- Hardware: RTX 3050 Ti, 4 GB VRAM. CUDA available.
- Constraints from CLAUDE.md: T5 must use `google-t5/t5-small`; submission paths fixed (`results/{t5_ft,t5_scr,test}_test.{sql,pkl}`); deadline 2026-04-24.
- Milestone (5 pt): test F1 ≥ 0.30 with T5 ft. Already past the milestone calendar date but the score still counts toward final grade.

## ANALYZE
- **Saturation check**: nothing explored. All knobs wide open.
- **Gap analysis**: T5 ft has the highest expected ROI per minute of compute:
  - It has a known good initialization (pretrained checkpoint), so even one epoch of training should yield a meaningful F1 (>0.1) within 5–10 min.
  - The milestone bar (0.30) is the first "must-clear" threshold; failing to meet it costs 5 pts.
  - In contrast, `t5_scr` needs much longer wall time (random init, more epochs, slower convergence) and `gemma_1b` needs HF auth which the user hasn't set up yet.
- **ROI ranking**:
  1. T5 ft baseline (~40 min, expected F1 ≈ 0.3–0.5)
  2. Gemma 1B 0-shot (~10 min once HF logged in, expected F1 ≈ 0.0–0.1 — instruction-tuned 1B models are weak at SQL but cheap to confirm)
  3. T5 ft variants (long encoder, frozen encoder, beam search) — refinements
  4. T5 from scratch — ship to Colab; local 4 GB VRAM would take 4+ hours
- **Hypotheses for the baseline**:
  - **H1**: With pretrained T5-small and AdamW lr=1e-4, dev F1 will hit 0.3+ within 5 epochs. Reason: SQL is a structured language with a small effective vocabulary inside this database, and the encoder already speaks English well.
  - **H2**: AMP bf16 will not destabilize training. RTX 3050 Ti has compute capability 8.6, so bf16 is native and there's no need for the GradScaler to actually scale.
  - **H3**: Generation cost will dominate eval time. 10 evals × 30 batches × 256 max_new_tokens. If too slow, drop to greedy with smaller max_new_tokens for intra-train evals.

## DECIDE
- **Action 1**: Run `t5_ft_baseline` config end-to-end via `colab_train.py --task t5 --config t5_ft_baseline`. Log to `experiments/agent_log/run_001.log`. Background.
  - Hypothesis: H1 above.
  - Cost: ~40-60 min wall time on RTX 3050 Ti.
  - Success criterion: dev_F1 > 0.25 (would clear the milestone bar with margin).
- Defer parallel actions: 4 GB VRAM cannot fit two training jobs. While the run is going I'll prep the prompting smoke (writing scripts) but won't launch GPU work.

## EXECUTE
- Launching: `colab_train.py --task t5 --config t5_ft_baseline` in background.
- Monitor: `tail experiments/agent_log/run_001.log`.

## VERIFY
*(to be filled after run completes)*

## NEXT DECISION
*(depends on run_001 result)*
- If dev_F1 ≥ 0.30: lock baseline submission, then sweep `t5_ft_long` and `t5_ft_frozen_encoder` for ablations.
- If 0.10 ≤ dev_F1 < 0.30: diagnose — likely lr or warmup issue. Try `t5_ft_long` (higher lr, more epochs).
- If dev_F1 < 0.10: training didn't take; check loss curve, possibly bf16/AMP issue, fall back to fp32.
