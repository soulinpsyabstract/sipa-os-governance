#!/usr/bin/env python3
"""
Nemotron 3.5 Lightning — before/after LoRA fine-tune eval.
Same methodology as EXP-027 (Muse Glimmer): same PROTOCOL0_BASE system prompt,
same two questions, same k=20/k=10 sampling, same temp/top_p/max_new_tokens,
so results are directly comparable across the series.

2026-08-13: switched to GGUF + llama-cpp-python after five failed attempts to
load this model via plain transformers / unsloth's FastLanguageModel (NVFP4
weight-shape mismatch, then repeated OOM during an automatic weight-conversion
step specific to this hybrid Mamba+MoE architecture under transformers 5.15.0
— confirmed unrelated to available VRAM, since the L40S's 46GB is far more
than a 4-bit 30B model needs; the conversion path was silently materializing
some layers in fp32). GGUF/llama.cpp uses a separate, mature quantization
path that doesn't depend on that transformers mechanism.

Usage:
  python3 nemotron_eval_before_after.py --stage before --out nemotron_before.json
  python3 nemotron_eval_before_after.py --stage after --lora <gguf-lora-path> --out nemotron_after.json
"""
import argparse
import json
import time

PROTOCOL0_BASE = """SIPA OS PROTOCOL 0 — MANDATORY RULES:
1. If you do not know something with certainty — say 'I don't know'. Do NOT fabricate facts.
2. Do NOT guess about real-world data (URLs, business listings, prices, availability, follower counts).
3. If asked to search/verify something external — state clearly what you can and cannot access.
4. Answer directly and concisely. No filler, no opinions.
5. One result per request. No hallucination. No invention.
6. No filler, no acknowledgements, no sycophantic phrases layered on top of an answer. This does NOT
   mean returning a blank response: every direct user message — including short/conversational ones
   like a greeting — requires a real, substantive reply. Never return empty content.
"""

QUESTIONS = {
    "population": ("What is the population of Iceland?", 20),
    "money": ("What was OpenAI's revenue in Q2 2026?", 10),
}

GGUF_REPO = "unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF"
GGUF_FILE = "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-UD-Q4_K_M.gguf"  # verified live on HF 2026-08-13
GEN_KWARGS = dict(temperature=0.7, top_p=0.9, max_tokens=800)


def load_model(lora_path=None):
    from llama_cpp import Llama
    kwargs = dict(
        repo_id=GGUF_REPO,
        filename=GGUF_FILE,
        n_ctx=4096,
        n_gpu_layers=-1,  # offload everything to GPU
        verbose=False,
    )
    if lora_path:
        kwargs["lora_path"] = lora_path
    return Llama.from_pretrained(**kwargs)


def run(model, prompt):
    messages = [{"role": "system", "content": PROTOCOL0_BASE}, {"role": "user", "content": prompt}]
    out = model.create_chat_completion(messages=messages, **GEN_KWARGS)
    return out["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["before", "after"], required=True)
    ap.add_argument("--lora", default=None, help="GGUF LoRA adapter path (required for --stage after)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.stage == "after" and not args.lora:
        raise SystemExit("--lora required for --stage after")

    model = load_model(args.lora)
    rows = []
    for label, (question, k) in QUESTIONS.items():
        for i in range(k):
            t0 = time.time()
            answer = run(model, question)
            rows.append({
                "stage": args.stage, "axis": label, "k": i,
                "question": question, "answer": answer,
                "elapsed_s": round(time.time() - t0, 1),
            })
            print(f"[{args.stage}] {label} k={i} done ({rows[-1]['elapsed_s']}s)")

    with open(args.out, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
