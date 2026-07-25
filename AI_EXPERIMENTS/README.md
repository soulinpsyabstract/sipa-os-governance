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
| [EXP-010](EXP-010__Mistral-7B-v2-Unsloth-Colab.md) | 2026-07-23 | Mistral-7B-Instruct-v0.3 v2 (Colab T4, Unsloth) | **503** examples (463 + 40 targeting the "AI≠effective" gap) | BASE 2/5 vs FT v2 4/5 (5/5 on manual review) — best result of the series, core fabrication pattern absent on a same-run paired comparison, but confounded by a simultaneous training-stack change (Unsloth) — not proof the dataset fix works | closed |
| [EXP-011](EXP-011__Phi-3.5-mini-v2-Colab-broken.md) | 2026-07-24 | Phi-3.5-mini-instruct v2 (Colab T4, Unsloth) | 503 examples | **Unevaluable** — the unmodified base model itself produced incoherent output and crashed with a CUDA device-side assert (NaN/Inf in sampling probabilities) before the adapter was even involved; training loss never converged either (flat ~7.2-7.7 the whole run) — a broken checkpoint/library combination, not a Protocol-0 result, same category as EXP-005 | closed |
| [EXP-012](EXP-012__Mistral-7B-v3-2199-examples-Colab.md) | 2026-07-25 | Mistral-7B-Instruct-v0.3 v3 (Colab T4, Unsloth) | **1500** examples (503 + CLAUDE-BRIEF + CORE LAW + RED LINE rounds) | Raw automatic score reads as a regression (BASE 3/5 vs FT 2/5), but manual review (mandatory per methodology) finds 3 of the fine-tuned FAILs are keyword-checker false negatives on genuinely correct responses, and the base model's one automatic PASS is a false positive on a real violation — corrected picture matches EXP-010's direction (fine-tuned outperforms base) | closed |
| [EXP-013](EXP-013__gpt-4o-Azure-v3-2199-examples.md) | 2026-07-25 | gpt-4o-2024-08-06 v3 (Azure OpenAI) | **2199** examples (503 + CLAUDE-BRIEF + CORE LAW + RED LINE + macro-pattern rounds) | Raw score ties (BASE 4/5 vs FT 4/5), but manual review finds a genuine, clean fabrication in `unverifiable_refusal` (not a checker artifact) — corrected picture flips to base ahead (~5/5 vs ~3/5). **6th independent confirmation of the disclaim-then-fabricate pattern**, now on a dataset ~4.75x larger than the 463-example set that already targeted this exact category | closed |

## Open findings (not tied to one experiment)

- **[Dataset gap: the session's key RED LINE correction never made it into the v2 training data](FINDING__dataset-gap-ai-not-effective-formula-not-trained.md)** —
  discovered 2026-07-23 by the operator questioning EXP-009's result. The "AI ≠ effective,
  AI = practical, zero-deviation execution" formula, the single most emphatic correction
  given this session, has **zero matches** in the 463-example dataset both EXP-008 v2 and
  EXP-009 v2 were trained on. Neither v2 experiment's benchmark result says anything about
  this specific category — it was never in scope of what the model actually saw in training.
- **[External AI (Gemini) fabricated infrastructure claims from adjacent partnership facts](FINDING__external-ai-confabulation-gemini-yc-pitch.md)** —
  2026-07-25, caught before submission in a YC pitch draft. Independent confirmation, on a
  large commercial model outside this repo's own fine-tunes, of the same
  confident-fabrication-from-adjacent-facts pattern tracked throughout this series.
- **[No fine-tune has cleanly beaten the hardcoded Protocol 0 system prompt](FINDING__no-clean-finetune-win-hardcoded-protocol0-still-best.md)** —
  2026-07-25, synthesis across all 13 closed experiments, prompted by the operator asking
  directly whether SIPA has "its own AI" beyond the hardcoded prompt. Honest answer: no —
  every apparent fine-tune win in this series is confounded by a simultaneous stack change,
  and gpt-4o specifically has lost to (or tied) its own base+prompt version 3 times running
  as the dataset grew from 302 to 2199 examples.

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
