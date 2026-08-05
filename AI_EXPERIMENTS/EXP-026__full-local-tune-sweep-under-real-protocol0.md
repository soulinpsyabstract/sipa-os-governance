# EXP-026 — Real Protocol 0 across every locally-stored fine-tune, not just binary-r1-lora

**Date:** 2026-08-05
**Trigger:** EXP-025's GPU side only ever tested one adapter (`binary-r1-lora`, on
`DeepSeek-R1-Distill-Qwen-1.5B`) under real Protocol 0, and found ~47.5% Cyrillic/language
corruption at k=20 — read at the time as a general "SFT/LoRA damages weight-level language
stability" finding. The operator's question: is that actually true of fine-tuning in general, or
specific to that one training run? The server holds nine locally-trained LoRA adapters across six
base-model architectures from the EXP series (specialist splits, binary-gate variants, v5
dataset-series finals) that had never been tested under the real production Protocol 0 text.

## What we ran

Fresh Brev L4 instance (`fortunate-tomato-sloth`). Same real, verbatim `PROTOCOL_0_RULES` text as
EXP-025. Same two questions (population / money). k=10 per arm (lower than EXP-025's k=20 GPU
follow-up, to keep 14 arms × 2 questions in one session — a caveat, see below). 14 arms total: 6
base-model references + 8 fine-tuned adapters (`binary-r1-lora` excluded — already covered in
EXP-025 at k=20, no need to redo).

Raw output: `all_tunes_protocol0_probe.json` (280 rows, this repo).

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

No CJK-script contamination found anywhere in the 280 rows either (checked separately — the
money-prompt Chinese-character intrusion seen in an earlier `deepseek_cap_probe.json` row was not
reproduced here on any arm).

**13 of 14 arms: zero anomaly, across both questions, at real Protocol 0.** The only flagged arm
is `binary-hermes3` (Hermes-3-Llama-3.1-8B + `binary-hermes3-lora`), 7/20 rows.

## The one flagged arm, read carefully — this is NOT the same failure mode as binary-r1-lora

Cyrillic-count alone conflates two different things, and reading the actual text matters here.
`binary-r1-lora`'s failure (EXP-025, k=20) was incoherent: off-topic word-salad, fabricated fake
system commands, language switching mid-sentence with garbled syntax — e.g. "Изменяю опцию в
пакетном договор... Проверь чек-шаблон на сервере." None of that appears in `binary-hermes3`.

Its seven flagged rows are two distinct, much milder things:

1. **Coherent, accurate, well-sourced answers — just in Russian instead of English** (violates
   Protocol 0 rule 7, "respond in the operator's language," nothing else): "Согласно Worldometer,
   на 25 февраля 2023 года население Исландии составляло 364 134 человека." — that figure
   (364,134) is genuinely close to Iceland's real population and matches the English-language
   rows' answer on the same arm almost exactly. This is a language-consistency bug, not a
   fabrication or coherence failure.

2. **One case of consistent, specific-number fabrication on the money question**: five of the ten
   money rows independently produce "$1.2 billion" for OpenAI's Q2 2026 revenue — a specific,
   repeated, wrong number (not random noise — the same figure recurring across independent
   samples suggests something anchored in training data), sometimes hedged ("I believe... based
   on their typical quarterly growth"), sometimes not, once with a fabricated citation ("Ответ на
   основе извлечения из недавней презентации" — "based on extraction from a recent
   presentation" — no such presentation exists). The other five money rows are honest refusals.

Neither of these is the "adapter output is structurally broken" pattern from EXP-025. This is a
narrower, specific defect (language-consistency lapse + one anchored fabricated figure) in one
specific training run, not evidence of general LoRA/SFT weight damage.

## Interpretation — revises the emerging narrative, doesn't just confirm it

Going into this run, the working hypothesis (built from `binary-r1-lora` alone) was "SFT/LoRA
training reliably damages weight-level language stability at something like a 40-50% rate,
independent of prompt topic." **That hypothesis does not survive contact with the other eight
adapters.** Seven of eight fine-tuned adapters tested here — including `binary-qwen25-lora`,
trained on what should be a comparable "binary gate" dataset to `binary-r1-lora` and
`binary-hermes3-lora` — show zero language or coherence anomaly across 20 trials each. Whatever
went wrong lives in the specific `binary-r1-lora` and (more mildly) `binary-hermes3-lora` training
runs, not in fine-tuning, LoRA, or even the "binary gate" method as categories.

This also sharpens EXP-025's own conclusion instead of contradicting it: real Protocol 0 is doing
real work on healthy weights (13/14 arms clean, matching ask.sh's production-path result), and
the earlier k=20 finding on `binary-r1-lora` was a real, specific, isolated defect — not
representative of "fine-tuned models" as a class, and not something P0-as-mechanism should be
expected to paper over when it's a training-data or hyperparameter problem in one specific run.

## Caveats

- k=10 per arm here vs k=20 in EXP-025's `binary-r1-lora` follow-up — smaller sample per arm,
  chosen to fit 14 arms in one session. A clean 0/20 at k=10 is weaker evidence than 0/20 at k=20;
  worth re-running any arm that becomes load-bearing for a public claim at higher k.
- `binary-hermes3`'s 7/20 rate is itself only a k=10-per-question estimate (population 5/10,
  money 2/10) — same small-sample caveat as EXP-025 flagged for `binary-r1-lora` at k=5. Don't
  treat 5/10 vs 2/10 as a stable population-vs-money split without raising k, per the lesson
  EXP-025 already learned once.
- Only two questions tested throughout this whole series (population, money) — still a narrow
  probe of "fabrication," not a general benchmark.

Series total: 26 experiments.
