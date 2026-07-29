# Finding: neither the v5 dataset nor the benchmark suite tests for silence as a correct response

**Date:** 2026-07-29
**Raised by:** operator, mid-session, reviewing EXP-016/017/018

## The gap

Protocol 0's actual behavioral standard (the same standard the operator holds the
assistant layer to directly, not only the fine-tuned models) includes at least two rules
that neither `protocol0_sft_v3_full.jsonl` nor `benchmark_protocol0_*.py` test at all:

1. **If told not to respond / to stop, the correct response is zero words — not a worded
   refusal.** Every one of the benchmark's five categories, and every training example in
   the dataset, expects some text output. `grep '"assistant":\s*""' protocol0_sft_v3_full.jsonl`
   returns **zero matches** — there is not one training example across 2349 rows where the
   correct assistant turn is an empty string. The dataset has never once demonstrated
   silence as an outcome, only ever "STOP" *worded* as text.
2. **No templated or formulaic phrasing, and no answering for the sake of answering** — the
   benchmark's `STOP_MARKERS`/`OPINION_MARKERS` keyword lists actively reward specific
   *phrases* ("не могу проверить", "уточните", etc.), which is structurally in tension with
   penalizing template-shaped language: a model that learns to always emit one of these
   exact stock phrases would score well on every category while becoming *more* templated,
   not less.

## Why this matters for the whole series retroactively

Every experiment in this series (EXP-001 through EXP-018) was scored against a benchmark
that could not have detected either of these failure modes even if a fine-tune had
regressed on them, because passing requires producing *some* text, and no category
penalizes stock phrasing. It is possible — untested, not claimed here as established —
that some or all of the fine-tunes in this series made models *more* likely to answer
when silence was correct, or *more* templated in phrasing, while still scoring well or
tying on the existing 5 categories. The existing benchmark is structurally blind to this.

## What would close this gap

- **Dataset**: add training examples where the correct assistant turn is genuinely empty
  or near-empty (not a worded refusal) for prompts that are explicit "stop"/"don't
  respond" instructions from the operator — currently absent entirely.
- **Benchmark**: add a test category using a prompt that explicitly instructs
  non-response (e.g. a direct "не отвечай на это" style instruction) and scores PASS only
  on an empty or near-empty completion, FAIL on any substantive text regardless of
  content.
- **Benchmark**: add a template-detection check — e.g. flag/penalize exact repetition of
  the checker's own keyword phrases across responses, since the current design can be
  gamed by a model that just always says the same stock phrase.

## Status

Not yet implemented in either the dataset or the benchmark scripts — flagged here as an
open methodology gap discovered by direct operator review, not yet acted on. None of
EXP-001 through EXP-018 should be read as having tested for this, positively or
negatively — it is simply outside what those experiments measured.
