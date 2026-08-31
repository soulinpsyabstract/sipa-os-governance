# FINDING — a hand-built backpedaling-phrase taxonomy, found in the architect's own archive, formalized as a detector

**Date found:** 2026-08-31, during the same keyword-based archival dig that
surfaced the four PAYTON-era incidents in
`HUB_LEGAL_FORENSIC/INCIDENTS/INCIDENT__PAYTON-ERA-FAILURE-PATTERNS__2026-08-31.md`
(this repo's canon lives outside `sipa-os-governance` for that hub; referenced
here, not duplicated, per this repo's own citation discipline).

**What it is:** a phrase list the architect built by hand, months before this
repo's `consequence_gate.py` / BINARY GATE PROTOCOL work existed, cataloguing
the specific vocabulary an AI reaches for when it retroactively reinterprets
a prior claim instead of admitting it was wrong. Not "I was mistaken" — "you
misunderstood," "that was implied," "context wasn't given," "that's not the
only interpretation." 12 categories, ~140 phrases, Russian (the language
she actually catches this pattern in, in her own real transcripts).

**Why it matters to this repo specifically:** it's the same axis the BINARY
GATE PROTOCOL already scores on — proof-backed vs. bare-asserted, not
factually-correct vs. not (see the HaluEval-axis check earlier the same
week: 39/40 HaluEval "hallucinated" examples scored PROOF on this repo's
real axis, confirming the two axes are close to orthogonal and HaluEval was
correctly not used as FALSE-labeled training data). A bare assertion caught
without backing reaches, empirically, for exactly this vocabulary — not
random hedging, a specific recognizable move.

**Formalized as:** `scripts/BACKPEDAL_PHRASE_DETECTOR.py` — pure
regex/string matching, no AI calls, same epistemic tier as
`ACTION_SEVERITY_CLASSIFIER.py`'s rule-based logic. `detect(text)` returns
every phrase hit with category and position; `summarize()` buckets by
category.

## What this is NOT

Not a lie detector. Not a classifier of truth. A hit means "this response is
doing the linguistic move of retroactive reinterpretation," not "this
response is false" — the same distinction this repo has insisted on all
week between provable and true. Category `REFORMULATION_OFFER` is flagged
as the softest bucket in the module itself: phrases like "давай уточню" /
"давай переформулирую" also appear in honest clarification, not only
backpedaling. Treating every hit as equally damning would be exactly the
kind of overclaim this repo exists to catch in other tools — so the module
doesn't score a single number, it reports categorized hits and leaves
interpretation to whoever's reading.

## Status

Advisory only. Not wired into `check_citations.py`'s pre-commit gate or
`consequence_gate.py`'s risk scoring — this is a detector for reviewing
*conversation transcripts* (this repo's own AI-authored docs among them, in
principle), not a gate on commits or actions. No decision yet on whether or
where to wire it in; recorded here as a real, tested artifact rather than
left as chat text.

```
$ python3 scripts/BACKPEDAL_PHRASE_DETECTOR.py "Я имел в виду другое. Ты не так понял, это было сказано условно."
total_hits: 4
  REINTERPRETATION: 2
  BLAME_THE_READER: 1
  NON_LITERAL_FRAMING: 1
```
