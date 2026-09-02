# EXP-037 — misbehavior/correct-behavior binary discriminator, Qwen2.5-7B

**Status: PREPARED, not yet run.** Data, training script, and eval script exist and are
sealed; no GPU has trained anything yet. Written this way deliberately -- a plan is not a
result, and this file says so rather than implying a run happened.

## Why this experiment, and why NOT per-group

Direct follow-up to `AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/misbehavior_incidents_seed_v1.jsonl`
reaching a workable true/false balance (50 BAD : 20 GOOD across the real+synthetic files,
2026-09-02). The project's existing pattern (EXP-031/033/036) is specialist-per-group-then-
merge -- but that needs real volume per group, and this dataset's ~20 true-categories have as
few as 1-2 records each. A per-group split here would be training noise, not signal.

Deliberately a single binary discriminator instead: does the AI-agent behavior described
count as misbehavior (BAD) or correct behavior (GOOD)? One question, all 70 records pooled.

## Zero-shot sanity check, run first, before writing a single line of training code

Before spending any compute, checked whether the signal exists at all: all 70 records (63
real + 7 synthetic), classified zero-shot by `deepseek-chat` via direct API call (no
fine-tuning), same BAD/GOOD system prompt used below. Caught and fixed one leak before
running: several `CORRECT_BEHAVIOR_CONTRAST` records' own summary text opens with "POSITIVE
example, not misbehavior..." -- a literal answer-in-the-prompt. Stripped before scoring.

**Result: 67/70 = 95.7%, against a 71.4% majority-class baseline.** Confusion: TP=50, TN=17,
FP=3, FN=0 -- zero false negatives (never missed a real bad-behavior case), all three errors
were false positives on records already flagged elsewhere in this project as evidentially
weaker (`ANTHROPIC-2026-prototype-stopped-CONTRAST`, `ANTHROPIC-2025-gtg2002-classifier-
response-CONTRAST`, `ANTHROPIC-2024-claude3haiku-no-alignment-faking-CONTRAST` -- an
absence-of-behavior case, harder to read from text alone than an explicit refusal). Signal is
real; this experiment asks whether fine-tuning holds it on a genuinely unseen split, not
whether it exists.

## What's prepared

- `scripts/prep_misbehavior_discriminator_sft.py` -- deterministic stratified split
  (every 5th record per class -> eval), strips the same "POSITIVE example" leak. Output:
  - `misbehavior_discriminator_sft_train_v1.jsonl` -- 56 records (BAD=40, GOOD=16)
  - `misbehavior_discriminator_sft_eval_v1.jsonl` -- 14 records (BAD=10, GOOD=4), never
    touched by the training script
- `scripts/train_misbehavior_discriminator_qwen25.py` -- same convention as
  `train_vuln_specialist_qwen25.py` exactly: Qwen2.5-7B-Instruct, 4-bit, LoRA
  r=16/alpha=32/dropout=0.05, target_modules q/k/v/o_proj+gate/up/down_proj, 3 epochs,
  lr=2e-4. Not a new methodology -- this project's existing standard, reused.
- `scripts/eval_misbehavior_discriminator.py` -- `before`/`after` modes (base model vs.
  base+LoRA), same before/after convention as EXP-036, runs against the 14-record held-out
  eval set only.

## What's NOT done yet

- No GPU instance confirmed/running for this specific job as of this file's writing.
- `before` eval (base Qwen2.5-7B-Instruct, zero-shot, no LoRA) not run.
- Training not run.
- `after` eval not run.
- This file will be updated (not silently rewritten -- Core Law #5) with real before/after
  numbers once a run actually happens, or marked abandoned with a stated reason if it doesn't,
  matching EXP-035's precedent rather than left silently stale.
