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

## Investigation log (forensic trace — every step, not just the conclusion)

1. Job `ftjob-d0df1d39ff944edda626055f8db0fd60` created via `POST /v1/fine_tuning/jobs`
   with `training_file` uploaded via `POST /v1/files` (purpose=fine-tune), model
   `meta-llama/Llama-3.1-8B-Instruct`, LoRA hyperparameters as above. Polled
   `GET /v1/fine_tuning/jobs/{id}` until `status: succeeded`.
2. `result_files` on the finished job listed 18 file IDs. Queried each individually via
   `GET /v1/files/{id}` to read `filename` — found 3 checkpoint directories
   (`ftckpt_6430ff22...`, `ftckpt_c8b2aed5...`, `ftckpt_a3e5111e...`), one per epoch, each
   with `adapter_config.json`, `adapter_model.safetensors`, `chat_template.jinja`,
   `tokenizer.json`, `tokenizer_config.json`, `checkpoint.meta`.
3. Downloaded each checkpoint's `checkpoint.meta` (a small JSON) to read `step_number` and
   `metrics.train_loss`, to identify the *final* checkpoint rather than guessing from file
   order: step 2 (loss 3.745) → step 4 (loss 3.614) → step 6 (loss 3.484, lowest, final).
   Selected `ftckpt_a3e5111e-7be9-4774-bac9-4b5b2051a8a4`.
4. First download attempt via `GET /v1/files/{id}/content` produced **0-byte files** for
   the two large binaries (`adapter_model.safetensors`, `tokenizer.json`) while small JSON
   files downloaded fine. Diagnosed with `curl -v` (no `-L`): the endpoint returns a
   redirect to a presigned S3 URL (`storage.eu-north1.nebius.cloud/ft-data/runtime/
   checkpoints/...`) that plain `curl -o` without `-L` doesn't follow, silently truncating
   output. Fixed by adding `-L`; re-downloaded both files, verified byte sizes matched the
   `bytes` field reported by the Files API exactly (83,938,576 and 17,209,920).
5. Since `meta-llama/Llama-3.1-8B-Instruct` returned 403 on every available HF token
   (verified: `curl -H "Authorization: Bearer $TOKEN" .../resolve/main/config.json` → 403
   on 3 separate tokens, cross-checked each token was itself valid via
   `/api/whoami-v2` → 200), substituted `NousResearch/Meta-Llama-3.1-8B-Instruct` (a known
   ungated mirror, confirmed accessible via the same config.json check → 307) as the base
   model for merging.
6. Ran the benchmark script (base vs. adapter, same 5-test suite as EXP-002/004) on
   Lightning L4. **Base model: 3/5 (60%), coherent responses.** **Fine-tuned: 3/5 (60%)
   headline score, but every response was gibberish** — the automatic checks happened to
   pass on garbage text by coincidence (short, no keyword matches), which is exactly why
   step 7 (manual reading of raw output, not just the score) matters.
7. Manually read the raw fine-tuned responses — confirmed genuine incoherence, not a
   formatting artifact (e.g. `"header headers headers Trem269 Vacuum..."`). Checked the
   run's stderr log and found: `Ignoring clean_up_tokenization_spaces=True for BPE
   tokenizer TokenizersBackend` — a transformers warning naming a non-existent tokenizer
   class, `TokenizersBackend`.
8. Inspected the downloaded `tokenizer_config.json` directly: confirmed
   `"tokenizer_class": "TokenizersBackend"` — matching the exact bug class already
   documented in EXP-001 (GGUF conversion producing the same kind of bogus tokenizer-class
   label). Fetched the NousResearch mirror's own `tokenizer_config.json` via
   `.../raw/main/tokenizer_config.json` to find the *correct* value for this architecture:
   `"PreTrainedTokenizerFast"`.
9. Patched the local copy of `tokenizer_config.json`, `scp`'d it to the training machine
   (overwriting the broken one in place), and **re-read the file over SSH immediately
   after the copy** to confirm the patched value actually landed on disk before re-running
   anything (not just trusting `scp`'s exit code) — this is the same discipline used
   throughout this log to avoid reporting an unverified fix as done.
10. Re-ran the full benchmark suite. **Still gibberish** — a different garbage pattern than
    before (`"احتاحتτανاحتاحتameleon..."` vs. the earlier `"header headers..."`), which
    itself is informative: a different-but-still-nonsensical output after only changing
    a metadata label confirms the label wasn't the actual cause, ruling out that specific
    hypothesis cleanly rather than leaving it ambiguous.
11. Stopped further fix attempts at this point (per the project's "one attempt, then
    report" rule for debugging) and wrote up the finding as closed/broken rather than
    continuing to try more workarounds blindly.

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
