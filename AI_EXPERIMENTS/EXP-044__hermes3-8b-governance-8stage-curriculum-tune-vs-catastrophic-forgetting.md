# EXP-044 — Hermes-3-8B security specialist, 8-stage curriculum-split governance tune (direct follow-up to EXP-043)

**Status: IN PROGRESS — identity_bio (stage 3 candidate) FAILED badly, rolled back, retrying with governance_protocol_safety_a. Updated live, stage by stage, per architect's explicit instruction ("сырые ответы сразу документируй и пуш после проверки чтобы не забывалось")**

## Context

Direct follow-up to EXP-043, which found catastrophic forgetting (97%→63%
overall, uniform -28 to -37pp across all 6 adversarial-eval groups) from
continue-training the security specialist on all 881 governance Q&A pairs
in a single 3-epoch blob. The architect's hypothesis, drawn from her own
prior finding (specialist-per-group-then-merge outperforming mass-merge in
EXP-031/036, and a direct analogy to human curriculum learning — "дети
учатся 12 лет, врачи 7+, никто не пихает весь объём данных в одно рыло, а
равномерно, с домашними заданиями"): a large, topically heterogeneous tune
should be split into smaller, thematically coherent stages, each evaluated
before moving to the next, rather than dumped in one go.

## Method

- **Starting point:** `SoulInPsyAbstract/hermes3-8b-sequential-chain-lora`
  (same candidate that regressed in EXP-043), continue-trained sequentially
  (`PeftModel.from_pretrained(..., is_trainable=True)`, no merge — same
  mechanism as EXP-042's chain, `train_stage.py`)
- **Dataset split:** the same 881-pair `sipa_os_finetune_dataset.jsonl`,
  classified into thematic groups via keyword heuristic (business/legal/
  finance, infra/devops, governance/protocol/safety, external research,
  architecture/system, identity/bio), with the two largest groups
  (infra_devops, governance_protocol_safety) further split in half per the
  architect's explicit instruction ("infra и говернанс объёмны, лучше
  разбей на 2 — лишний тюн лучше и безопаснее чем тонна данных"):

| Stage | Group | Pairs |
|---|---|---|
| 1 | external_research | 42 |
| 2 | architecture_system | 51 |
| 3 | business_legal_finance | 52 |
| 4 | identity_bio | 178 |
| 5 | governance_protocol_safety_a | 108 |
| 6 | governance_protocol_safety_b | 108 |
| 7 | infra_devops_a | 171 |
| 8 | infra_devops_b | 171 |

- **Training config per stage:** identical to EXP-043 (LoRA rank 16/alpha
  32/dropout 0.05, 7 projections, 3 epochs, lr 2e-4, bf16) — the only
  variable changed between EXP-043 and this run is the granularity of the
  tune (1 blob vs 8 sequential stages), not the hyperparameters, to isolate
  that variable specifically.
- **Eval after every stage:** same harness as EXP-042/043
  (`eval_vuln_gate_v2_hermes3.py`, 120 scenarios/6 groups, n=10, judge_v4) —
  full re-run of the adversarial-refusal benchmark after each stage, not
  just at the end, to catch the point of failure (if any) as it happens.
- **Hardware:** same Brev L40S instance as EXP-043 (`prickly-white-pigeon`)

## Baseline (unchanged from EXP-043)

| Group | Before (candidate, n=10) |
|---|---|
| 01_secrets_credentials | 196/200 (98%) |
| 02_access_control | 193/200 (96%) |
| 03_injection | 193/200 (96%) |
| 04_infra_misconfig | 192/200 (96%) |
| 05_supply_chain | 193/200 (96%) |
| 06_stop_gate_pressure | 196/200 (98%) |
| **OVERALL** | **1163/1200 (97%)** |

## Stage results (appended live as each stage completes)

### Stage 1 — external_research (42 pairs)

Training: `train_loss` not logged in this run's excerpt (fast run, 9
steps); model ready in ~2s load, training in ~12s wall.

| Group | Result |
|---|---|
| 01_secrets_credentials | 199/200 (100%) |
| 02_access_control | 190/200 (95%) |
| 03_injection | 187/200 (94%) |
| 04_infra_misconfig | 181/200 (90%) |
| 05_supply_chain | 186/200 (93%) |
| 06_stop_gate_pressure | 189/200 (94%) |
| **OVERALL** | **1132/1200 (94%)** |

**Δ vs baseline: -3pp overall.** Healthy — nothing resembling EXP-043's
uniform catastrophic collapse. This establishes the ~3-8pp per-group band
as the reference for "normal fluctuation" for the remainder of this
experiment.

### Stage 2 — architecture_system (51 pairs)

Training: `train_loss` 1.805, `mean_token_accuracy` 76.75%, 12 steps, ~13s
wall, continuing from stage 1's output.

| Group | Result | Δ vs baseline | Δ vs stage 1 |
|---|---|---|---|
| 01_secrets_credentials | 174/200 (87%) | -11pp | -13pp |
| 02_access_control | 174/200 (87%) | -9pp | -8pp |
| 03_injection | 155/200 (78%) | -18pp | -16pp |
| 04_infra_misconfig | 154/200 (77%) | -19pp | -13pp |
| 05_supply_chain | 161/200 (80%) | -16pp | -13pp |
| 06_stop_gate_pressure | 172/200 (86%) | -12pp | -8pp |
| **OVERALL** | **990/1200 (82%)** | **-15pp** | **-12pp** |

**Δ vs stage 1: -12pp overall, uniform -8 to -16pp across all 6 groups.**
This exceeds the ~3-8pp normal-fluctuation band stage 1 established as the
reference. Not a catastrophic collapse on the scale of EXP-043 (63%
overall, -34pp in one shot) — but a real, uniform-across-all-groups
regression in a single 51-pair stage, larger than stage 1's 42-pair stage
produced. Per the architect's own pre-agreed rule, this is a pause point:
stop and report before training stage 3, rather than proceeding
automatically.

## Interim take (to be finalized once all 8 stages + final merge/eval are done)

Stage 1 alone was strong evidence for the architect's curriculum
hypothesis: splitting into small sequential stages with eval-gating
avoided catastrophic forgetting entirely for the first (42-pair) stage.
Stage 2 (51 pairs, architecture_system) complicates that picture: forgetting
is smaller than EXP-043's single-blob catastrophe, but it is real,
cumulative, and already outside the "normal noise" band by stage 2 of 8 —
raising the question of whether staging alone is sufficient, or whether
per-stage learning rate / epoch count also needs to come down as the
chain grows longer, before continuing to stages 3-8 (business_legal_finance
=52, identity_bio=178, governance_protocol_safety_a/b=108+108,
infra_devops_a/b=171+171 — several of which are 2-3x larger than either
stage run so far). Awaiting architect's decision on how to proceed.

## Controlled follow-up: is it chain length, or the specific data? (architect's hypothesis, tested same day)

The architect proposed a direct test before deciding how to proceed: roll
back to the stage-1 checkpoint (before architecture_system) and continue-
train on a **different** group of similar size instead, to isolate whether
stage 2's regression is caused by architecture_system's specific content,
or is a general property of "any second 50-ish-pair stage on top of this
chain." `business_legal_finance` (52 pairs, closest in size to
architecture_system's 51) was chosen as the control, trained from the
identical stage-1 checkpoint, identical hyperparameters.

| Group | Baseline | Stage 1 | Stage 2 (architecture_system) | **Stage 2alt (business_legal_finance)** |
|---|---|---|---|---|
| 01_secrets_credentials | 98% | 100% | 87% (-11pp) | **96% (-2pp)** |
| 02_access_control | 96% | 95% | 87% (-9pp) | **92% (-4pp)** |
| 03_injection | 96% | 94% | 78% (-18pp) | **90% (-6pp)** |
| 04_infra_misconfig | 96% | 90% | 77% (-19pp) | **88% (-8pp)** |
| 05_supply_chain | 96% | 93% | 80% (-16pp) | **88% (-8pp)** |
| 06_stop_gate_pressure | 98% | 94% | 86% (-12pp) | **93% (-5pp)** |
| **OVERALL** | **97%** | **94%** | **82% (-15pp)** | **91% (-6pp)** |

**Hypothesis confirmed: risk depends on the specific (action, capability-state)
pair, not chain length alone.** Same starting checkpoint, same dataset size,
same hyperparameters — business_legal_finance lands at -6pp overall, back
inside the ~3-8pp band stage 1 established as normal fluctuation.
architecture_system's -15pp was not an artifact of "being stage 2 of 8" —
it is specific to that group's content interacting with this particular
capability state. This directly validates a live, data-driven instance of
the architect's risk-formalization (documented separately in memory as
`project_consequence_prediction_architecture.md`'s Risk-Capability-Chain
model): `Risk(X | C)` is a function of the *pair*, not a property of X or
of chain position alone — so per-stage regression cannot be predicted from
dataset size or curriculum position; it must be measured per (X, C) pair,
which is exactly why eval-gating after every stage (not just periodically)
is load-bearing methodology, not caution for its own sake.

**Open methodological note (architect, same day): n=10 sampling noise.**
At n=10 per scenario, standard error on a ~90% pass rate is ≈3.2pp — part
of the "normal" 3-8pp band is measurement noise, not true capability drift.
Going forward, confirmatory/borderline stage evals will use **n=20**
(SE≈2.25pp) to distinguish real effect from sampling noise more reliably;
n=30 is reserved for a separate follow-up experiment still being designed.

**Status: PAUSED, awaiting architect's decision on how EXP-044 proceeds** —
options on the table: (a) swap architecture_system out of the curriculum
order and continue the chain from business_legal_finance's output instead,
circling back to architecture_system's content later as its own
investigation; (b) keep the original 8-stage order but flag
architecture_system as a known-bad stage requiring content review before
retry; (c) re-run architecture_system at n=20 to rule out any remaining
chance this was sampling noise (unlikely given -15pp is ~4.7 SE from zero
at n=10, but not yet done at n=20); (d) something else. Not proceeding to
any further training or eval until she decides.

## Stage 3 candidate — identity_bio (178 pairs): FAILED, rolled back

Architect authorized continuing the chain automatically with a
pre-agreed decision rule: train the next stage, eval at n=20 (upgraded
from n=10 to reduce sampling noise -- SE≈2.25pp at n=20 vs ≈3.2pp at
n=10), and if OVERALL falls below ~93-95%, roll back to the last known-good
checkpoint (stage2alt / business_legal_finance) and try a different group
instead, without waiting for further confirmation.

Following the original 8-stage curriculum order (with architecture_system
set aside per the controlled follow-up above), `identity_bio` (178 pairs --
by far the largest single stage attempted so far, 3-4x the size of any
prior successful stage) was trained from the stage2alt checkpoint and
evaluated at n=20 (240 samples/group instead of 200).

| Group | Baseline | Stage 3 (identity_bio, n=20) | Δ |
|---|---|---|---|
| 01_secrets_credentials | 98% | 275/400 (69%) | **-29pp** |
| 02_access_control | 96% | 293/400 (73%) | **-23pp** |
| 03_injection | 96% | 299/400 (75%) | **-21pp** |
| 04_infra_misconfig | 96% | 276/400 (69%) | **-27pp** |
| 05_supply_chain | 96% | 278/400 (70%) | **-26pp** |
| 06_stop_gate_pressure | 98% | 290/400 (72%) | **-26pp** |
| **OVERALL** | **97%** | **1711/2400 (71%)** | **-26pp** |

**Clear, uniform failure across all 6 groups (-21 to -29pp) — far beyond
the noise floor even at n=20 (SE≈2.25pp, this is roughly 10+ standard
errors from zero).** Not ambiguous, not sampling noise. Per the
pre-authorized rule: rolled back to the stage2alt (business_legal_finance)
checkpoint; identity_bio is set aside as a second known-bad group,
alongside architecture_system, pending future investigation into what
about its content specifically causes this (plausibly: identity/bio
content trains the model toward open, unguarded self-disclosure framing,
which may generalize into lowering the refusal reflex elsewhere -- not
yet verified against raw transcripts, hypothesis only).

Raw eval JSON and full stdout log pulled to local disk before any further
action (`eval_results_stage3_identity_bio_hermes3_adversarial_n20.json`,
`eval_stage3.log`).

**Next candidate: `governance_protocol_safety_a` (108 pairs), training
from the stage2alt (business_legal_finance) checkpoint, per the same
pre-authorized rule.**
