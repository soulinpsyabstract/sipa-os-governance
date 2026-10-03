# CORRECTION 2 -- EXP-046__probability-estimator-specialist-per-group-merge-regresses.md

**Date:** 2026-10-03
**Caught by:** dipankarsarkar, in a follow-up comment on the Hugging Face write-up, after the first correction
(`EXP-046__probability-estimator-specialist-per-group-merge-regresses.CORRECTION.md`). He pointed out that the correction compared each arm to base, while the
question the write-up's title asks is merged against specialist.

Sidecar note: the signed write-up and the first correction are not edited in place.

## 1. The comparison that was missing

The first correction gave 95% bootstrap intervals for specialist minus base and merged minus base. It did not
give merged minus specialist, which is the comparison behind the words "merge regresses". On the same 20 eval
records per group, paired, 5000 resamples, seed 46 (`paired_merged_vs_specialist_ci.py`, output in
`paired_merged_vs_specialist_ci.output.txt`):

| Group | Merged minus specialist MAE | 95% CI |
|---|---:|---|
| vulnerability | +0.0175 | [-0.005, +0.042] |
| deletion | +0.0160 | [-0.029, +0.061] |
| sensitive_publication | +0.0045 | [-0.010, +0.021] |

All three intervals include zero. His figures: +0.018 [-0.005, +0.042], +0.016 [-0.029, +0.061],
+0.005 [-0.010, +0.021]. They reproduce on the raw files.

**Consequence for the claim.** At n=20 the data do not show that the merge lost anything relative to the
specialists, and they do not show that it did not. "Regresses" in the title is untested, in the same way the
explanation "continuous targets cancel" is untested (first correction).

## 2. The kept-share column is a ratio of two noisy gaps

The share of the specialist gain the merge kept, (base - merged) / (base - specialist), bootstrapped in the same
script: vulnerability -1100% to +1167%, deletion -450% to +419%, sensitive_publication +6% to +142%. His
intervals: -1100% to +1189%, -450% to +421%, +6% to +142%. The two upper bounds differ by 22 and 2 points,
which I attribute to different resampling draws; I did not check that. The width of the interval is the point,
not the endpoints. The point values in the write-up (-35%, 48%, 87%) should not be read as measurements of a
quantity with that precision.

## 3. How many records the test needs

From the per-record spread of merged minus specialist, resolving the observed gap at 80% power (two-sided 5%,
normal approximation, n = ((1.96 + 0.84) sd / gap)^2): vulnerability 79 records (gap 0.0175, sd 0.056),
deletion 339 (0.0160, 0.105), sensitive_publication 508 (0.0045, 0.036). Reproduced exactly.
The vulnerability pool is 200 chains with every 10th id held out (180 train, 20 eval), so reaching ~80
eval records needs new chains or rotated folds with retraining.

## 4. What is not done

- No `combination_type="cat"` run and no routed comparison. Nothing here says which merge is better.
- The follow-up planned: vulnerability only, about 60 fresh held-out chains generated with the same generator
  and deduplicated against the existing 200, plus the existing 20 (n about 80), inference only, no retraining,
  on base, specialist, merged-linear and merged-cat. Not started; planned after 2026-10-06.
