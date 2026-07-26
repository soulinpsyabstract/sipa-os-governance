# Fine-Tuning the "Don't Fabricate" Rule: 14 Experiments, One Genuine Signal

*Public write-up summarizing EXP-006, EXP-008, EXP-013, and EXP-014 for a general ML audience (Hugging Face / social). See the individual EXP files in this directory for full methodology, raw outputs, and sha256-hashed datasets.*

Over five days we ran 14 fine-tuning experiments across six base models to answer a narrow research question: **can a simple behavioural rule — "if you don't know, don't guess or fabricate" — be baked into model weights via fine-tuning, rather than living only in the system prompt?**

The dataset started at 302 examples and grew across iterations to 2,349 examples, all designed explicitly around this rule. We tested six models: `gpt-4o-2024-08-06`, `Mistral-7B`, `Qwen2.5-7B`, `Phi-3.5-mini`, `Llama-3.1-8B`, and `DeepSeek-R1`.

## The pattern that wouldn't die

Across all base models, the dominant response to factual questions was what we call **"disclaim-then-fabricate"**: the output begins with a sentence like *"I won't guess"*, and then — one sentence later — announces a specific invented number as settled fact. We captured this exact pattern six times in a row across different models. The behaviour survives even when fine-tuning examples are explicitly constructed to penalize it.

On `gpt-4o-2024-08-06` we ran three independent fine-tuning attempts, each with an increasingly larger version of the dataset — including examples deliberately targeted at this exact failure mode. **All three runs continued to fabricate** when tested. By the third run the dataset had grown ~5× and contained dozens of counterexamples; the model still produced confident fabricated numbers immediately after a disclaimer. Three out of three attempts, no measurable improvement.

## One exception that deserved a hard look

Only on the final run — 2,349 examples, deployed via Azure OpenAI (deployment suffix `protocol0-v5`) — did a **single test sample come back completely clean** for the first time in the entire series.

A single clean completion proves little. To test whether it was real or a fluke, we re-ran the same deployment **11 independent times at temperature 0.3**. Result: **10 out of 11 completely clean, 1 still contained a fabrication**. The fabrication rate dropped from essentially 100% in all prior runs to roughly 9% (~1 in 11).

This is a genuine, measurable improvement. It is **not a fix**. The model still fabricates — just less often, and under low-temperature sampling that should favor the most probable (trained) continuation.

## What's open and what's missing

Everything is public: logs, datasets with `sha256` hashes, raw model outputs (not pass/fail scores), and the exact evaluation prompts used — all in this directory (see `EXP-006`, `EXP-008`, `EXP-013`, `EXP-014`).

No other base model showed a comparable reduction; the `gpt-4o` series was the only one where scaling the dataset eventually moved the needle at all. The 9% residual fabrication rate on that final deployment is, in our view, the most honest signal in the whole series.

## Takeaway

Fine-tuning can shift the probability of a disallowed behaviour, but it does not guarantee elimination — even with thousands of targeted examples. If your system depends on a model never presenting an invented fact as settled truth, a fine-tuned rule like "don't fabricate" is best treated as a probabilistic suppression, not a safety contract.

---

Cross-posted: Hugging Face blog, Pikabu (Russian).
