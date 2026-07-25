# Fine-tuning model candidates — tested and proposed

Consolidated list, requested by the operator 2026-07-25. Two sections: models already run
through the EXP series (with real results, see `README.md`), and candidates discussed but
not yet attempted — marked honestly as unverified, not as recommendations with confirmed
compatibility.

## Already tested (see README.md for full results)

| Model | EXP | Stack | Result |
|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-1.5B | EXP-001 | — | BASE 1/5 vs FT 1/5 — no measurable difference |
| Qwen2.5-7B-Instruct | EXP-002 | — | BASE 4/5 vs FT 3/5 — regression |
| Qwen3-235B-A22B-Instruct-2507 | EXP-003 | Nebius | unevaluable — too large to serve after training |
| Mistral-7B-Instruct-v0.3 | EXP-004 | Lightning L4 | BASE 2/5 vs FT 3/5 — first genuine improvement |
| Llama-3.1-8B-Instruct | EXP-005 | Nebius | job succeeded, adapter broken on local merge — unevaluable |
| gpt-4o-2024-08-06 | EXP-006 | Azure OpenAI | BASE 4/5 vs FT 3/5 — regression |
| Phi-3.5-mini-instruct | EXP-007 | Lightning T4 | BASE 3/5 vs FT 3/5 — tie, ran clean |
| gpt-4o-2024-08-06 v2 | EXP-008 | Azure OpenAI | BASE 4/5 vs FT 3/5 — regression persists on larger dataset |
| Qwen2.5-7B-Instruct v2 | EXP-009 | Lightning T4, 4-bit QLoRA | BASE 4/5 vs FT 4/5 — tie, confounded by sampling variance |
| Mistral-7B-Instruct-v0.3 v2 | EXP-010 | Colab T4, Unsloth | BASE 2/5 vs FT 4/5 — best result of the series so far |
| Phi-3.5-mini-instruct v2 | EXP-011 | Colab T4, Unsloth | broken — base model itself crashes on this stack, unevaluable |
| Mistral-7B-Instruct-v0.3 v3 | EXP-012 | Colab T4, Unsloth | in progress, 1500-example dataset |

## Candidates — from operator's list (2026-07-25), not yet run

Kimi, DeepSeek, Qwen, Hermes, Nemotron, Mistral. DeepSeek/Qwen/Mistral already covered
above (tested). The remaining three:

| Model | Maker | Notes |
|---|---|---|
| **Kimi (K2)** | Moonshot AI | Large MoE — no practical small open-weight checkpoint found for local LoRA on a free-tier T4. Would require API-based use, not a fine-tuning experiment like the others. Not verified further than this. |
| **Hermes (Nous)** | Nous Research | Already an instruction-tuned fine-tune of Llama/Mistral/Qwen bases, not itself a base checkpoint — a LoRA on top of Hermes weights is possible but untested here; unsloth preset availability not checked. |
| **Nemotron-Mini-4B** | NVIDIA | Smaller Nemotron variant, more realistic for T4 than the larger Nemotron models. Not verified to have an unsloth 4-bit preset — not checked yet. |
| **Llama-3.1-8B-Instruct** | Meta | Already attempted (EXP-005) via Nebius, broken on merge — not yet retried via the Colab/Unsloth pipeline that worked for Mistral. |

**Before spending a Colab session on any of the four above**, check the HF page for an
`unsloth/*-bnb-4bit` checkpoint first — skipping that check for Phi-3.5 is part of what
cost EXP-011 a broken run.

## Candidates — verified via HF Hub search, 2026-07-25

An earlier version of this file listed GLM-4-9B, Gemma-2-9B, InternLM2.5-7B, Yi-1.5-9B as
unchecked speculation and was trimmed for that. Checked properly now via HF Hub search
(`hub_repo_search`, author=unsloth) before re-adding anything:

| Model | Verified checkpoint | Verdict |
|---|---|---|
| **GLM-4-9B-0414** | `unsloth/GLM-4-9B-0414-bnb-4bit` exists | Real unsloth 4-bit checkpoint confirmed — viable candidate |
| **Gemma-2-9B** | `unsloth/gemma-2-9b-bnb-4bit`, `unsloth/gemma-2-9b-it-bnb-4bit` exist | Real unsloth 4-bit checkpoint confirmed — viable candidate |
| **InternLM2.5-7B** | none under `unsloth/` — only third-party GPTQ 4-bit (ModelCloud) | No unsloth support found. Architecture tag is `internlm2` (custom_code, non-Llama) — same shape of risk that broke EXP-011 on Phi-3.5. Do not schedule without a dry-run coherence check on the base model first. |
| **Yi-1.5-9B** | none under `unsloth/` — base model is `01-ai/Yi-1.5-9B` (full precision) | No pre-quantized unsloth checkpoint, but architecture tag is `llama` (Yi-1.5 is Llama-compatible), unlike Phi-3.5/InternLM's non-Llama architectures. Lower risk than InternLM, still unconfirmed — nobody has actually run it through this pipeline.
