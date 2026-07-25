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

## Candidates — not yet run, unverified compatibility

From operator's list (2026-07-25): Kimi, DeepSeek, Qwen, Hermes, Nemotron, Mistral.
DeepSeek/Qwen/Mistral already covered above. The remaining three, plus additions:

| Model | Maker | Notes |
|---|---|---|
| **Kimi (K2)** | Moonshot AI | Large MoE — no practical small open-weight checkpoint found for local LoRA on a free-tier T4. Would require API-based use, not a fine-tuning experiment like the others. Not verified further than this. |
| **Hermes (Nous)** | Nous Research | Already an instruction-tuned fine-tune of Llama/Mistral/Qwen bases, not itself a base checkpoint — a LoRA on top of Hermes weights is possible but untested here; unsloth preset availability not checked. |
| **Nemotron-Mini-4B** | NVIDIA | Smaller Nemotron variant, more realistic for T4 than the larger Nemotron models. Not verified to have an unsloth 4-bit preset — not checked yet. |
| **Llama-3.1-8B-Instruct** | Meta | Already attempted (EXP-005) via Nebius, broken on merge — not yet retried via the Colab/Unsloth pipeline that worked for Mistral. |
| **GLM-4-9B** | Zhipu AI | Not attempted. Unsloth preset availability not checked. |
| **Gemma-2-9B** | Google | Not attempted. Unsloth preset availability not checked. |
| **InternLM2.5-7B** | Shanghai AI Lab | Not attempted. Unsloth preset availability not checked. |
| **Yi-1.5-9B** | 01.AI | Not attempted. Unsloth preset availability not checked. |

**Honesty note:** "not verified" above means exactly that — I have not confirmed an
`unsloth/*-bnb-4bit` checkpoint exists for these, nor run them. Before spending a Colab
session on any of them, that should be checked first (`hf_hub` search or HF page), same
as was skipped for Phi-3.5 going in and cost EXP-011 a broken run.
