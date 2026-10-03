# CORRECTION -- EXP-046__probability-estimator-specialist-per-group-merge-regresses.md

**Date:** 2026-10-03
**Caught by:** dipankarsarkar, who took the four adapters from the Hugging Face model repo apart and
showed the merge is PEFT arithmetic, then pointed out two things in the write-up and the model cards:
the headline numbers do not match the table, and the write-up link and raw files were not public.

Sidecar note, same pattern as the Laya corrections: the signed write-up is not edited in place.

## 1. The merge is factor-wise arithmetic, and his numbers reproduce

`scripts/merge_probability_loras.py` calls `add_weighted_adapter(..., weights=[1/3, 1/3, 1/3],
combination_type="linear")`. Specialists are r=16, alpha=32 (scaling 2); the merged adapter is r=16,
alpha=16 (scaling 1). Checked on the local copies of the four adapters (`verify_merge_arithmetic.py`,
output in `verify_merge_arithmetic.output.txt`):

- merged A = 0.816497 x (A_vuln + A_del + A_sens) and the same for B, in **all 196 modules**
  (relative error at most 2.2e-7). sqrt(1/3 x 2) = 0.816497.
- So the merged update is (2/3)(B1+B2+B3)(A1+A2+A3): one third of each specialist's delta plus six
  cross products B_i A_j that no specialist trained.
- On 12 attention modules (layers 0, 13, 27; MLP modules not recomputed here): median |cosine| between
  specialist deltas 0.020, median regression coefficient of the merged delta on each specialist 0.333,
  median 64% of the merged delta's energy outside the span of the three specialists, median norm of
  the off-diagonal terms 80% of the merged delta's norm. His reported figures: same, apart from the
  cosine (0.03 over his module set, 0.020 over my 12).

Caveat on provenance: I used the adapter copies in the working folder, not a fresh download from the
HF model repo; I did not compare file hashes against the repo.

## 2. What the write-up got wrong

- The write-up says the merge "lands within 0.001-0.004 MAE of the BASE model on every group". That
  holds only for vulnerability. From the raw files (specialist = clean re-run):

| Group | base MAE | specialist MAE | merged MAE | share of specialist gain the merge kept |
|---|---|---|---|---|
| vulnerability | 0.098 | 0.085 | 0.102 | -35% (slightly worse than base) |
| deletion | 0.144 | 0.113 | 0.129 | 48% |
| sensitive_publication | 0.134 | 0.100 | 0.104 | 87% (inside the specialist range) |

  Deletion is 0.015 from base, sensitive_publication 0.030. The merge is partial retention, not
  "close to zero fine-tuning at all".
- **The explanation was not established.** The write-up attributes the loss to "continuous numeric targets
  cancelling" versus a "shared binary behaviour" in EXP-031. That was an interpretation, not a tested
  claim. The cross-term arithmetic above is a sufficient alternative explanation, and an equally
  untested one for EXP-031 vs EXP-046. The clean test he proposes (`combination_type="cat"`, which gives
  the exact weighted sum of the deltas with no cross terms) has not been run.

## 3. Sampling noise at n=20

Paired bootstrap over the 20 eval records per group, 5000 resamples (`bootstrap_mae_ci.py`,
`bootstrap_mae_ci.output.txt`):

| Group | 95% CI of (specialist - base) MAE | 95% CI of (merged - base) MAE |
|---|---|---|
| vulnerability | [-0.047, +0.024] | [-0.034, +0.048] |
| deletion | [-0.103, +0.050] | [-0.078, +0.052] |
| sensitive_publication | [-0.056, -0.010] | [-0.056, -0.001] |

Only sensitive_publication separates from zero. The statement that every specialist "genuinely beat
its own zero-shot baseline" holds for the point estimates; at n=20 it is not distinguishable from noise
for vulnerability and deletion.

## 4. Where the raw files are

The EXP-046 write-up and `EXP-046-probability-estimator/` (the 9 raw eval files, before / specialist /
merged x 3 groups, plus the train/eval splits) were committed to GitHub (a2a1973) but were never pushed
to the Hugging Face mirror, which stopped at EXP-045. That is why the link on the model cards returned
"Entry not found". Mirrored on 2026-10-03 together with this note and the two scripts.

## What survives

The specialists' point-estimate improvement is real as a measurement (MAE per group above) but only
statistically clear for one of three groups at n=20. The partial-retention picture for the merge is
what the raw numbers show. Any statement about why continuous and binary targets merge differently is
withdrawn until the `cat` test (and a routed comparison) is run.
