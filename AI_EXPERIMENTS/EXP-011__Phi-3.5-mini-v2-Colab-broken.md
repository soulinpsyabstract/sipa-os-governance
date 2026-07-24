# EXP-011 · Phi-3.5-mini-instruct v2 (Colab T4, Unsloth) — broken, not a Protocol-0 result

**Date:** 2026-07-24
**Status:** closed — **infrastructure/compatibility failure, not evaluable**, following the
same precedent as EXP-005 (a broken artifact is reported as broken, not spun as a result)

## Setup

Same pipeline as EXP-010 (Mistral-7B v2, which worked correctly): Unsloth `FastLanguageModel`
+ LoRA (r=16, alpha=32, q/k/v/o_proj, dropout=0.05), 503-example dataset, 3 epochs, Colab
free-tier T4, driven headlessly via the same HTTP exec-bridge.

- **Base model:** `unsloth/Phi-3.5-mini-instruct-bnb-4bit`
- **Training:** completed without crashing — 189 steps, `train_runtime: 1162.6s` (~19 min)

## What went wrong

**Training loss never converged — flat and high for the entire run.** Loss values across
all 189 steps stayed in the 7.2–7.7 range from step 1 to the end (`train_loss: 7.467`
final), compared to EXP-010's Mistral run which went from ~2.0 down to ~1.1 over the same
number of steps. `grad_norm` was also anomalously small throughout (0.002–0.05, vs
Mistral's 2.5–3.2) — consistent with almost no real gradient signal reaching the model,
not consistent with normal training on this dataset/hyperparameters.

**The benchmark crashed on the very first prompt of the BASE model suite — before any
fine-tuned weights were even involved.** The base model's raw output for the first test
prompt was incoherent noise, not language:

> *"b.am, [orbit showing{,respaれ} parte ?�_ T elsus-다х像 sophour_not?R, BERÄLLEZ R.m((101), a Five.Ra, and no_to dev-1o-faczedadem. )-first,i to toamever(0, NO as three ...ayEx$content0ur'esensndu tip movementgr(Be; —exp to is of and) was;we_t...0...^{}) handle:0 times now..."*

Generation then hit a fatal CUDA error partway through: `Assertion "probability tensor
contains either inf, nan or element < 0" failed` → `torch.AcceleratorError: CUDA error:
device-side assert triggered`. This is a NaN/Inf appearing in the sampling probability
distribution — a numerical-instability crash, not a normal generation failure. Once a
CUDA device-side assert fires, the CUDA context for that process is permanently corrupted;
the benchmark process could not continue and had to be treated as failed, not retried
in-process.

## Why this is being closed as broken, not scored

**The garbage output and the crash both happened on the unmodified base model**, before
the LoRA adapter was loaded at all. This means the failure is not something the fine-tune
caused — the underlying `unsloth/Phi-3.5-mini-instruct-bnb-4bit` checkpoint itself
produces incoherent, numerically unstable output on this exact software stack (Unsloth
2026.7.5, transformers 4.53.1, Torch 2.11.0+cu128, Tesla T4). The training run's flat,
never-decreasing loss is consistent with this same instability being present from the
first training step too — the model was likely never in a state where meaningful learning
could happen, regardless of dataset or hyperparameters.

**This is the same category of finding as EXP-005** (Llama-3.1-8B via Nebius: "job
succeeded, but downloaded adapter produces incoherent output when merged locally — broken,
not a Protocol-0 result"). A benchmark score would be actively misleading here — a "FAIL"
in either direction would say nothing about Protocol-0 compliance, only about a broken
checkpoint/library combination. No score is reported for this reason.

## What is NOT concluded here

- **Not concluded that Phi-3.5-mini can't be fine-tuned for this task** — EXP-007
  (Phi-3.5-mini on Lightning AI, plain transformers/peft, no Unsloth) trained and
  benchmarked successfully with normal loss values (0.6–1 range) on the same kind of
  dataset. The variable that changed here is the training/inference stack
  (`unsloth/Phi-3.5-mini-instruct-bnb-4bit` + Unsloth's kernels on this exact library
  version combination), not the model family itself.
- **Root cause not fully diagnosed** — plausible candidates, none confirmed: a
  known Unsloth/transformers version-compatibility gap specific to Phi-3.5 (the startup
  banner logged `"Unsloth: Fast Llama patching"` — Unsloth internally maps Phi-3.5 onto
  its Llama-architecture kernels via `auto_mapping: base_model_class: LlamaForCausalLM`,
  which is a legitimate optimization for other models but may not be safe for Phi-3.5's
  actual attention/rotary implementation on this specific version); a `bfloat16=FALSE`
  fallback to a less numerically stable dtype was logged at model load (visible in the
  banner: `"Bfloat16 = FALSE"`), which combined with 4-bit quantization on a T4 (no
  native bf16 support on this GPU class) is a known source of NaN/Inf during generation
  for some checkpoints.
- **Not retried within this session** given time constraints (operator traveling with
  degrading connectivity) — flagged as a TODO for a future attempt: either use
  `unsloth/Phi-3.5-mini-instruct` (non-pre-quantized, quantize at load time instead of
  using the pre-quantized `-bnb-4bit` repo) or pin an earlier Unsloth/transformers version
  combination known to work with this model family, and re-verify the base model alone
  generates coherent text *before* attempting any fine-tuning run.

## Conclusion

Recorded as a broken infrastructure result, consistent with this repo's charter of
documenting negative and inconclusive outcomes rather than omitting or spinning them.
Of the 4 approved v2 re-runs (Qwen2.5-7B, Mistral-7B, Phi-3.5-mini, and gpt-4o already
done via Azure in EXP-008), this closes out Phi-3.5-mini as unevaluable on this specific
attempt, not as a completed comparison.
