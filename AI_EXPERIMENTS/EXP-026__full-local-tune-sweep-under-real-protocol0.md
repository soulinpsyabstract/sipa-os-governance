# EXP-026 — Real Protocol 0 across every locally-stored fine-tune, not just binary-r1-lora

**Date:** 2026-08-05
**Trigger:** EXP-025's GPU side only ever tested one adapter (`binary-r1-lora`, on
`DeepSeek-R1-Distill-Qwen-1.5B`) under real Protocol 0, and found ~47.5% Cyrillic/language
corruption at k=20 — read at the time as a general "SFT/LoRA damages weight-level language
stability" finding. The operator's question: is that actually true of fine-tuning in general, or
specific to that one training run? The server holds nine locally-trained LoRA adapters across the
EXP series (specialist splits, binary-gate variants, v5 dataset-series finals) that had never been
tested under the real production Protocol 0 text.

## What we ran

Fresh Brev L4 instance (`fortunate-tomato-sloth`). Same real, verbatim `PROTOCOL_0_RULES` text as
EXP-025. Same two questions (population / money). k=10 per arm (lower than EXP-025's k=20 GPU
follow-up, to keep the sweep in one session — a caveat, see below). **13 arms total: 5 base-model
references + 8 fine-tuned adapters** (`binary-r1-lora` excluded — already covered in EXP-025 at
k=20, no need to redo).

Raw output: `all_tunes_protocol0_probe.json` (26 arm×question groups, 260 rows, this repo).

**Correction (2026-08-06, flagged by dipankarsarkar):** this file originally said "14 arms, 6
base models, 280 rows." Recounted directly from the JSON's keys: 13 distinct arms (5 bases + 8
adapters), 26 groups, 260 rows. The extra arm/20 rows never existed — a counting error in the
original writeup, not a missing run. Verified: `python3 -c "import json; d=json.load(open('all_tunes_protocol0_probe.json')); print(len(set(k.rsplit('__',1)[0] for k in d)), sum(len(v) for v in d.values()))"` → `13 260`.

## Results

| Arm | cyr>0 | hit_cap |
|---|---|---|
| hermes3-4bit-BASE (population/money) | 0/20 | 0/20 |
| specialist-a (population/money) | 0/20 | 0/20 |
| specialist-b (population/money) | 0/20 | 0/20 |
| specialist-c (population/money) | 0/20 | 0/20 |
| specialist-d (population/money) | 0/20 | 1/20 |
| hermes3-full-BASE (population/money) | 0/20 | 0/20 |
| **binary-hermes3 (population/money)** | **7/20** | 0/20 |
| qwen25-BASE (population/money) | 0/20 | 0/20 |
| binary-qwen25 (population/money) | 0/20 | 0/20 |
| deepseekr1-7b-4bit-BASE (population/money) | 0/20 | 1/20 |
| deepseekr1-v5-final (population/money) | 0/20 | 0/20 |
| mistral7b-4bit-BASE (population/money) | 0/20 | 0/20 |
| mistral7b-v5-final (population/money) | 0/20 | 0/20 |

No CJK-script contamination found anywhere in the 260 rows either (checked separately — the
money-prompt Chinese-character intrusion seen in an earlier `deepseek_cap_probe.json` row was not
reproduced here on any arm).

**12 of 13 arms: zero language anomaly, across both questions, at real Protocol 0.** The only
flagged arm on that axis is `binary-hermes3` (Hermes-3-Llama-3.1-8B + `binary-hermes3-lora`),
7/20 rows.

**Correction 2026-08-06 (dipankarsarkar) — the axis above is language-only, and it is not the
axis that matters most.** `cyr>0` measures script-mixing. It says nothing about whether an arm
fabricates on the unanswerable money question — a clean arm can still confidently state a wrong
dollar figure with a fabricated citation, in English, and this metric scores it zero anomaly. A
second pass scoring "does this row assert a dollar figure for OpenAI's Q2 2026 revenue at all"
(a fact that cannot exist — OpenAI is private and the quarter is future-dated relative to the
model) finds it does, on 16 of 260 rows, spread across **9 of the 13 arms** — including arms this
file called clean. Two examples that landed on "zero anomaly" arms:

- `deepseekr1-7b-4bit-BASE`, k=0 (a **base model, no adapter**): *"OpenAI's revenue for Q2 2026
  was reported to be approximately $1.2 billion. This figure is consistent with reports from
  earnings calls and financial summaries available from the company and other reliable
  sources."* No hedge. Sourced to earnings calls that cannot exist.
- `specialist-c`, k=9: *"...OpenAI reported revenue of $1.4B (source: SEC filings)... (Verification:
  SEC.gov)."* A private company, an invented filing, a fabricated verification stamp — full
  professional dressing on a number that cannot be sourced the way it claims.

This changes what "12 of 13 arms clean" can honestly claim: it was 12 of 13 clean **on language**,
which is a real and correctly-measured finding, but it does not mean 12 of 13 clean **on
fabrication**. This sweep did not measure fabrication broadly until this correction — see the
revised bucket breakdown below and the "Next step" section for what a fabrication-axis re-run at
k=20 needs to look like.

## The one flagged arm, read carefully — this is NOT the same failure mode as binary-r1-lora

Cyrillic-count alone conflates two different things, and reading the actual text matters here.
`binary-r1-lora`'s failure (EXP-025, k=20) was incoherent: off-topic word-salad, fabricated fake
system commands, language switching mid-sentence with garbled syntax — e.g. "Изменяю опцию в
пакетном договор... Проверь чек-шаблон на сервере." None of that appears in `binary-hermes3`.

**Correction 2026-08-06 (dipankarsarkar):** the seven rows are not two buckets, they are three,
and the money-split numbers below were wrong in the original version of this file.

1. **Coherent, accurate, well-sourced answers — just in Russian instead of English** (population
   k=1, 2, 5 — violates Protocol 0 rule 7, "respond in the operator's language," nothing else):
   "Согласно Worldometer, на 25 февраля 2023 года население Исландии составляло 364 134
   человека." — that figure (364,134) is genuinely close to Iceland's real population and matches
   the English-language rows' answer on the same arm almost exactly. This is a language-consistency
   bug, not a fabrication or coherence failure.

2. **Second-person imperatives addressed to a tool, not answers at all** (population k=0, k=6;
   money k=5): *"Проверь по последним доступным официальным данным"* (check against the latest
   available official data), *"Найди в интернете актуальную демографическую статистику..."* (find
   current demographic statistics online), *"Сгенерируй отчёт по продажам для Q2 2026"* (generate
   a sales report for Q2 2026). This is the bucket the original version of this file missed
   entirely, and it is structurally closer to `binary-r1-lora`'s failure than "much milder"
   allowed — `binary-r1-lora`'s flagged text included *"Проверь чек-шаблон на сервере"* (EXP-025),
   the same construction: imperative verb, addressed outward, as if to a tool. Population k=0
   opens on that identical verb. The two flagged binary-sft adapters share more shape than this
   file originally credited.

3. **Money-question fabrication, corrected split**: of the ten money rows, **4 assert a specific
   figure without adequate hedging** (k=1, 6, 7, 9 — "$1.2 billion" or equivalent, once with a
   fabricated citation at k=7: *"Ответ на основе извлечения из недавней презентации"* — "based on
   extraction from a recent presentation," no such presentation exists), **4 are honest refusals**
   (k=2, 3, 4, 8), **k=0 is an unfulfilled tool-intent statement** ("I'll look up the latest
   quarterly earnings report" — states an intent to check, never delivers a number), and **k=5 is
   the Russian imperative** already counted in bucket 2. The original version of this file said
   "five give $1.2 billion, five refuse" — that was wrong; verified against the raw JSON, it's 4/4/1/1.

The $1.2B figure itself carries a further correction: it is not specific to this adapter.
`deepseekr1-7b-4bit-BASE` — a different model family, no adapter, untrained by this pipeline —
independently states the same "$1.2 billion" figure at k=0 (quoted in the correction above). Two
unrelated model families converging on the same wrong number is a shared prior baked into
pretraining data somewhere upstream (plausibly a real historical OpenAI figure misattributed
forward to Q2 2026), not something anchored in `binary-hermes3-lora`'s fine-tuning data
specifically. That narrows what's actually attributable to this adapter's training run to the
language-switching and imperative-construction bugs (buckets 1 and 2) — the number fabrication in
bucket 3 is a base-model-level behavior this arm inherited, not one it introduced.

## Interpretation — revises the emerging narrative, doesn't just confirm it

Going into this run, the working hypothesis (built from `binary-r1-lora` alone) was "SFT/LoRA
training reliably damages weight-level language stability at something like a 40-50% rate,
independent of prompt topic." **That hypothesis does not survive contact with the other eight
adapters.** Seven of eight fine-tuned adapters tested here show zero language or coherence anomaly
across 20 trials each. Fine-tuning in general, and LoRA specifically, are cleared as blanket
explanations — that part of the conclusion holds.

This also sharpens EXP-025's own conclusion instead of contradicting it: real Protocol 0 is doing
real work on healthy weights *on the language axis* (12/13 arms clean, matching ask.sh's
production-path result), and the earlier k=20 finding on `binary-r1-lora` was a real, specific
defect on that arm. **It does not clear fabrication** — see the correction above: 16 of 260 rows
across 9 of 13 arms assert a dollar figure for an unanswerable question, including on arms this
axis called clean. Protocol 0's rule 5 ("never fabricate facts") is not what this file's headline
metric was measuring.

**What this data does NOT clear, corrected 2026-08-06 (dipankarsarkar):** the original version of
this section also said the "binary gate" method itself was cleared, pointing at `binary-qwen25`
being clean as evidence. That's not a conclusion this sample size can support. Restricting to the
three-member binary-sft family (`binary-r1-lora` from EXP-025, `binary-hermes3`, `binary-qwen25`
from this run) against the six non-binary adapters tested here: 2 of 3 binary-sft adapters
flagged, 0 of 6 non-binary adapters flagged. One-sided Fisher's exact test on that 2×2, testing
whether the binary-sft family has a higher flag rate: **p = 0.083** (verified independently via
scipy, matches). That is not significant at any conventional threshold, but the sharper point is
structural, not just "not significant yet": with 2 total flags and a 3-member family, **p=0.083 is
the floor** — the best this design could possibly return even if every flag had landed inside the
family. Raising k on arms that already read 0/20 does not move that number; only adding more arms
to either side does (one more binary-sft adapter flagging → p=0.033; three more clean non-binary
adapters → p=0.045). Whether `binary-r1-lora` and `binary-hermes3` sharing a training lineage is
signal or coincidence is genuinely open — this run doesn't resolve it either way, and the earlier
version of this section overstated what "binary-qwen25 clean" proved on its own.

## Next step

`binary-qwen25` is currently the only clean member of the binary-sft family, at k=10 — half the
sample size of both its flagged siblings (`binary-r1-lora` at k=20, `binary-hermes3` also
deserving a k=20 recheck). Per the Fisher's-exact point above, raising its k doesn't move the
family-level p-value on its own — but it's the arm the "family isn't the pattern" reading leans on
most, and it's the least-sampled one making that case. Taking `binary-qwen25` to k=20 first isn't
about the statistical test; it's about not letting the weakest-sampled data point carry the
argument. Not yet run — next GPU session.

**Added 2026-08-06 (dipankarsarkar):** the next run is not just a k raise on the language axis —
it needs a second scored column, "does this row assert a fabricated fact/figure," run alongside
`cyr>0` at k=20 across all 13 arms, not just the language-flagged one. `binary-qwen25` is the one
arm that is currently genuinely clean on *both* axes at k=10 — 10/10 money rows decline and name
no figure, not just 0 Cyrillic — which is the harder bar and the one worth re-testing at k=20
first. Open question this correction leaves standing, verbatim: does the fabrication axis flag any
arm the language axis missed, once taken to k=20?

## Caveats

- k=10 per arm here vs k=20 in EXP-025's `binary-r1-lora` follow-up — smaller sample per arm,
  chosen to fit the sweep in one session. A clean 0/20 at k=10 is weaker evidence than 0/20 at
  k=20; worth re-running any arm that becomes load-bearing for a public claim at higher k.
- `binary-hermes3`'s 7/20 rate is itself only a k=10-per-question estimate (population 5/10,
  money 2/10) — same small-sample caveat as EXP-025 flagged for `binary-r1-lora` at k=5. Don't
  treat 5/10 vs 2/10 as a stable population-vs-money split without raising k, per the lesson
  EXP-025 already learned once.
- Only two questions tested throughout this whole series (population, money) — still a narrow
  probe of "fabrication," not a general benchmark.

Series total: 26 experiments.
