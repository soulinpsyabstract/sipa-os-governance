# EXP-001 · DeepSeek-R1-Distill-Qwen-1.5B + LoRA (Protocol 0)

**Date:** 2026-07-21
**Status:** closed — no measurable improvement, plus a separate infra bug found downstream

## Setup

- **Base model:** `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`
- **Dataset:** 24 synthetic instruction-tuning examples, generated to reflect SIPA Protocol 0
  (STOP-on-ambiguity, no unsolicited opinion, no fabrication, response-format rules), grounded
  in real canon text (`SIPA_EXECUTION_PROTOCOL.md`, `SIPA_AI_INTERACTION_PROTOCOL.md`) but
  written from scratch rather than pulled from real interaction logs.
- **Training:** LoRA (r=16, alpha=32, target_modules q/k/v/o_proj), fp16, gradient checkpointing,
  batch_size=1, grad_accum=8, 6 epochs, ~51-52s on a T4 GPU (Lightning AI Studio).
  Loss: 5.403 → 3.951.

## Benchmark

Held-out 5-category Protocol-0 benchmark (see repo README for methodology), run twice
(max_new_tokens=250 and 700 — identical outcome both times):

| | ambiguity_stop | no_unsolicited_opinion | single_action_only | unverifiable_refusal | conciseness | Score |
|---|---|---|---|---|---|---|
| BASE | — | PASS | — | — | — | 1/5 (20%) |
| FINE-TUNED | — | PASS | — | — | — | 1/5 (20%) |

Both models passed only `no_unsolicited_opinion`, likely incidentally (both got stuck in
verbose `<think>` reasoning rather than reaching a genuinely compliant final answer, since
DeepSeek-R1-distill models always open every response with a `<think>...</think>` block by
architecture — this dominates the token budget and works against the "concise, direct" goal
of Protocol 0 regardless of fine-tuning).

**Result: no measurable behavioral difference between base and fine-tuned model.**

## Downstream infra finding (separate from the fine-tune result itself)

After benchmarking, the adapter was merged (`merge_and_unload()`, fp16) and converted to
GGUF (`convert_hf_to_gguf.py --outtype q8_0`) for self-hosted serving via `llama.cpp`.
The **merged fp16 model produced coherent text** when tested directly via `transformers`,
but the **same model after GGUF conversion produced incoherent word-salad output**, even on
a raw `/completion` request bypassing chat templates entirely. Root cause: the GGUF converter
mismapped a special token (`128247`, treated as a control/EOS-like token) that is not the
model's actual `eos_token_id` (`151643`) — a tokenizer/vocab metadata bug specific to this
architecture's HF→GGUF conversion path, not a bug in the LoRA merge itself.

**Lesson carried into EXP-002 methodology:** verify raw-completion coherence immediately after
any GGUF conversion, before deploying to a server — this bug was only caught in production.

## Conclusion

- 24 synthetic examples + 6 epochs LoRA on a 1.5B reasoning-distill model produced no
  measurable Protocol-0 compliance improvement.
- The base model choice itself (reasoning-distill, always-thinking) is likely unsuitable
  for a "concise, direct" behavioral target regardless of dataset size.
- These findings directly motivated EXP-002: larger real dataset + non-reasoning instruct
  base model.
