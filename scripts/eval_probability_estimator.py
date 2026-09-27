#! /home/shadeform/sipa_ft/bin/python
"""EXP-046 eval: BEFORE (base Qwen2.5-7B-Instruct) vs AFTER (base + specialist
or merged LoRA), on <group>_eval.jsonl (20 held-out records/group, never
touched by training).

Regression task (probability_estimate is continuous, 0.0-1.0), not binary --
so the EXP-037/045 majority-vote convention doesn't apply directly. Instead:
n=5 samples/record at temperature=0.7 (repeated sampling still matters here --
one generation can misparse or land on a fluke value), report the MEAN of the
successfully-parsed samples as the record's prediction, MAE against gold, and
the fraction of records within 0.15 absolute error (matching the ~0.2-0.95
observed spread this dataset's own README documents). Raw per-sample text
saved, not just the parsed number, so a parsing-faithfulness audit doesn't
need a re-run.

Usage: eval_probability_estimator.py <adapter_dir_or_none> <group> [n_samples]
  adapter_dir: path to a LoRA adapter (specialist or merged), or the literal
               string "base" for BEFORE (no adapter).
"""
import json
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
DATA_DIR = "/home/shadeform/per_group"


def load_model(adapter: str):
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto")
    if adapter != "base":
        model = PeftModel.from_pretrained(model, adapter)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    return model, tokenizer


def parse_prob(gen: str):
    m = re.search(r'"probability_estimate"\s*:\s*([0-9.]+)', gen)
    if not m:
        return None
    try:
        v = float(m.group(1))
        return v if 0.0 <= v <= 1.0 else None
    except ValueError:
        return None


def sample_once(model, tokenizer, prompt: str) -> tuple[str, float | None]:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=80, do_sample=True, temperature=0.7)
    raw = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return raw, parse_prob(raw)


def main():
    if len(sys.argv) < 3:
        print("Usage: eval_probability_estimator.py <adapter_dir_or_base> <group> [n_samples]")
        sys.exit(1)
    adapter = sys.argv[1]
    group = sys.argv[2]
    n_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    mode = "before" if adapter == "base" else "after"

    items = [json.loads(l) for l in open(f"{DATA_DIR}/{group}_eval.jsonl")]
    model, tokenizer = load_model(adapter)

    results = []
    abs_errors = []
    within_015 = 0
    parse_failures = 0
    for it in items:
        messages = it["messages"][:2]
        gold = it["probability_estimate"]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        samples = []
        for _ in range(n_samples):
            raw, val = sample_once(model, tokenizer, prompt)
            samples.append({"raw": raw, "parsed": val})
        parsed_vals = [s["parsed"] for s in samples if s["parsed"] is not None]
        if not parsed_vals:
            parse_failures += 1
            pred_mean = None
            err = None
        else:
            pred_mean = sum(parsed_vals) / len(parsed_vals)
            err = abs(pred_mean - gold)
            abs_errors.append(err)
            if err <= 0.15:
                within_015 += 1
        results.append({
            "id": it["id"], "group": group, "gold": gold, "pred_mean": pred_mean,
            "abs_error": err, "n_parsed": len(parsed_vals), "n_samples": n_samples,
            "samples": samples,
        })
        print(f"{it['id']}: gold={gold:.2f} pred_mean={pred_mean if pred_mean is None else round(pred_mean,2)} err={err if err is None else round(err,3)} parsed={len(parsed_vals)}/{n_samples}")

    n = len(items)
    mae = sum(abs_errors) / len(abs_errors) if abs_errors else None
    adapter_tag = "base" if adapter == "base" else adapter.rstrip("/").split("/")[-2 if adapter.rstrip("/").endswith("merged") else -1]
    out_path = f"/home/shadeform/eval_probability_results_{mode}_{adapter_tag}_{group}.json"
    with open(out_path, "w") as f:
        json.dump({
            "mode": mode, "adapter": adapter, "group": group, "n": n, "n_samples_per_record": n_samples,
            "mae": mae, "within_0.15": within_015, "parse_failures": parse_failures,
            "results": results,
        }, f, indent=2)

    print(f"\n=== {mode.upper()} [{group}]: MAE={mae if mae is None else round(mae,3)}, within_0.15={within_015}/{n}, parse_failures={parse_failures}/{n} ===")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
