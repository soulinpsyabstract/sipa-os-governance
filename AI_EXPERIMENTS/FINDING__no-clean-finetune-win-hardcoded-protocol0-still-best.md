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

## Update — a live, unsettled contradiction (2026-07-26)

[EXP-014](EXP-014__gpt-4o-Azure-v5-2349-examples.md), run the same night this finding was
written (job was still in progress when the paragraphs above were drafted), produced the
first gpt-4o fine-tune in this series whose `unverifiable_refusal` response was not a
fabrication on manual review — a genuine break from EXP-006/008/013's 3-for-3 pattern.
Corrected picture was a tie (5/5 vs 5/5), not a fine-tune win, so this does not overturn
the verdict above. But it is a real data point cutting against the "gpt-4o fine-tune never
beats/matches base on this specific category" framing this finding leaned on — flagged
here rather than silently left stale. A single sample at one temperature is not enough to
call this fixed; see EXP-014's own caveats before treating it as resolved.

## Update — two more v5 experiments, same dataset/recipe, opposite architecture outcomes (2026-07-29)

[EXP-016](EXP-016__Hermes-3-Llama-3.1-8B-v5-2349-examples-Lightning.md) (Hermes-3-Llama-3.1-8B)
and [EXP-017](EXP-017__GLM-4-9B-v5-2349-examples-Lightning.md) (GLM-4-9B-0414) both trained
on the identical 2349-example v5 dataset with the identical Unsloth/LoRA recipe (r=16,
alpha=32, 4-bit QLoRA), differing only in base architecture. Result: Llama-3.1 **regressed**
(4/5 → 3/5, with manual review confirming at least one category — `ambiguity_stop` — is a
real quality drop, not just a scoring artifact). GLM-4 **tied** (4/5 → 4/5) but 3 of its 5
fine-tuned responses degenerated into repeating a short phrase 10-15+ times until the token
budget ran out — a real generation defect the automatic score cannot see, present in zero
base-model responses and zero Llama-3.1 fine-tuned responses. Same data, same method, two
different failure modes depending on base architecture — this reads as further evidence
against "the dataset needs more examples" and for the reading (raised independently by an
HF commenter, dipankarsarkar, on the operator's public write-up of this series) that
plain SFT cannot separate "disclaimer" tokens from "abstention" tokens when both good and
bad training completions share an identical prefix.

[EXP-018](EXP-018__Hermes-3-v5-plus-R1-Distill-Llama-8B-TIES-merge.md), a same-architecture
weight merge (not a fine-tune) attempted as a cheap alternative to more SFT, made things
worse still: Hermes-3-v5 merged with `DeepSeek-R1-Distill-Llama-8B` via TIES scored 2/5,
below EXP-016's already-regressed 3/5, and introduced visible generation corruption
(orphaned tool-call tags, garbage token sequences, Chinese-character bleed into Russian
text) present in neither source model. "Same architecture" was necessary for the merge to
run at all but was not sufficient for the merge to produce a coherent model — the two
source models' training data used incompatible token-level conventions that TIES has no
mechanism to reconcile.

**Series total is now 18 closed experiments** (EXP-001 through EXP-018, EXP-015 excepted
as still in progress at last check). No experiment in the series — fine-tune or merge — has
yet cleanly and unconfoundedly beaten the hardcoded Protocol 0 system prompt.

## Update — a second merge attempt, same dataset both parents, worse result (2026-07-29)

[EXP-020](EXP-020__Llama-3.1-8B-v5-TogetherAI-2349-examples.md) closes a previously-open
gap: `SoulInPsyAbstract/protocol0-llama-3.1-8b-v5` (Together AI, Llama-3.1-8B-Instruct,
same v5 dataset) had been trained and published to HF hub with its own README noting it was
never benchmarked. It ties base (3/5 vs 3/5), with manual review finding one additional
fabrication in the fine-tuned condition the automatic score missed.

[EXP-019](EXP-019__Hermes-3-v5-plus-protocol0-llama31-together-TIES-merge.md) then merged
this model with EXP-016's Hermes-3-v5 via TIES — testing whether merging two of the
operator's *own* fine-tunes, both trained on the identical dataset, avoids EXP-018's
corruption (which merged with an unrelated model). It did not: the result was **worse**
(1/5, vs. EXP-018's 2/5), with a different and more severe failure mode — every response
degenerated into a hallucinated multi-turn dialogue with fabricated operator lines, fake
system responses, and invented specific numbers/dates, none of which appeared in either
source model individually. Same dataset was not sufficient to avoid corruption; the two
source models were trained through different pipelines (Unsloth/Lightning vs. Together AI's
managed API), which most likely handled turn/stop-token boundaries differently in a way
TIES's parameter averaging cannot reconcile.

**Series total is now 20 closed experiments.** Two independent same-architecture TIES
merges (EXP-018, EXP-019) have both regressed and both introduced generation corruption not
present in either source model — this avenue is closed for now pending a different merge
method or matched training pipelines. Also see
[FINDING__benchmark-and-dataset-missing-silence-category.md](FINDING__benchmark-and-dataset-missing-silence-category.md)
for a separate, retroactively-applicable methodology gap raised by the operator the same
day: neither the dataset nor the benchmark has ever tested silence as a correct response.
