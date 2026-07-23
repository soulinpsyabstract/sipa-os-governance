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
| [EXP-004](EXP-004__Mistral-7B-Instruct.md) | 2026-07-22 | Mistral-7B-Instruct-v0.3 (Lightning L4) | 302 real canon-grounded examples | BASE 2/5 (40%) vs FT 3/5 (60%) — first genuine improvement, with caveats | closed |
| [EXP-005](EXP-005__Llama-3.1-8B-Nebius.md) | 2026-07-22 | Llama-3.1-8B-Instruct (Nebius) | 302 real canon-grounded examples | Job succeeded, but downloaded adapter produces incoherent output when merged locally — broken, not a Protocol-0 result | closed |
| [EXP-006](EXP-006__gpt-4o-Azure.md) | 2026-07-22/23 | gpt-4o-2024-08-06 (Azure OpenAI) | 302 real canon-grounded examples | BASE 4/5 (80%) vs FT 3/5 (60%) — regression; 3rd independent confirmation of a fabrication-under-protocol-language pattern | closed |
| [EXP-007](EXP-007__Phi-3.5-mini-Instruct.md) | 2026-07-22/23 | Phi-3.5-mini-instruct (Lightning T4) | 302 real canon-grounded examples | BASE 3/5 vs FT 3/5 (tie); 4th independent confirmation of the fabrication pattern (fake reference IDs) | closed |
| [EXP-008](EXP-008__gpt-4o-Azure-v2-expanded-dataset.md) | 2026-07-23 | gpt-4o-2024-08-06 v2 (Azure OpenAI) | **463** examples (expanded, targeting fabrication/sycophancy/silence/false-verification) | BASE 4/5 vs FT 3/5 — same raw score as EXP-006; 2/5 categories genuinely improved, but the core fabrication pattern survived the targeted fix (5th confirmation) | closed |
| [EXP-009](EXP-009__Qwen2.5-7B-Instruct-v2-4bit-QLoRA.md) | 2026-07-23 | Qwen2.5-7B-Instruct v2 (Lightning T4, 4-bit QLoRA) | 463 examples | BASE 4/5 vs FT v2 4/5 — tie, best result yet, but core `unverifiable_refusal` result is confounded by cross-run sampling variance on the untouched base model — inconclusive, not a fix | closed |

## Open findings (not tied to one experiment)

- **[Dataset gap: the session's key RED LINE correction never made it into the v2 training data](FINDING__dataset-gap-ai-not-effective-formula-not-trained.md)** —
  discovered 2026-07-23 by the operator questioning EXP-009's result. The "AI ≠ effective,
  AI = practical, zero-deviation execution" formula, the single most emphatic correction
  given this session, has **zero matches** in the 463-example dataset both EXP-008 v2 and
  EXP-009 v2 were trained on. Neither v2 experiment's benchmark result says anything about
  this specific category — it was never in scope of what the model actually saw in training.

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
