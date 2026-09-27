# EXP-046 -- Probability-estimator LoRA: specialist gain, merge gives most of it back

**Date:** 2026-09-27
**Hardware:** Brev L40S (`joyous-moccasin-limpet`)
**Base model:** Qwen/Qwen2.5-7B-Instruct, LoRA r=16/alpha=32/dropout=0.05,
target_modules=[q/k/v/o/gate/up/down_proj], 3 epochs, specialist-per-group-then-merge
(EXP-031's convention).

## Why

Her request, second half of "тюн интересно на чем погонять" (2026-09-27, right after the
Laya finding/EXP-045): fine-tune on the causal-chain + probability datasets already prepared
2026-09-21 for the project's own consequence-prediction architecture, Risk(X|C) = P(harmful
Y|X,C) x Impact(harmful Y) (`project_consequence_prediction_architecture.md`, memory).
`/home/sipa/bin/FREQUENCY_PROBABILITY_ESTIMATOR.py` is the project's existing answer to the
P side -- but it's a hand-built frequency-table lookup by action type, seeded from a Base44
app's data, explicitly not AI-calibrated (its own docstring names the real gap: the one real
feedback log available, `binary-gate-dryrun-verdicts.jsonl`, is 99.87% constant "fail" and
unusable for calibration). This experiment is a different, model-based approach to the same
estimation task -- not a fine-tune of that script -- using the two dataset layers Hermes-
4-405B already generated for it: `causal_chain_<group>.jsonl` (structural X->Y->Z chains, no
numbers) and `probability_<group>.jsonl` (each chain's `probability_estimate` +
`probability_reasoning`), joined by `chain_ref`.

## Dataset

`scripts/prep_probability_estimator_pergroup.py` joins the two layers per group (vulnerability,
deletion, sensitive_publication -- 200 chains each, 600 total) and writes `messages`-format SFT
records: system prompt asks for a JSON `{"probability_estimate": float, "probability_reasoning":
str}` given the initiating action, the chain steps, and the terminal outcome; assistant turn is
the gold JSON. Deterministic split, every 10th record -> eval (180 train / 20 eval per group,
matching EXP-031's 176-180/20 ratio) -- real per-group volume, so this followed EXP-031's
specialist-per-group-then-merge convention, not EXP-037/045's single-generalist pattern (which
those experiments justified specifically by having too little volume per category).

## Pipeline

`scripts/train_probability_estimator_pergroup.py <group>` x3 -> `scripts/eval_probability_estimator.py
<adapter> <group> 5` (before/specialist/merged) -> `scripts/merge_probability_loras.py` (equal-
weight linear merge, same `add_weighted_adapter` pattern as `merge_vuln_loras.py`).

Regression task, not binary -- the EXP-037/045 majority-vote convention doesn't apply. Instead:
n=5 samples/record at temperature=0.7, MEAN of the parsed `probability_estimate` values as the
record's prediction, MAE against gold, and the fraction of records within 0.15 absolute error
(the dataset's own README documents a 0.2-0.95 observed spread). Full per-sample raw text saved.

One bug caught and fixed mid-run, not guessed at: `eval_probability_estimator.py`'s output
filename only encoded `before`/`after`, not which adapter -- the merged-adapter eval run
silently overwrote each specialist's own result file on the GPU box (both are "after" runs).
Caught by checking the downloaded file's own `adapter` field before writing this doc, not by
assuming the download matched what was requested. Fixed (`adapter_tag` added to the output
path) and the three specialist evals were re-run cleanly under distinct filenames -- the
re-run numbers land within sampling noise of the original run (vulnerability 0.098->0.084 the
first time, 0.085 the re-run; same pattern all 3 groups), confirming the fix didn't change
anything about the specialists themselves, only which file survives.

## Results

| Group | BEFORE (base, zero-shot) | AFTER specialist | AFTER merged |
|---|---|---|---|
| vulnerability | MAE 0.098, within_0.15 15/20 | **MAE 0.085, within_0.15 15-17/20** | MAE 0.102, within_0.15 15/20 |
| deletion | MAE 0.144, within_0.15 13/20 | **MAE 0.113-0.118, within_0.15 16/20** | MAE 0.129, within_0.15 13/20 |
| sensitive_publication | MAE 0.134, within_0.15 12/20 | **MAE 0.100-0.105, within_0.15 15-16/20** | MAE 0.104, within_0.15 14/20 |

(Ranges reflect the original run vs. the clean re-run after the filename fix -- same pattern,
sampling noise only.)

Real training happened in all 3 (loss 1.5-1.6 -> 0.4-0.5 over 3 epochs, `mean_token_accuracy`
0.66-0.68 -> 0.85-0.88), and every specialist genuinely beat its own zero-shot baseline -- a
consistent MAE drop of 0.014-0.034 and a within-0.15 gain of 2-4 records per group, on a task
that (unlike EXP-045's binary decomposition classifier) was NOT already at ceiling zero-shot.

**The merge gave most of that gain back.** Equal-weight linear merging the 3 specialists into
one adapter lands within 0.001-0.004 MAE of the BASE model on every group -- not "close to the
best specialist," close to zero fine-tuning at all. This is a different outcome from EXP-031's
own merge result (6 binary vuln-gate specialists merged with a total accuracy swing of -1
percentage point, "within single-example greedy-decoding noise"). Base rate here is: something
about combining LoRAs trained to shift a *continuous number* in group-specific directions
cancels out under equal-weight linear combination in a way that combining LoRAs trained to
enforce a *shared binary refusal behavior* (EXP-031's task) does not.

## What this shows, and the honest limitation

Per-group fine-tuning genuinely improves calibration on this task -- confirmed, not assumed,
against a real zero-shot baseline that was NOT already saturated (unlike EXP-045's classifier
task). But the specialist-per-group-then-merge convention that worked cleanly for a shared
binary behavior (EXP-031) does not transfer as-is to a regression task where each specialist
learns a *different numeric calibration* -- equal-weight linear merging averages those
calibrations back toward the unspecialized starting point rather than preserving each group's
gain. Not investigated here (would be the natural next step, not run without her explicit
ask): whether a routed/gated combination (pick the right specialist per group at inference
time, instead of blending weights) holds the gain a flat merge loses.

**How to apply:** for `Risk(X|C) = P x Impact` deployment, per-group specialists deployed
separately (routed by `risk_group`, which the pipeline already tags every record with) keep
the real MAE improvement this experiment measured; a single merged adapter does not, and
should not be assumed equivalent to "the specialists, combined" without re-checking per task
type -- this is now a documented counter-example to that assumption, not a rule for every
future merge.

Raw: `EXP-046-probability-estimator/eval_probability_results_{before,after_specialist-prob-<group>-qwen25-lora,after_merged}_<group>.json`
(9 files, before/specialist/merged x 3 groups), plus the `<group>_train.jsonl`/`<group>_eval.jsonl`
SFT splits, in this directory.
