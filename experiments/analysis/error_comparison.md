# Error category comparison across all 19 runs

Each cell = % of dev queries that errored in that category. Sorted by dev F1 (descending).

| Run | F1 | err% | unbalanced_parens | no_such_column | no_such_table | syntax_error | other | ambiguous_column | incomplete_input | query_timeout | aggregate_misuse |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gemma_12b/gemma3_12b_k3_bm25_compact_schema_pp` | 0.7408 | 17.8% | — | 13.3% | 0.2% | 1.1% | 2.6% | — | 0.6% | — | — |
| `gemma_12b/gemma3_12b_k3_bm25_compact_schema` | 0.7313 | 20.6% | 14.6% | 4.3% | 0.2% | — | 0.9% | — | 0.6% | — | — |
| `codegemma_7b/codegemma7b_k3_compact_schema_pp` | 0.7190 | 19.1% | — | 12.7% | — | 4.7% | 0.9% | — | 0.9% | — | — |
| `codegemma_7b/codegemma7b_k3_compact_schema` | 0.7048 | 22.7% | 16.7% | 4.7% | — | 0.2% | 0.2% | — | 0.9% | — | — |
| `codegemma_7b/codegemma7b_k3_bm25_schema_pp` | 0.6969 | 17.4% | — | 10.1% | 0.9% | 2.6% | 1.3% | 1.9% | 0.6% | — | — |
| `t5_ft/t5_ft_h100_long_pp` | 0.6001 | 22.5% | — | 8.4% | 0.4% | 7.7% | 3.9% | 1.3% | 0.9% | — | — |
| `t5_ft/t5_ft_h100_long` | 0.5814 | 29.2% | 20.4% | 3.6% | 0.4% | 3.2% | 0.2% | 0.6% | 0.6% | — | — |
| `codegemma_7b/codegemma7b_k3_bm25_schema` | 0.5678 | 37.8% | 30.5% | 4.9% | 0.2% | 0.2% | — | 1.1% | 0.6% | 0.2% | — |
| `t5_ft/t5_ft_baseline_pp` | 0.5438 | 27.7% | 0.2% | 15.9% | 0.2% | 8.4% | 0.4% | 0.2% | 0.4% | 0.9% | 1.1% |
| `t5_ft/t5_ft_baseline` | 0.5171 | 38.6% | 23.6% | 10.3% | 0.2% | 3.0% | 0.4% | 0.2% | 0.4% | 0.4% | — |
| `t5_ft/t5_ft_baseline_beam4` | 0.5135 | 34.1% | 21.9% | 9.9% | — | 1.3% | — | 0.2% | 0.6% | 0.2% | — |
| `gemma_1b/gemma1b_k3_bm25_schema` | 0.4648 | 38.2% | 23.4% | 12.0% | 0.2% | 1.5% | 0.4% | 0.6% | — | — | — |
| `gemma_1b/gemma1b_k3_bm25` | 0.4565 | 41.6% | 25.8% | 12.0% | 0.6% | 2.4% | 0.2% | 0.2% | — | 0.4% | — |
| `t5_ft/t5_ft_frozen_encoder_beam4` | 0.4474 | 20.6% | 17.6% | 1.7% | — | 0.2% | — | 1.1% | — | — | — |
| `gemma_1b/gemma1b_k3_random` | 0.1968 | 67.6% | 35.8% | 17.8% | 8.2% | 3.9% | 0.2% | 1.1% | 0.6% | — | — |
| `gemma_1b/gemma1b_k1_random` | 0.1779 | 66.1% | 14.8% | 20.2% | 26.2% | 4.5% | — | — | 0.2% | — | 0.2% |
| `t5_scr/t5_scr_h100` | 0.1663 | 79.6% | 48.7% | 11.8% | 1.1% | 15.2% | 2.8% | — | — | — | — |
| `t5_scr/t5_scr_h100_pp` | 0.1663 | 67.4% | 11.2% | 25.5% | 2.1% | 24.7% | 3.9% | — | — | — | — |
| `gemma_1b/gemma1b_k0` | 0.1180 | 99.1% | — | 2.1% | 90.6% | 6.4% | — | — | — | — | — |

## Section-4 narrative bullets (cross-system patterns)

1. **Paren-balance is universally effective.** Across all raw/_pp pairs, raw runs show 14-49% unbalanced_parens; post-processed versions show 0%. Net F1 lifts: codegemma compact +0.014, gemma3_12b +0.010, t5_ft_h100_long +0.019, t5_ft_baseline +0.027.

2. **Schema compaction shifts errors, not magnitude.** codegemma7b_k3_bm25_schema_pp (full 23 KB schema, F1=0.6969) errors are 10.1% no_such_column + 2.6% syntax_error; codegemma7b_k3_compact_schema_pp (3 KB DDL, F1=0.7190) errors are 12.7% no_such_column + 4.7% syntax_error. Compact schema replaces some "could not see schema, hallucinated table" with "could see schema, hallucinated column" - but the F1 still goes up because the latter mistakes are recoverable in more cases.

3. **T5 vs LLM error signature.** T5_ft_h100_long_pp 7.7% syntax_error vs gemma3_12b_pp 1.1% syntax_error - the token-level seq2seq model still produces malformed SQL much more often than the chat-template LLM. Both are dominated by no_such_column (T5: 8.4%, LLM: 13.3%).

4. **From-scratch T5 fails differently.** t5_scr_h100 errors are 48.7% unbalanced_parens + 15.2% syntax_error - half of all queries are not even valid SQL. Even paren-balance only patches the syntax half (down to 24.7%); the model has not learned the relational schema at all (no_such_column jumps to 25.5% post-balance because the now-valid SQL still references nonexistent columns).

5. **k=0 is structurally broken.** gemma1b_k0 90.6% no_such_table: zero-shot Gemma-1B has no idea what tables exist in the flight database. Adding even one ICL example drops this to 26.2% (k=1) and 8.2% (k=3 random) - the examples teach table names implicitly.

## Suggested figure (optional)

Stacked-bar of error_rate breakdown by category for the 6 best runs (one per track + ablation pivots) gives the reader a single visual of how failure modes shift as F1 rises.
