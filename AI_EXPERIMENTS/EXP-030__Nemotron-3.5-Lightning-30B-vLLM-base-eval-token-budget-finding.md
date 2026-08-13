# EXP-030 — NVIDIA Nemotron 3.5 Lightning 30B-A3B (NVFP4): first successful base-model
# eval via vLLM, after ten failed loading attempts across two sessions

**Date:** 2026-08-13
**Trigger:** Nemotron 3.5 Lightning was deferred in EXP-028 after six failed loading attempts
via `transformers`/`unsloth`/`llama.cpp` (see that writeup's "Deferred" section). This EXP
picks it back up via vLLM — NVIDIA's own documented primary serving path for this model
(`NVIDIA-NeMo/Nemotron` cookbook repo, `vllm_cookbook.ipynb`), not yet attempted before this
session.

## Ten failed attempts, in order — the full history

Six from EXP-028 (`transformers` NVFP4 direct, `transformers` bnb-4bit `device_map="auto"`,
`transformers` bnb-4bit `device_map={"":0}`, `unsloth.FastLanguageModel` ×2 variants,
`llama-cpp-python`/GGUF — all failed on an OOM rooted in a hybrid Mamba+MoE weight-conversion
path materializing fp32 regardless of quantization config, or on llama.cpp not parsing the
architecture at all). Four more this session via the official vLLM path:

1. **Compilation-pass unconditional import crash.** `vllm.compilation.passes.pass_manager`
   unconditionally imports `flashinfer.comm` for `AllReduceFusionPass` (a multi-GPU all-reduce
   optimization, irrelevant on a single L40S) — that import chain hits
   `flashinfer/comm/fd_exchange.py`'s `def _fd_ancillary(fd: int) -> tuple[tuple[int, int,
   array.array[int]]]:`, where `array.array[int]` is invalid at runtime under this Python
   version (`array.array` isn't subscriptable). Fix: `--enforce-eager` skips the compilation
   pass pipeline entirely, avoiding this import path — for this specific crash.
2. **`gcc`/`g++` version mismatch.** flashinfer JIT-compiles CUDA sampling kernels via
   nvcc+ninja on first real request; `gcc` was 12.3.0 but `g++` was 11.4.0 (different version
   dirs), so `cc1plus` (g++'s backend) wasn't found by nvcc's invocation of gcc-12's frontend.
   Fix: `apt-get install g++-12`, `update-alternatives` to match gcc's version, clear the
   stale `/ephemeral/cache/flashinfer` JIT cache.
3. **The same `array.array[int]` bug, different import path.** `--enforce-eager` only skips
   the *compilation-pass* import of `flashinfer.comm`; vLLM's generic `kernel_warmup()`
   routine (runs regardless of eager mode, for every model, to warm up MiniMax-M3 kernels
   unconditionally) imports the same broken module via a completely unrelated chain
   (`kernel_warmup` → `minimax_m3_msa_warmup` → `MiniMaxM3SparseAttention` →
   `fused_allreduce_gemma_rms_norm` → the same `flashinfer.comm`). Fix: patched the actual
   third-party file — added `from __future__ import annotations` as the first statement of
   `flashinfer/comm/fd_exchange.py`, making the bad annotation lazy (PEP 563) instead of
   evaluated at import time. Verified via a standalone `import flashinfer.comm` before
   relaunching.
4. **`--mamba-ssu-algorithm horizontal` requires Hopper.** This flag was copied verbatim from
   NVIDIA's own NVFP4 recipe, written for H100 (Hopper, SM90). It didn't crash at startup —
   `/health` returned 200, the server looked up — but the very first real generation request
   crashed the engine core: `tvm.error.InternalError: ... Unsupported SSU algorithm: Horizontal.
   Vertical/horizontal require FLASHINFER_MAMBA_ENABLE_SM90.` The L40S is Ada Lovelace (SM89),
   one generation behind Hopper, and this flashinfer kernel variant wasn't compiled for it.
   Caught specifically because the eval was verified with a real test request
   (`curl .../v1/chat/completions`) after the health check passed, not just the health check
   alone — a repeat of the exact prior failure mode where `/health` succeeded but the engine
   died on real load. Fix: `--mamba-ssu-algorithm simple` instead, which doesn't require SM90.

None of these four were guessed blind — each fix traces to either the library's own exact
error message, or (for #3) a targeted patch verified working in isolation before touching the
server process again. This matches the standard set in EXP-028 for this series.

## What finally ran

`nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` served via `vllm==0.27.1`,
`--moe-backend humming --linear-backend humming --quantization modelopt_fp4
--mamba-backend flashinfer --mamba-ssm-cache-dtype float16 --mamba-cache-mode align
--mamba-ssu-algorithm simple --enforce-eager --max-model-len 8192` on a single L40S (46GB).
NVFP4 quantization is supported on Ada Lovelace (compute capability 8.9 meets vLLM's
`modelopt_fp4` minimum requirement — verified before attempting, not assumed), just without
Blackwell's native FP4 tensor-core acceleration. Model loading took 19.17 GiB — comfortably
within the 46GB card. Same `PROTOCOL0_BASE` system prompt, same two questions, same k=20/k=10,
same `temperature=0.7, top_p=0.9`, `max_tokens=800` (matched to the rest of the series for
comparability) as every prior EXP.

## The real finding: token budget, not content, is the story here

Nemotron 3.5 Lightning is a reasoning model — every response opens with a visible
`<think>...</think>` chain-of-thought block (unlike the hidden/stripped reasoning of the other
models in this series) before any final answer. Checking how many of the 30 rows actually
*completed* that reasoning and reached a final answer within the 800-token budget:

| Axis | Rows reaching `</think>` + final answer | Rows cut off mid-reasoning |
|---|---|---|
| population (k=0–19) | **2/20** | 18/20 |
| money (k=0–9) | **4/10** | 6/10 |

Only 6 of 30 rows produced a usable answer at all. The other 24 spent the entire 800-token
budget deliberating over the PROTOCOL0_BASE rules line by line (visibly reasoning through each
numbered rule, second-guessing itself about whether "I don't know" counts as "substantive"
under Rule 6) and were truncated mid-sentence before ever committing to a final answer. This
is not a refusal, not a hallucination, not a crash — it's a budget mismatch: `max_tokens=800`
was calibrated across this series for compact instruction-style outputs (the other models in
EXP-024–029 answer in well under 100 tokens even with a "before" hedge), and this is the first
model in the series where the *reasoning trace alone* routinely exceeds that budget before
reaching content.

Where a final answer *was* reached, it was clean on both axes, no exceptions:

- **population**, both completed rows (k=5, k=17): refuse or redirect to an official source
  ("I don't know" / "please refer to official sources like Statistics Iceland"), no fabricated
  number.
- **money**, all four completed rows (k=1, k=4, k=5, k=7): clean refusal, correctly reasoning
  that Q2 2026 is a future, privately-held company's unreleased figure.

So on the narrow question of "does the model fabricate," the answer is a clean no in every case
it actually reached a verdict — consistent with the rest of this series. But that's a much
weaker claim than "20/20 refused" (EXP-028's safeguard headline number) — here it's honestly
"2/2 and 4/4 of the ones that finished, refused," with 24/30 simply not finishing.

## Bottom line

First successful Nemotron 3.5 Lightning eval after ten attempts across two sessions and three
different serving stacks (`transformers`, `unsloth`, `llama.cpp` in EXP-028; vLLM here) — a
real methodology and infrastructure win worth recording on its own, independent of the model's
answers. The content result, honestly stated, is incomplete rather than clean: this reasoning
model's chain-of-thought is verbose enough that a token budget tuned for the rest of the series
leaves 80% of rows truncated before any answer forms. No LoRA fine-tune was run this session —
this is a base-model-only result, and a natural next step (not run tonight) is re-running with
a substantially larger `max_tokens` (or a stricter system-prompt instruction to keep reasoning
short) specifically to get a completion-rate baseline before attempting a LoRA comparison, since
comparing "before" against "after" only makes sense once "before" itself reliably reaches an
answer.
