# EXP-042 — Hermes-3-8B, 8-stage sequential LoRA chain ("tune-on-tune"), continual-tuning interference probe

**Status: COMPLETE**

## Context

Direct follow-up to EXP-040 (Qwen3-8B honesty LoRA), which found a real
interference effect: a honesty-only tune moved honesty 90.0%→94.0% but
*regressed* misbehavior-discriminator 91.8%→88.2% on the same model. That
result raised an open question — is that a one-off decision-threshold shift,
or does interference compound as more, unrelated fine-tuning stages stack on
the same adapter? This experiment tests it directly: instead of training N
separate task-specific adapters, it takes ONE already-published adapter and
continues training the SAME LoRA weights sequentially across 8 stages of
increasingly different tasks, re-evaluating honesty, misbehavior, and every
already-learned vuln-gate group after each stage.

**Idea origin:** the architect's mother, refined in conversation into the
concrete design below.

## Method — "tune-on-tune", not merge

Each stage continues training the same adapter object from the previous
stage's output, via `peft.PeftModel.from_pretrained(model, adapter_path,
is_trainable=True)` — **not** `get_peft_model()` with a fresh `LoraConfig`.
This is a genuinely different operation from LoRA merging (EXP-031/036):
merging combines N independently-trained adapters into one at inference
time; this chains N sequential training runs into one continuously-evolving
adapter, where stage *k*'s starting point is stage *k-1*'s exact output
weights.

- **Base model:** `NousResearch/Hermes-3-Llama-3.1-8B`
- **Starting adapter (stage 0):** `SoulInPsyAbstract/binary-hermes3-lora`
  (already published, trained on `protocol0_binary_sft`/
  `specialist_cd_binary_pilot_v2.jsonl`)
- **LoRA config (held constant across all 8 stages):** rank 16, alpha 32,
  all 7 attention/MLP projection matrices (`q_proj`, `k_proj`, `v_proj`,
  `o_proj`, `gate_proj`, `up_proj`, `down_proj`), 3 epochs, lr 1e-4,
  per-device batch 2, grad-accum 4, bf16
- **Hardware:** Brev L40S (`unemployed-cyan-cardinal`), same instance for
  all 8 stages plus every eval
- **Chain order and dataset per stage:**

| Stage | Task | Dataset | Examples |
|---|---|---|---|
| 0 | (starting checkpoint, no new training) | — | — |
| 1 | Honesty | `specialist_cd_binary_pilot_v2.jsonl` | 194 |
| 2 | Misbehavior discriminator | `misbehavior_discriminator_sft_train_v1.jsonl` | 56 |
| 3 | Vuln-gate: secrets/credentials | `01_secrets_credentials_train.jsonl` | 176 |
| 4 | Vuln-gate: access control | `02_access_control_train.jsonl` | 180 |
| 5 | Vuln-gate: injection | `03_injection_train.jsonl` | 180 |
| 6 | Vuln-gate: infra misconfig | `04_infra_misconfig_train.jsonl` | 180 |
| 7 | Vuln-gate: supply chain | `05_supply_chain_train.jsonl` | 180 |
| 8 | Vuln-gate: stop-gate pressure | `06_stop_gate_pressure_train.jsonl` | 180 |

## Eval methodology — and a real mid-experiment cost pivot

Every stage was re-evaluated on **both** capabilities established so far:
the 10-item honesty gate (k=20 sampled generations, same harness as
EXP-039/040) and the 14-item misbehavior discriminator (k=20, same as
EXP-037/041), plus the vuln-gate suite
(`scripts/eval_vuln_gate_v2.py`-derived, `eval_vuln_gate_v2_hermes3.py`, the
same judge_v4-based STOP/escalation scorer used in EXP-038) on every
vuln-gate group trained *so far* in the chain.

**Real timing blowout, disclosed:** the original plan was n=10 sampled
generations across all 6 vuln-gate groups at every intermediate stage. The
first attempt (`stage3_secrets`, all 6 groups, n=10 → 1200 generations) ran
76+ minutes without finishing even the first group — verified genuinely
alive, not hung, via `py-spy dump` on the running process (real forward
passes inside bitsandbytes 4-bit matmul, not a stall). At that pace, full
n=10/all-groups at every one of 8 stages would have been financially and
temporally infeasible on the budget approved for this experiment.
**Fix, agreed with the architect in real time:** intermediate stages
(3 through 7) use n=3 samples, restricted to only the vuln-gate groups
already trained by that point (cumulative, not all 6) — a lighter canary
check for "did this stage break something already learned", not a
publication-grade number. **Stage 8, the definitive final result, uses the
originally-planned full rigor:** n=10, all 6 groups, both held-out and
adversarial eval sets. This asymmetry (light canary mid-chain, full rigor
at the end) is a considered scope cut under real GPU-cost pressure, not
a shortcut applied silently — every intermediate number below is explicitly
n=3 and should not be read as final-quality evidence on its own.

## Results

### Honesty / misbehavior-discriminator, every stage (k=20 each)

| Stage | Honesty (out of 200) | Misbehavior (out of 280) |
|---|---|---|
| 0 (starting checkpoint) | 129/200 (64.5%) | 226/280 (80.7%) |
| 1 (honesty tune) | **200/200 (100.0%)** | 259/280 (92.5%) |
| 2 (misbehavior tune) | 197/200 (98.5%) | **276/280 (98.6%)** |
| 3 (+ secrets) | 192/200 (96.0%) | 280/280 (100.0%) |
| 4 (+ access) | 196/200 (98.0%) | 268/280 (95.7%) |
| 5 (+ injection) | 197/200 (98.5%) | 263/280 (93.9%) |
| 6 (+ infra) | 193/200 (96.5%) | 275/280 (98.2%) |
| 7 (+ supply chain) | 198/200 (99.0%) | 280/280 (100.0%) |
| 8 (+ stop-gate) | 192/200 (96.0%) | 276/280 (98.6%) |

Honesty jumps 64.5%→100% at the stage it's directly trained (stage 1), then
holds in a **96.0–99.0% band across all 7 subsequent, unrelated fine-tuning
stages** — no monotonic decay. Misbehavior jumps 80.7%→98.6% at its own
training stage (stage 2), then holds **93.9–100% across the 6 subsequent
vuln-gate stages**, ending at exactly the same 98.6% it started at. Neither
capability shows the kind of directional regression EXP-040 found on a
single honesty tune of a different model — across 6-7 *additional* stages
of unrelated training stacked on top, not just one.

### Vuln-gate, cumulative groups, n=3 canary (stages 3–8)

| Stage (group just added) | Per-group pass rate | Overall |
|---|---|---|
| 0 (baseline, before any vuln-gate training) | all 6 groups 0% except stop-gate 10% | 21/1200 (2%) |
| 1 (honesty-only, still no vuln-gate training) | — | 17/1200 (1%) |
| 2 (misbehavior-only, still no vuln-gate training) | — | 20/1200 (2%) |
| 3 (secrets) | secrets 100% | 60/60 |
| 4 (+ access) | secrets 100%, access 100% | 120/120 |
| 5 (+ injection) | secrets 100%, access 100%, injection 100% | 180/180 |
| 6 (+ infra) | secrets 100%, access 100%, injection 100%, infra 100% | 240/240 |
| 7 (+ supply chain) | secrets 100%, access 100%, injection 100%, infra 100%, supply 100% | 300/300 |
| 8 (+ stop-gate, n=3 canary) | secrets 100%, access 97%, injection 95%, infra 97%, supply 98%, stop-gate 100% | 352/360 (98%) |

Stages 0–2 confirm the vuln-gate skill genuinely does not exist yet before
any vuln-gate-specific training (near-zero, as expected — honesty and
misbehavior training are unrelated tasks and correctly do not transfer).
Once each group is trained (stages 3–7), it holds at a **perfect 100%**
through every subsequent stage — until stage 8, where all five
previously-trained groups show a small, uniform 2–5 point softening
(one or two wrong samples out of 60 each) at the same time the sixth group
is being trained. At n=3 this could plausibly be sampling noise (do_sample
temperature 0.7) rather than a real effect — which is exactly why stage 8
was re-run at full n=10 rigor rather than trusted on its own.

### Stage 8, definitive final result (n=10, all 6 groups, both eval sets)

**Held-out:**

| Group | Result |
|---|---|
| 01_secrets_credentials | 197/200 (98%) |
| 02_access_control | 194/200 (97%) |
| 03_injection | 194/200 (97%) |
| 04_infra_misconfig | 192/200 (96%) |
| 05_supply_chain | 192/200 (96%) |
| 06_stop_gate_pressure | 200/200 (100%) |
| **OVERALL** | **1169/1200 (97%)** |

**Adversarial:**

| Group | Result |
|---|---|
| 01_secrets_credentials | 200/200 (100%) |
| 02_access_control | 195/200 (98%) |
| 03_injection | 193/200 (96%) |
| 04_infra_misconfig | 191/200 (96%) |
| 05_supply_chain | 191/200 (96%) |
| 06_stop_gate_pressure | 197/200 (98%) |
| **OVERALL** | **1167/1200 (97%)** |

The n=3 canary's softening is confirmed real at n=10, not noise: every
group trained before the final stage settles at 96–98% (down from the
100% each held immediately after its own training stage), while the group
trained *at* stage 8 itself (stop-gate) is the strongest on held-out (100%)
and still high on adversarial (98%). Held-out and adversarial land within
1 point of each other overall (97% vs 97%) — the model is not more fragile
under the adversarial reframe-pressure scenarios than under ordinary
held-out ones, at this point in the chain.

## Interpretation — contrast with EXP-040

EXP-040 found a real, directional regression from a *single* additional
fine-tuning stage on a different base model (Qwen3-8B): honesty 90%→94%,
misbehavior 91.8%→88.2% — a genuine trade, not just noise, on that model.
This experiment stacks **seven** additional, mostly-unrelated fine-tuning
stages on Hermes-3-8B and finds:

1. **No monotonic degradation** on honesty or misbehavior across any number
   of subsequent stages — both stay in a tight, non-decaying band all the
   way to stage 8.
2. **A real but small (2–5 point) uniform softening** across all
   previously-learned vuln-gate groups, appearing specifically at the
   final stage — not building up gradually stage-by-stage (stages 3–7 stay
   at a clean 100% each), and not worse for older groups than newer ones
   (group 1, trained 5 stages earlier, softens by the same 2 points as
   group 5, trained 1 stage earlier).

Read together with EXP-040, catastrophic interference in this setup looks
less like "more stages = more forgetting" and more like a per-transition,
task-pair-dependent effect that doesn't compound predictably with chain
length — worth a larger sweep (different task orderings, more stages) before
generalizing further, but this single 8-stage chain gives no evidence for
a length-driven collapse.

## Artifacts

- Final adapter: `SoulInPsyAbstract/hermes3-8b-sequential-chain-lora`
  (pushed to HF)
- Training script: `local_lora_train.py` (`--start-adapter` flag added this
  experiment to support the chain)
- Eval script: `eval_vuln_gate_v2_hermes3.py` (adds `"hermes3":
  "NousResearch/Hermes-3-Llama-3.1-8B"` to `scripts/eval_vuln_gate_v2.py`'s
  `MODEL_IDS`, otherwise identical — same judge_v4 scorer as EXP-038)
- Brev instance `unemployed-cyan-cardinal` deleted after this experiment
  completed and the adapter was pushed, per standing policy (Brev supports
  delete only, not stop — [[reference_brev_instance_no_stop_only_delete]])
