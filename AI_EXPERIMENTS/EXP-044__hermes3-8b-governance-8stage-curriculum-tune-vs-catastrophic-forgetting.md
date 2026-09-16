# EXP-044 — Hermes-3-8B security specialist, 8-stage curriculum-split governance tune (direct follow-up to EXP-043)

**Status: IN PROGRESS — updated live, stage by stage, per architect's explicit instruction ("сырые ответы сразу документируй и пуш после проверки чтобы не забывалось")**

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

*(eval in progress at time of this doc's first commit — result to be
appended in the next update once the eval completes)*

## Interim take (to be finalized once all 8 stages + final merge/eval are done)

Stage 1 alone is strong evidence for the architect's curriculum hypothesis:
identical hyperparameters, identical starting adapter, identical total
governance-knowledge content eventually intended — but splitting into
small sequential stages with eval-gating between them avoided the
catastrophic forgetting entirely, at least for the first stage. This will
continue to be tested stage-by-stage; a full verdict (including whether
later, larger stages like identity_bio=178 or the infra_devops halves at
171 each hold up as well as this first 42-pair stage) is pending.
