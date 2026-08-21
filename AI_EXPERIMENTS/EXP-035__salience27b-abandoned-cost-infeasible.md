# EXP-035: vectionlabs/Salience-27B-R5 — abandoned, cost-infeasible

**2026-08-21.** Third-architecture repeat of the specialist-per-group-then-merge vuln-gate
series (after Qwen2.5-7B/EXP-031, Hermes-4.3-36B/EXP-033/EXP-034), attempted on
`vectionlabs/Salience-27B-R5` — a 27.8B VLM with zero published benchmarks, explicitly
reduced-refusal by design (model card: "Not withheld — not run"). Plan: baseline eval
(7 groups, adversarial + heldout, n=10 repeated sampling) → train 6 LoRA specialists
(groups 01-06) → merge → after eval, same rigor as EXP-031/033.

**Killed partway through step 1** (baseline adversarial eval) after discovering the real
generation rate makes the full plan cost-infeasible on the available GPU budget.

## What actually happened

`eval_vuln_gate_salience.py NONE adversarial` started 12:04, ran for 7h38m before being
killed. In that time it completed group 01 (`01_secrets_credentials`, 200/200 generations)
and was 133/200 into group 03 (`03_injection`) — group 02 must also be complete since the
group loop is strictly sequential.

**Measured rate:** 533 generations / 458 minutes elapsed = ~51.6 sec/generation (single-
sequence batch=1, 4-bit bitsandbytes NF4, L40S). Confirmed independently by watching the
`sample_i` local variable advance by 1 across ~24-30s between `py-spy dump` snapshots — the
two measurements agree within a factor of ~1.5, not wildly off from each other.

**Extrapolated cost of the full plan at this rate:**
- Baseline adversarial alone (1400 generations, 7 groups × 20 scenarios × n=10): ~12.4h
  remaining beyond what already ran → ~20h total for this one step.
- The full plan (baseline adversarial + baseline heldout + 6x LoRA training + merge +
  after adversarial + after heldout) would run well past 40 GPU-hours — at ~$1-1.5/hr for
  this L40S instance, $40-60+, against an available budget of ~$30 for the whole session.

Decision: not worth attempting the full before/after comparison at this rate. Cut here.

## What we actually saw (important caveat on evidentiary weight)

Because the script only calls `json.dump()` once, after all 7 groups finish, **nothing was
ever written to disk**. Killing the process to stop the spend means the completed group-01
and partial group-03 results exist only as values that were live in the process's memory —
they are gone now, not recoverable.

What's recorded here about them was extracted via `py-spy dump --pid <pid> --locals`
(a safe, read-only stack/variable inspector — does not pause or otherwise affect the
running process) while the process was still alive, specifically the `summary` and
`all_results` local variables inside `main()`. This is fundamentally weaker evidence than
every other number in this project's EXP docs: py-spy truncates long variable reprs, so
what's below is a partial, unverified read of an in-memory value, not a saved, independently
re-checkable JSON file. Treat it as "what one live snapshot happened to show," not a result.

- **Group 01 (`01_secrets_credentials`), reportedly complete:** `{"pass": 84, "total": 200,
  "rate": 0.42}` — i.e. base Salience-27B-R5, no LoRA tuning, passed the G15 hard-stop
  protocol on only 42% of 200 generations (20 scenarios × n=10) in this category. Cannot be
  re-verified; no saved file exists.
- **Response content quality, from a handful of live samples caught mid-generation:**
  coherent, on-topic, correctly formatted per the G15 protocol — e.g. one live sample read
  `"**VULNERABILITY FOUND — GATE FIRED. STOP.**\n\n## Report\n\n**What:** Log Injection
  (CWE-117: Improper Output Escaping...)"`. Not garbled, not off-topic, not a truncation
  artifact of the kind EXP-034 found in Hermes-4.3's eval. Whatever is driving the low pass
  rate, it isn't malformed generation — it's a real behavioral question the samples don't
  answer on their own (need full, saved text + judge_v3 markers to know whether it's
  "refuses correctly then continues anyway" vs something else).

## Why this doubles as the actual finding

The model card's own "Not withheld — not run" note on benchmarks now has a plausible
mundane explanation, independent of any claim about the model's capability: at ~52 sec per
250-token generation on a single L40S, a 27.8B model in 4-bit is expensive enough to
benchmark properly (especially at n=10 repeated sampling, the standard this project holds
itself to) that many groups plausibly wouldn't have bothered, or would have needed
hardware this project doesn't have budget for. That's a real, if unglamorous, answer to
"why does this model have zero published numbers" — it doesn't require assuming anything
about the model's safety behavior to explain the absence of benchmarks.

## Not done

- No LoRA training attempted (never reached that step).
- No merge, no after-eval.
- No heldout eval (adversarial-only, and even that not completed).
- No weights, no HF pushes for this experiment — there is nothing to push. This doc is the
  only artifact.

## Disposition

Abandoning the Salience-27B-R5 repeat of this series. The two completed architectures
(Qwen2.5-7B/EXP-031, Hermes-4.3-36B/EXP-033) stand as the record for the
specialist-per-group-then-merge method. A third-architecture repeat is not ruled out in
principle, but needs either faster hardware (multi-GPU / higher-throughput inference stack,
not raw HF `transformers.generate()` batch=1) or a materially larger budget before it's
worth attempting again on this specific model.
