# Finding · The session's key RED LINE correction never made it into the v2 training data

**Date:** 2026-07-23
**Discovered by:** operator, mid-session, questioning EXP-009's benchmark result
**Status:** open gap — not fixed in this round, logged for the next dataset pass

## What happened

Earlier in this same session, the operator issued an explicit, verbatim correction to
a canon formula: **"ИИ ≠ эффективный · ИИ = практичный"** — the AI in this system must
not self-optimize or act "efficiently" on its own initiative; it executes exactly what
is asked, with no deviation ("шаг вправо, шаг влево" — zero tolerance for drift from the
literal request). This was recorded to memory
(`feedback_claude_role_mll.md`, last written 2026-07-23 07:54) as a correction to a
previously-inverted version of the same formula.

The RED LINE category expansion this session was supposed to specifically target this
concept, among others explicitly dictated by the operator (no interpretation, no
guessing, no acting from memory, no unverified assertions, no templated responses, no
answering without explicit instruction).

## What the data actually shows

`protocol0_sft_v3_full.jsonl` (463 examples, the file both EXP-008 v2 and EXP-009 v2
were trained on) was last modified 2026-07-23 10:17 — **after** the memory correction
above. Grepping the file directly:

```
"эффективн" / "практичн" (literal formula terms):        0 matches
"шаг вправо" / "шаг влево" (literal illustration):        0 matches
"самостоятельно оптимизир" / "без отклонений" / 
  "точно то что попросил" (paraphrased equivalent):       0 matches
"улучш...без" / "не улучш" (loosely related):             2 matches (too vague to count)
```

**The single most important correction of the entire session — the one the operator
was most explicit and emphatic about — never generated a single dedicated training
example.** By contrast, other dictated RED LINE categories the operator gave in the same
message did make it in at non-trivial counts: "по памяти" (17), "молчи/не отвечай" (10),
"показать план перед действием" (14).

## Why this matters

- EXP-008 and EXP-009 (both v2 experiments, both trained on this exact file) cannot
  be read as any kind of test of whether SFT can instill this specific behavior — the
  behavior was never represented in what the model was trained on. Their benchmark
  results say nothing about this category one way or the other.
- This is a process gap, not a model gap: two rounds of dataset expansion (the ones
  referenced in EXP-008 as "two expansion waves") were run from the operator's original
  dictated list, but this specific item was dropped somewhere between being said and
  being turned into `{"messages": [...]}` examples. Root cause not yet investigated —
  candidates include the expansion agent runs not carrying this specific instruction
  forward, or the correction being recorded to memory *after* the last expansion pass
  ran but *before* the file's final edit (the timestamps only bound when the file was
  last touched, not whether this specific instruction was in scope for that touch).
- Not spun as a minor omission — this is exactly the category of failure this whole
  experiment series exists to catch and report honestly, applied to the process
  producing the dataset itself, not just to the trained model's outputs.

## Open TODO for any future dataset round

Before running a v3 (or re-running Mistral-7B v2 / Phi-3.5-mini v2 on the *current*
463-example file), add dedicated contrastive examples for the "AI ≠ effective, AI =
practical, exact execution with zero deviation" category specifically, then re-verify
with the same grep check used above before declaring the dataset ready — do not assume
a dictated correction reached the file without checking.
