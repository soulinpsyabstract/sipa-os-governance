# Style curriculum dataset (EXP-044, stage10)

Generated 2026-09-17 via `nb-hermes405` (Hermes-4-405B, direct Nebius endpoint), per the architect's explicit
direction after stage9's math-eval and safety-eval both showed the model over-elaborating with
unrequested, wrong reasoning chains (invented Bayesian-update steps injected into plain risk
questions and into G15 safety scenarios) instead of executing directly. Targets the response
*format* itself -- terse, cold, algorithmic execution -- as distinct from the *content* topics
the math-curriculum datasets cover.

Four groups, ~50 pairs each, one style axis per group (not a topic sequence -- trained together
as a single stage, not staged one-per-group like the math curriculum):

| File | Pairs | Axis |
|---|---|---|
| `no_sycophancy.jsonl` | 49 | Disagree/confirm plainly on a flawed or debatable idea, no flattery, no validation-for-its-own-sake |
| `no_unsolicited_advice.jsonl` | 55 | Answer exactly what was asked, no extra suggestions/caveats/offers to do more |
| `no_emotional_language.jsonl` | 48 | Answer the factual/actionable part of an emotionally-framed message with zero emotional acknowledgment |
| `terse_direct_execution.jsonl` | 49 | No preamble, no postamble, no restating the task, minimum work shown |

`cold_no_sycophancy_style.jsonl` (201 pairs, shuffled) is the combined training file used for
stage10.

Format: JSONL, each line `{"instruction": ..., "response": ...}`.

See `EXP-044__hermes3-8b-governance-8stage-curriculum-tune-vs-catastrophic-forgetting.md` (one
directory up) for the full experiment writeup and stage10 results.
