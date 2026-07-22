# EXP-005 · Llama-3.1-8B-Instruct + LoRA (Nebius AI Studio)

**Date:** 2026-07-22
**Status:** closed — **broken adapter portability, not a Protocol-0 result**

## Setup

- **Base model:** `meta-llama/Llama-3.1-8B-Instruct`, via Nebius AI Studio's managed
  fine-tuning API (`api.tokenfactory.nebius.com`)
- **Dataset:** same 302-example real dataset as EXP-002/004, confirmed byte-identical
  (569,903 bytes) on upload
- **Training:** LoRA (r=16, alpha=32, dropout=0.05, `q/k/v/o/gate/up/down_proj` — Nebius's
  default target-module set is broader than the q/k/v/o-only config used on Lightning),
  3 epochs, packing enabled. **Job `ftjob-d0df1d39ff944edda626055f8db0fd60`: succeeded**,
  330,504 trained tokens, 6/6 steps (packing folds the 302 short examples into few,
  long ~8k-token sequences — not a sign of truncation, verified against the exact uploaded
  file size).

## Why this experiment is broken, not evaluated

Nebius has deprecated the shared per-token LoRA-inference path (see EXP-003) — the only
free option is to download the trained checkpoint's raw files and serve it elsewhere.
Downloaded: `adapter_config.json`, `adapter_model.safetensors` (80MB), `chat_template.jinja`,
`tokenizer.json` (17MB), `tokenizer_config.json` — the final checkpoint
(`ftckpt_a3e5111e-7be9-4774-bac9-4b5b2051a8a4`, step 6, lowest train_loss 3.484).

Since `meta-llama/Llama-3.1-8B-Instruct` itself is gated on HuggingFace (403 on all
available account tokens), the merge used `NousResearch/Meta-Llama-3.1-8B-Instruct` — a
long-standing, widely-used ungated mirror of the identical weights — as the base model,
while loading the tokenizer from the downloaded Nebius adapter files.

**Result: the fine-tuned model's output is pure word-salad garbage** ("header headers
headers Trem269 Vacuum...", "احتاحتτανاحتاحتameleon...") — not a Protocol-0 compliance
question, the model is not producing coherent text at all. The base model (no adapter,
same benchmark run) answered normally and scored 3/5 (60%), confirming the base setup
itself (NousResearch mirror + benchmark script) works correctly — the corruption is
specific to combining it with the downloaded adapter/tokenizer.

**One fix attempted and ruled out:** Nebius's exported `tokenizer_config.json` had
`"tokenizer_class": "TokenizersBackend"` — not a real transformers class name, and
identical in kind to the exact bug found in EXP-001's GGUF conversion. Patched to the
correct value (`PreTrainedTokenizerFast`, confirmed against the NousResearch mirror's own
config) and re-ran. **Confirmed the file was actually patched on the training machine
before rerunning** — the garbage output persisted regardless, with a different (but
equally incoherent) gibberish pattern. This rules out the tokenizer *class label* as the
root cause; the real issue is a deeper vocabulary/token-ID mapping mismatch between
whatever tokenizer Nebius actually trained the adapter against internally and the
tokenizer bundled with the ungated mirror used for merging.

## Conclusion

- **Not a "no improvement" or "regression" result** — the fine-tuned model is simply
  broken when served this way, so no Protocol-0 comparison is meaningful here.
- **Second independent confirmation of a pattern first seen in EXP-001**: a fine-tuning
  platform's own export/serving path can work fine internally, while the exported
  artifact (GGUF in EXP-001, downloaded LoRA checkpoint here) produces incoherent output
  when reapplied outside that platform's own stack — via two *completely unrelated*
  technical paths (llama.cpp GGUF conversion vs. direct PEFT/transformers merge), which
  makes this look like a genuine cross-platform LoRA-portability risk worth treating as a
  standing methodology caveat, not a one-off bug.
- Root cause not fully diagnosed (would need Nebius's own internal tokenizer/vocab
  artifact to compare against, which isn't exposed) — not pursued further given the
  "no guessing loops" principle after one fix attempt failed. Marked closed as
  inconclusive/broken, consistent with how EXP-003 was handled.
- **Practical takeaway for future experiments:** when downloading a fine-tuned adapter
  from a hosted platform for local use, verify the base model's tokenizer vocabulary size
  and special-token IDs match exactly between the platform's training environment and the
  local merge environment *before* trusting any benchmark result — a coherence smoke test
  (a single unconstrained completion) should be run immediately after merging, before
  running the full benchmark suite.
