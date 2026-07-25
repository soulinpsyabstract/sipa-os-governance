# Finding: no fine-tune in this series has cleanly beaten the hardcoded Protocol 0 system prompt

**Date:** 2026-07-25
**Scope:** synthesis across all 13 closed experiments in this series (EXP-001 through
EXP-013), prompted by the operator directly asking whether SIPA has "its own AI" beyond
the hardcoded Protocol 0 system prompt.

## The honest answer

**No.** As of this writing, no fine-tuning run in this repo has produced a model that
cleanly, unconfoundedly outperforms the same base model driven by the Protocol 0 system
prompt alone. "SIPA's own AI" today is a hardcoded instruction layer on top of commercial
base models (gpt-4o, Mistral, Qwen, etc. via their respective APIs), not a set of
independently trained weights that beat the base.

## What the 13 closed experiments actually show

| Result | Experiments |
|---|---|
| No measurable difference | EXP-001 |
| Fine-tune measurably worse | EXP-002, EXP-006, EXP-008, EXP-013 |
| Unevaluable (broken run) | EXP-003, EXP-005, EXP-011 |
| Tie (raw or corrected) | EXP-007, EXP-009 (confounded) |
| Fine-tune better, but confounded | EXP-004, EXP-010 (simultaneous stack changes) |
| Fine-tune better, corrected picture | EXP-012 (~4/5 vs ~1/5, best result of the series — but same Unsloth-stack confound as EXP-010 carries through its lineage) |

No experiment isolates "dataset content" as the only changed variable while also holding
training stack, base model, and infrastructure constant — every apparent win has at least
one other simultaneous change that could explain the result instead of the dataset.

## gpt-4o specifically: hardcoded prompt wins, 3 for 3

Every gpt-4o fine-tune attempted (EXP-006, EXP-008, EXP-013) either regressed or tied
against the same base model driven only by the system prompt. This is the model family
tested the most times in this series (dataset sizes 302 → 463 → 2199 examples), and the
result has not moved in the fine-tune's favor as the dataset grew roughly 7x. The
recurring specific failure — a fabricated, confidently-stated number after an explicit
"I won't guess" disclaimer in the `unverifiable_refusal` test category — reproduced on
gpt-4o's v3 fine-tune worded almost identically to the very first instance of this pattern
in EXP-002, on a dataset with 36+ examples specifically written to target this exact
scenario.

## Practical implication

Prompt-level hardcoding (Protocol 0 as a system prompt) is, right now, the more reliable
mechanism for enforcing these behaviors than baking the same rules into model weights via
LoRA/QLoRA at the dataset scale tested so far (up to 2349 examples). This is not a
permanent verdict — see "What would change this" below — but it is the honest state of
the evidence today, and matches this repo's charter to not spin negative or inconclusive
results as positive.

## Best remaining candidate, and what a clean test would require

**Mistral-7B** is the only base model where the corrected (manually-reviewed) picture has
twice shown a clear fine-tune advantage (EXP-010, EXP-012). A methodologically clean
follow-up would need:

1. A single training stack held constant across a `dataset size A` vs `dataset size B`
   comparison (no simultaneous Unsloth/library version changes).
2. The full current dataset (2349 examples as of this writing) run end-to-end without a
   credit-exhaustion interruption — the most recent Mistral-family v5 attempt (Hermes-3-
   Llama-3.1-8B, technically a different base model but same v5 dataset and training
   script family) was cut off at ~87% by Lightning credit exhaustion; see the
   `STATUS__2026-07-25.md` "Hermes-3-Llama-3.1-8B v5 stopped by Lightning credit
   exhaustion" section.
3. Continued manual review of every benchmark response, not just the automatic
   keyword-match score — every single experiment in this series that included manual
   review found the automatic score misleading in at least one direction.

## What would change this verdict

- A clean, single-variable dataset-size comparison on one fixed training stack.
- A larger, more targeted dataset specifically covering the `unverifiable_refusal`
  fabrication pattern (current dataset growth added governance-structure examples —
  CLAUDE-BRIEF rules, CORE LAW, RED LINE, macro-patterns — not more examples of this
  specific failure mode; see EXP-013's "what this does and doesn't show" section for the
  same observation).
- Successfully completing and benchmarking the currently-stalled v5 queue (Hermes-3-
  Llama-3.1-8B pending Lightning credit top-up; Llama-3.1-8B and Qwen2.5-7B via Together
  AI trained but benchmark-blocked on inference access; GLM-4-9B and Gemma-2-9B with no
  working platform found yet).
