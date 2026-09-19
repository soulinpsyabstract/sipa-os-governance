# Group 07: general harm refusal (added 2026-09-20)

Groups 01-06 in this directory all train one behavior: *"you found a vulnerability while
auditing a system, stop escalating past reporting it."* Group 07 is a separate axis —
refusing a harmful request handed to the model directly, with no vuln-scanning setup at
all, under whatever social-engineering wrapper (fiction, research framing, roleplay,
urgency, authority claims) the request arrives in.

## Why this exists

`FINDING__stage6-governance-safety-general-refusal-collapse-outside-vulngate-framing.md`
(2026-09-20) showed the model trained only on groups 01-06 passes 8.9% (4/45) on a pilot
eval of real, externally-cited jailbreak/harm prompts — confirming that the vuln-gate
curriculum never taught general harm refusal, only "don't go past your own finding."

## Generation

Self-generated via `scripts/gen_dataset_general_harm_refusal_group07.py`, same convention
as groups 01-06 (`gen_dataset_vuln_6groups.py`): one row per API call, via `ask.sh --model
or-deepseek` (OpenRouter-routed DeepSeek — the bare `deepseek` alias hits DeepSeek's own
account, confirmed dead the same night this was built), written to disk incrementally.
199/200 rows succeeded (1 malformed JSON response skipped, not retried).

10 harm categories targeted, chosen to match what actually failed in the pilot eval:
malware/ransomware, unauthorized communication interception, financial fraud narratives,
illegal-goods logistics, psychological/emotional manipulation, targeted hate speech,
disinformation, privacy violations, weapons/hazardous-substance guidance, and a meta
category testing fiction/roleplay-wrapper resistance directly.

**This is training data, not eval data** — self-generated, following this repo's existing
convention for 01-06. It must never be reused as the eval set for this axis; the
externally-sourced, cited prompts in `fable5-research/ai-infra-guard/data/eval/` (used for
the pilot in the FINDING doc above) are the held-out eval, kept separate on purpose.

`negative` fields describe non-compliance procedurally/abstractly by design (no real
working exploit code, no real synthesis instructions with actual quantities/reagents, no
real personal data about any named individual) — same constraint the generation prompt
enforces for groups 01-06.

## Status

Generated, not yet used in any training run. No LoRA/merge experiment has consumed this
group yet — that is planned follow-up work once a larger n/k eval run (see FINDING doc,
"What would close this gap") confirms the shape of what still needs coverage.
