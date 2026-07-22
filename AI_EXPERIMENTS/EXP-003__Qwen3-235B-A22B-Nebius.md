# EXP-003 · Qwen3-235B-A22B-Instruct-2507 + LoRA (Nebius AI Studio)

**Date:** 2026-07-20 (run prior to this session; documented retroactively 2026-07-22 from a
support ticket found during platform research for EXP-004/005)
**Status:** closed — **unevaluable**, not "success" or "failure"

## Setup

- **Base model:** `Qwen/Qwen3-235B-A22B-Instruct-2507`, via Nebius AI Studio's managed
  fine-tuning API (`api.studio.nebius.ai`, project `project-e00pp0qspr00hgse3ffpaf`)
- **Method:** supervised fine-tuning (LoRA), suffix `sipa-protocol-v1`
- **Dataset:** not directly confirmed from the support ticket that is the source for this
  entry — presumed to be the original 24-example Protocol-0 dataset (`protocol0_sft.jsonl`,
  same one used in EXP-001) based on the naming and timing, but this is **not verified** and
  should not be treated as fact.
- **Job ID:** `ftjob-56ea846badc64bc6b8b53916d432054a`
- **Result:** reported "succeeded", 38,979 trained tokens, 3/3 steps.
- **Training loss by epoch:** 1: 4.7104149 · 2: 4.6834140 · 3: 4.6542659 (no validation loss
  recorded — no validation file was used). Loss barely moved across 3 steps; not enough
  signal to say anything about convergence one way or the other.

## Why this is unevaluable, not a normal result

1. **Deployment for inference is blocked as a matter of Nebius product policy, not a bug.**
   Attempting to deploy the trained adapter (`POST /v0/models`) returns `400: Base model
   ... does not support LoRa inference yet, list of supported models: []`. A support ticket
   (ID M20181142, filed 2026-07-20 15:05, answered 15:14 same day) confirms this directly:
   *"LoRA per token model deployments have been deprecated. As an alternative, we may
   suggest you using Dedicated endpoint."* Re-verified live on 2026-07-22: the supported-model
   list for LoRA inference is still empty for any model on this account, consistent with the
   support answer (a permanent product change, not a transient outage).
2. **Downloading and serving the adapter locally — the workaround used elsewhere in this
   log (see EXP-004) — is not practically available here.** Qwen3-235B-A22B is a ~235-billion
   parameter model. Even the base weights alone are far beyond what any GPU used in this
   project's other experiments (T4 15GB, L4 24GB) could load, merge, or run inference on.
   There is no accessible path to actually test what this fine-tune did to model behavior.

## Conclusion

- The job completed on Nebius's own terms ("succeeded"), but **this project has no way to
  independently verify or benchmark the result** — not because the experiment failed, but
  because the model is too large to serve on our infrastructure and the platform's
  lightweight LoRA-serving path was deprecated by Nebius on the same day the job ran.
- Recorded here as **inconclusive/blocked**, not spun as either a success or a negative
  result — the honest answer is "we don't know, and can't find out without paying for a
  Nebius Dedicated Endpoint," which was deliberately not pursued (see repo README approach:
  free/self-hostable paths first).
- No further action planned on this specific job. Superseded in practice by EXP-005
  (Nebius fine-tune on a size-appropriate model chosen specifically to remain locally
  downloadable and mergeable).
