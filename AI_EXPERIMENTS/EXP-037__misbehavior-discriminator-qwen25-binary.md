# EXP-037 — misbehavior/correct-behavior binary discriminator, Qwen2.5-7B

**Status: RUN. Result: no measurable effect on the held-out set, and that's reported
honestly, not spun.** GPU: Brev/massedcompute L40S (`content-black-cattle`), woken
2026-09-02 specifically for this experiment.

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

## What actually ran

One bug caught and fixed before training would even start: `train_misbehavior_discriminator_qwen25.py`
was copied from `train_vuln_specialist_qwen25.py`'s exact convention, including
`SFTConfig(..., max_length=768, ...)` -- but this project's pinned `trl==0.12.2` doesn't
accept that kwarg; the parameter is `max_seq_length` in this version. Confirmed directly via
`inspect.signature` on the installed package rather than guessing. Fixed, re-ran.

**BEFORE** (base Qwen2.5-7B-Instruct, zero-shot, no LoRA): **13/14 = 92.9%**. TP=9 TN=4 FP=0
FN=1. The one miss: `ANTHROPIC-2026-april-rl-environment-audit` (BAD, predicted GOOD) -- a
genuinely subtle case, Anthropic auditing its own RL training environments and admitting
>10% were flagged for reward-hacking, which reads less like a discrete misbehavior incident
and more like a self-critical process disclosure.

**Training**: 56 examples, 3 epochs, 21 steps, ~35 seconds on the L40S. Loss 3.46 -> 1.86.
Real learning happened on the training set -- verified directly, not assumed: after training,
`lora_B` weights were fully nonzero (57,344/57,344 elements, abs-sum=40.16), not the
zero-initialized default PEFT ships with. The adapter genuinely changed.

**AFTER** (base + trained LoRA): **13/14 = 92.9%** -- identical to BEFORE. Checked
programmatically, not eyeballed: every one of the 14 per-record predictions matches BEFORE
exactly, same single miss on the same record. TP=9 TN=4 FP=0 FN=1, unchanged.

**What this means, stated plainly rather than smoothed into either "it worked" or "it
failed"**: the LoRA adapter learned real weight changes on the training data (loss dropped,
`lora_B` populated), but produced zero measurable behavior change on this specific 14-record
held-out set. Most likely reading: the base model was already near-ceiling on this task (92.9%
before training, close to the 95.7% zero-shot DeepSeek result from the sanity check that
started this whole experiment) -- 14 held-out examples is too small a set for a marginal
improvement to show up as a flipped prediction, and 56 training examples may not carry enough
signal for a 40M-parameter LoRA to shift a decision this close to already-correct. Not ruled
out and not claimed either: this result does not distinguish "the LoRA has no effect" from "the
LoRA has a small effect this eval set is too small to detect." A larger eval set (more of the
misbehavior dataset held out, or the disjoint `misbehavior_synthetic_contrast_v1.jsonl` records
not yet used anywhere in this split) would be the next real test, not re-running the same
14 records and hoping for a different outcome.

Raw results: `EXP-037_eval_results_before.json` / `EXP-037_eval_results_after.json` in this
same directory, copied off the GPU instance and sealed -- not left stranded on an ephemeral
box, per this project's own data-loss-prevention discipline (the same one EXP-035 lost a
baseline run to).

## Real, unaddressed gap: this is single-shot greedy, not repeated sampling

Caught by the architect directly, not self-caught: both eval runs used `do_sample=False`,
one deterministic generation per record. That is a real methodological step down from this
project's own established convention -- `EXP-036`'s "n=10 repeated sampling, temperature=0.7"
and the `bench_base_k20.py` family used elsewhere in this repo exist specifically because a
single greedy pass on one prompt cannot distinguish "the model reliably gets this right" from
"it happened to land on the right token this one time." A single BAD/GOOD verdict per record,
run once, is not evidence of calibrated accuracy -- the same prompt at temperature could come
back GOOD five times and BAD once, or the reverse, and 92.9%/92.9% from one greedy pass each
would never reveal that.

This means the headline numbers in this file -- 13/14 BEFORE, 13/14 AFTER, identical -- are
each a single sample, not a rate. The "identical predictions" finding is still real (both runs
used the same deterministic decoding, so at minimum the comparison between BEFORE and AFTER is
apples-to-apples) but neither number should be read as "the model's true accuracy on this task
is 92.9%" -- that would require the same k=10-or-k=20 repeated-sampling methodology already
standard in this project, not a new one invented for this file. Not run here, not claimed as
run. The honest fix, next time this experiment is picked back up: n=10+ samples per record at
temperature=0.7 (matching EXP-036's own precedent exactly), majority-vote or full-distribution
reporting per record, for both BEFORE and AFTER -- on a GPU instance, not retroactively
recoverable from the single-sample results already saved here.
