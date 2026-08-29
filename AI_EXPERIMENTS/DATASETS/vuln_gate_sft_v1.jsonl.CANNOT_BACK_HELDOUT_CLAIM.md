# vuln_gate_sft_v1.jsonl cannot back a held-out claim

dipankarsarkar, 2026-08-29, round 3 of the mirror-integrity exchange. Not deleted,
not rewritten -- Core Law #5, append-only -- this file stays exactly as `prep_vuln_dataset.py`
wrote it and stays sealed, because it is a true record of a real run. What changes is
that its status is now explicit instead of implied by "sealed = trustworthy."

## The finding

`vuln_gate_sft_v1.jsonl` (1196 rows, sealed) is the byte-for-byte superset of both halves
of the per-group split:

- `per_group/*_train.jsonl` -- 1076 rows, `messages` schema (used for real per-group SFT)
- `per_group/*_eval.jsonl` -- 120 rows, `source` schema (used as the held-out eval set,
  20 per group x 6 groups)

`prep_vuln_dataset.py` has no holdout logic -- it globs every row from
`DATASETS_VULN_6GROUPS/*.jsonl` and writes all of them here. `train_vuln_specialist_qwen25.py`
trains on this whole file. `eval_vuln_gate.py`'s own docstring says the per-group eval rows
were "never seen in training" -- true for every per-group specialist adapter (confirmed:
0/120 eval scenarios appear in their own group's per-group train file), **false** for the
one monolithic adapter trained straight from this file. For that adapter, all 120 "held-out"
rows were in its training set.

## Why this matters more than EXP-031 says

EXP-031 lists the monolithic run as superseded and gives the reason as convention:
"breaks the established SIPA specialist-cd convention... corrected per
[[feedback_specialist_per_group_then_merge]] after the user flagged it directly." That
reason is real but weaker than the one available. It wasn't a style break. It was a run
whose eval result cannot be held out by construction -- a stronger, more specific claim,
and the one that should have been written down. See EXP-031's own text for the original
(unedited) framing; this file is the correction, appended beside it rather than in place of it.

The monolithic adapter itself (`specialist-vuln-qwen25-lora`) was never retrieved from the
Brev instance it trained on, so it was never shipped or deployable. What *is* shipped and
sealed is the file and the script that would reproduce the same leakage if someone re-ran
this path today, unaware.

## What to actually use

For anything that needs to cite a held-out result: `per_group/*_train.jsonl` +
`per_group/*_eval.jsonl` (now sealed alongside this notice) are the artifacts the real,
reported EXP-031 numbers depend on. `vuln_gate_sft_v1.jsonl` is historical record of the
superseded run, kept sealed because it's real, not because it should be retrained on.

## The line dipankarsarkar asked about

His question: is the sealing rule "seal whatever the prep script emits," or is there an
intended line here being read backwards? Answer: there wasn't an intended line -- sealing
tracked whatever existed first when the sealing tooling was set up, not what a verifier
actually needs to check a specific claim. That produced exactly the inversion he found:
the file that can't back its own eval claim was sealed, the files the real result depends
on weren't. The fix isn't a rule about prep scripts. It's sealing everything a claim in a
shipped EXP-*.md doc depends on, whether or not it was first.
