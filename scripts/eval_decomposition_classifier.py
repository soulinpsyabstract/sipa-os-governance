#! /home/shadeform/venv/bin/python
"""Decomposition-classifier eval: BEFORE (base Qwen2.5-7B-Instruct, no LoRA)
vs AFTER (with the decomposition-classifier LoRA), on decomposition_sft_eval_v1.jsonl
-- the held-out records train_decomposition_classifier_qwen25.py never sees.
Same before/after + n-repeated-sampling convention as EXP-037 v2/EXP-036
(n=10 samples/record at temperature=0.7, majority vote, full per-sample
distribution saved) -- a single greedy pass cannot distinguish "reliably
correct" from "got lucky once."

Usage: eval_decomposition_classifier.py before|after [n_samples]
"""
import json
import sys
from collections import Counter

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
LORA_DIR = "/home/shadeform/decomposition-classifier-qwen25-lora"
EVAL_PATH = "/home/shadeform/decomposition_sft_eval_v1.jsonl"


def load_model(mode: str):
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto")
    if mode == "after":
        model = PeftModel.from_pretrained(model, LORA_DIR)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    return model, tokenizer


def parse(gen: str) -> str:
    gen = gen.strip().upper()
    if "BAD" in gen:
        return "BAD"
    if "GOOD" in gen:
        return "GOOD"
    return "UNCLEAR"


def sample_once(model, tokenizer, prompt: str) -> tuple[str, str]:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=5, do_sample=True, temperature=0.7)
    raw = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return raw, parse(raw)


def classify_repeated(model, tokenizer, messages: list, n_samples: int) -> dict:
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    samples = []
    for _ in range(n_samples):
        raw, label = sample_once(model, tokenizer, prompt)
        samples.append({"raw": raw, "label": label})
    counts = Counter(s["label"] for s in samples)
    majority_label, majority_count = counts.most_common(1)[0]
    return {
        "samples": samples, "majority": majority_label, "majority_count": majority_count,
        "n": n_samples, "counts": dict(counts),
    }


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("before", "after"):
        print("Usage: eval_decomposition_classifier.py before|after [n_samples]")
        sys.exit(1)
    mode = sys.argv[1]
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    items = [json.loads(l) for l in open(EVAL_PATH)]
    model, tokenizer = load_model(mode)

    results = []
    correct = tp = tn = fp = fn = 0
    for it in items:
        messages = it["messages"][:2]  # system + user only, drop the gold assistant answer
        true_label = it["label"]
        cls = classify_repeated(model, tokenizer, messages, n_samples)
        pred = cls["majority"]
        is_correct = pred == true_label
        correct += is_correct
        if true_label == "BAD" and pred == "BAD":
            tp += 1
        elif true_label == "GOOD" and pred == "GOOD":
            tn += 1
        elif true_label == "GOOD" and pred == "BAD":
            fp += 1
        elif true_label == "BAD" and pred == "GOOD":
            fn += 1
        results.append({
            "id": it["id"], "goal": it["goal"], "label": true_label, "pred": pred, "correct": is_correct,
            "majority_count": cls["majority_count"], "n_samples": n_samples,
            "counts": cls["counts"], "samples": cls["samples"],
        })
        consistency = f"{cls['majority_count']}/{n_samples}"
        print(f"{it['id']}: true={true_label} majority={pred} ({consistency}) counts={cls['counts']} {'OK' if is_correct else 'WRONG'}")

    n = len(items)
    out_path = f"/home/shadeform/eval_decomposition_results_{mode}.json"
    with open(out_path, "w") as f:
        json.dump({
            "mode": mode, "n": n, "n_samples_per_record": n_samples,
            "correct": correct, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "results": results,
        }, f, indent=2)

    unanimous = sum(1 for r in results if r["majority_count"] == n_samples)
    print(f"\n=== {mode.upper()}: {correct}/{n} = {correct/n*100:.1f}% (majority vote, n={n_samples} samples/record) ===")
    print(f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"Unanimous records (all {n_samples} samples agreed): {unanimous}/{n}")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
