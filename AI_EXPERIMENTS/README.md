# AI Experiments Log — SIPA OS

Honest, public record of self-hosted / fine-tuned AI model experiments run under the
Soul In PsyAbstract / SIPA OS project. Consistent with this repo's "honestly, governance,
forensic and zero-trust" charter — results are recorded as measured, including negative
and inconclusive ones. Nothing here is spun for marketing purposes.

## Index

| ID | Date | Base model | Dataset | Result | Status |
|----|------|-----------|---------|--------|--------|
| [EXP-001](EXP-001__DeepSeek-R1-Distill-Qwen-1.5B.md) | 2026-07-21 | DeepSeek-R1-Distill-Qwen-1.5B | 24 synthetic examples | BASE 1/5 vs FT 1/5 — no measurable difference | closed |
| [EXP-002](EXP-002__Qwen2.5-7B-Instruct.md) | 2026-07-22 | Qwen2.5-7B-Instruct | 302 real canon-grounded examples | BASE 4/5 (80%) vs FT 3/5 (60%) — fine-tune measurably worse | closed |
| [EXP-003](EXP-003__Qwen3-235B-A22B-Nebius.md) | 2026-07-20 | Qwen3-235B-A22B-Instruct-2507 (Nebius) | unconfirmed, likely 24 examples | Job succeeded but **unevaluable** — Nebius deprecated LoRA inference deployment, model too large to serve locally | closed |
| EXP-004 | 2026-07-22 | Mistral-7B-Instruct-v0.3 (Lightning L4) | 302 real canon-grounded examples | running | in progress |
| EXP-005 | 2026-07-22 | Llama-3.1-8B-Instruct (Nebius) | 302 real canon-grounded examples | running | in progress |
| EXP-006 | 2026-07-22 | gpt-4o-mini (Azure OpenAI) | 302 real canon-grounded examples | file upload pending | in progress |

## Methodology (shared across experiments)

- **Held-out benchmark**: 5 Protocol-0 behavior categories (ambiguity → STOP, no unsolicited
  opinion, single-action-only, unverifiable-info refusal, conciseness), scored by automatic
  keyword/regex checks, run on BASE model and FINE-TUNED model with identical prompts and
  identical system prompt.
- **No training examples appear in the benchmark** — tests generalization, not memorization.
- Full response text is recorded and reviewed manually in addition to the automatic pass/fail
  score, since keyword-matching can miss semantically-correct-but-differently-phrased responses
  (see EXP-002 for a documented case of this).

## Why this exists

Self-hosted fine-tuning was explored as a path toward "our own model" instead of relying
entirely on commercial AI API tokens. Both experiments so far are documented as run, including
the ones that did not work, so future attempts build on accurate priors instead of folklore.
