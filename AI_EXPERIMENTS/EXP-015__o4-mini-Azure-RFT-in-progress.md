# EXP-015 · o4-mini + Reinforcement Fine-Tuning (Azure OpenAI) — IN PROGRESS

**Date:** 2026-07-26
**Status:** in progress — this file is being written while the job runs, not after
completion, per this repo's charter of documenting honestly rather than only after a
clean result is known.

## Why this is different from EXP-001 through EXP-014

Every prior experiment in this series used **supervised fine-tuning (SFT)**: the model is
shown example (prompt, target completion) pairs and trained to reproduce them. This
experiment uses **reinforcement fine-tuning (RFT)** instead: the model is given only
prompts, generates its own responses during training, and a separate **grader** scores
each response — the model is optimized to maximize the grader's score, not to match a
fixed target completion. This is a different mechanism for the same underlying question
this series has been asking: can Protocol 0's behavioral rules survive being baked into a
model's weights, rather than kept in a system prompt.

## Setup

- **Base model:** `o4-mini-2025-04-16`, Azure OpenAI's only fine-tunable reasoning model
  on this resource. Confirmed via live API check that `o4-mini` and `gpt-35-turbo` are the
  only fine-tunable models besides `gpt-4o-2024-08-06` (already used in EXP-006/008/013/014)
  — `o4-mini` does **not** support standard SFT at all; the API rejects a normal
  fine-tuning request with `"Finetuning with o4-mini-2025-04-16 requires the reinforcement
  method of finetuning."`
- **Dataset conversion:** derived from `protocol0_sft_v3_full.jsonl` (2349 examples, the
  same dataset EXP-014 used). Each SFT row's `(system, user, assistant)` triple was split:
  the `user` message becomes the RFT prompt, and the original `assistant` completion is
  kept as a `reference_answer` field for the grader to compare against — **not** used as a
  training target directly. **System messages had to be stripped entirely** — Azure's RFT
  endpoint rejects any training example containing a `system` role
  (`"System messages are not supported in 'reinforcement' examples"`), discovered via a
  failed first attempt (see "What went wrong on the first try" below). This means the
  Protocol 0 rules are not shown to the model during RFT training turns at all — they are
  only present inside the grader's own instructions, and the model must learn the
  behavior purely from the reward signal, not from being told the rules directly. Split
  95/5 into 2231 training / 118 validation examples (well under Azure's 50,000/1,000 caps).
- **Grader:** a `score_model` grader — a separate call to `gpt-4o-2024-08-06` that reads
  the model's generated response plus the `reference_answer`, and returns a 0.0-1.0 score
  based on Protocol 0 compliance (no fabrication, no unsolicited opinion, stop-on-ambiguity,
  single-action-only, concise). This reuses the same criteria this series' benchmark script
  has checked automatically since EXP-002, just as a training signal instead of a
  post-hoc evaluation.
- **Job:** `ftjob-c24fd461d0d7443d94ae16f0586a79bf`, suffix `protocol0-rft-v1`,
  `estimated_finish` ~6 hours from submission — RFT trains by generating and grading many
  rollouts per example, and is inherently much slower than SFT's single forward/backward
  pass per example; this is expected, not a stall.

## What went wrong on the first try (kept here, not silently fixed)

The first submission attempt also surfaced a real operational mistake worth recording
plainly: while probing which Azure `api-version` supports the RFT `method` field, three
separate job-creation requests were sent across different preview API versions without
stopping at the first success, because the older versions returned clean-looking errors
that looked like "this version doesn't support it" rather than being recognized as
successes on the newer ones. This created **three simultaneous duplicate RFT jobs**
before the mistake was caught. Two were cancelled immediately
(`ftjob-60578856527e47f29338fd5fc351979d`, `ftjob-679fb81f9eb840a0b4a6848d7837c5b0`); the
third (`ftjob-2995a0739cb94c97a7e7c5b5d770aef2`) was left running as the "kept" one — but
it then failed on file preprocessing (the system-message rejection described above) before
any real training cost was incurred, once cancellation of the duplicates was confirmed
working (the Azure `cancel` endpoint requires an explicit `Content-Length` — a bare `-X
POST` with no body triggers an HTTP 411 and silently fails to cancel, which cost a few
minutes of investigation before finding the fix: pass an explicit JSON body, even just
`{}`).

## What this will and won't show once it completes

- **Will show:** whether reward-based training on the *same* dataset content this series
  has already SFT-tuned on produces different fabrication-pattern behavior than the SFT
  line's gpt-4o results (EXP-006/008/013/014) — a genuinely different training mechanism,
  not just a different base model.
- **Will not show:** a clean comparison to the SFT line, since multiple things differ
  simultaneously (base model family — o4-mini is a reasoning model, not gpt-4o; training
  mechanism — RFT vs SFT; and the training data no longer includes the system prompt
  context that SFT examples had). Any result here should be read as its own data point,
  not a controlled ablation against the rest of the series.
- **Benchmark plan once complete:** same 5-category methodology as every other experiment
  in this series (`ambiguity_stop`, `no_unsolicited_opinion`, `single_action_only`,
  `unverifiable_refusal`, `conciseness`), run against base `o4-mini-2025-04-16` and the
  fine-tuned deployment, with mandatory manual review of every response before reporting
  a score — per this repo's own repeatedly-confirmed finding that the automatic keyword
  checker is unreliable in both directions.

This file will be updated (not silently rewritten) once the job reaches a terminal state.

## Update — second attempt also failed, different reason (2026-07-26)

After fixing the system-message format issue, the resubmitted job
(`ftjob-c24fd461d0d7443d94ae16f0586a79bf`) failed again, this time for a substantively
different reason:

```
unsafe_file: The job failed due to an unsafe training file. This training file was
blocked because too many examples were flagged by our moderation for content that
violates Azure OpenAI's usage policies with respect to model reasoning extraction.
Please review the data and remove potential offending examples before retrying
fine-tuning.
```

**This is a content-moderation block, not a format error** — Azure's RFT pipeline appears
to specifically screen for training data that resembles attempts to distill/extract a
reasoning model's chain-of-thought (a known industry concern with o-series models). This
dataset's governance-heavy content — CORE LAW, RED LINE prohibitions, macro-pattern
rounds about refusal boundaries and security — plausibly triggered this at scale, though
Azure's error does not identify which specific examples were flagged, so this is
diagnosis by plausibility, not confirmed cause.

**Status: blocked, pending a decision on how to proceed** — options not yet chosen
between:
1. Filter the dataset for content most likely to trigger this policy (RED LINE/security-
   framed examples specifically) and retry with a smaller, non-governance subset.
2. Abandon the o4-mini RFT attempt and treat EXP-015 as closed-unevaluable (same category
   as EXP-003/005/011 — job blocked before any real training happened, not a Protocol-0
   result).
3. Try a different reasoning-capable model or platform for RFT instead of Azure's o4-mini.

No further Azure fine-tuning jobs were submitted after this failure pending that decision
— avoiding a repeat of the earlier duplicate-job mistake by not retrying blindly.
