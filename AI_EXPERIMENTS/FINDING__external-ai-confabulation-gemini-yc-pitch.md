# Finding: external AI (Gemini) fabricated infrastructure claims from adjacent partnership facts

**Date:** 2026-07-25
**Source:** not one of our fine-tuned models — Google Gemini, used by the operator to draft
YC pitch text based on this repo's live experiment progress.

## What happened

Asked to draft YC application text, Gemini produced: *"Наша инфраструктура развёрнута на
базе AMD MI300X и NVIDIA AI Enterprise."* This is false.

## Ground truth (verified against project state, not memory)

- **AMD MI300X**: SIPA is an approved participant in the AMD/lablab.ai hackathon (Act II,
  deadline 2026-07-11, $10K prize pool). That is program **enrollment**, not deployed
  infrastructure — nothing runs on MI300X in production.
- **NVIDIA AI Enterprise**: an approved evaluation license found in old email
  (2026-07-19), sitting unused in `.sipa_env`. Explicitly "не задействована" — not
  deployed, not integrated, not running anything.
- **Actual infrastructure**: no owned GPU at all. All VPS/VM are CPU-only. Every training
  run in this repo (EXP-010, EXP-011, EXP-012) runs on free-tier Google Colab T4 via a
  custom HTTP bridge — the opposite of "MI300X + AI Enterprise deployment."

## Root cause (operator's diagnosis, confirmed by the facts above)

Gemini had context that SIPA is *in programs/partnerships* with AMD and NVIDIA (hackathon
signup, eval license grant). It then inferred a specific, concrete claim — "infrastructure
deployed on their hardware" — from that adjacency, with **zero actual basis** for that
leap. Program enrollment and an unused eval license are not deployment; nothing in the
source material supported the jump, but the output was stated with full confidence and
no hedge.

## Why this belongs in this repo

This is the exact fabrication pattern this repo has been tracking in our own fine-tuned
models since EXP-002 (confident, plausible-sounding claims built from adjacent-but-not-
equivalent facts, stated as settled rather than flagged as inferred) — see
`FINDING__dataset-gap-ai-not-effective-formula-not-trained.md` and the recurring
"fabrication-under-protocol-language" note in EXP-006/007/008. This is independent
confirmation that the pattern is not specific to small self-hosted models under LoRA —
a large commercial model (Gemini) reproduced the same failure mode on a real task, with
real stakes (this text was headed for an actual YC application before being caught).

## Disposition

Caught before use — not submitted to YC. The AMD/NVIDIA sentence was removed from the
pitch draft; replaced with the honest framing (no owned GPU, training run on free-tier
Colab, a deliberate low-budget constraint, not a deployment claim).
