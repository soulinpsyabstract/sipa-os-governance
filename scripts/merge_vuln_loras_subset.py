#! /home/shadeform/venv/bin/python
"""Merge an arbitrary SUBSET of the 6 per-group vuln-gate LoRA specialists,
for ablation: find where the injection-stresstest degradation starts by
merging 2 at a time before jumping to all 6.

Usage: merge_vuln_loras_subset.py <model_tag> <group1> <group2> [group3 ...]
e.g.:  merge_vuln_loras_subset.py qwen25 06_stop_gate_pressure 01_secrets_credentials

Output dir name encodes the exact combo: specialist-vuln-merged-<g1>+<g2>[+...]-<model_tag>-lora
"""
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

if len(sys.argv) < 4:
    raise SystemExit("usage: merge_vuln_loras_subset.py <model_tag> <group1> <group2> [group3 ...]")
MODEL_TAG = sys.argv[1]
GROUPS = sys.argv[2:]

MODEL_IDS = {
    "qwen25": "Qwen/Qwen2.5-7B-Instruct",
    "hermes43": "NousResearch/Hermes-4.3-36B",
}
if MODEL_TAG not in MODEL_IDS:
    raise SystemExit(f"unknown model_tag {MODEL_TAG!r}")
MODEL_ID = MODEL_IDS[MODEL_TAG]

combo_tag = "+".join(g.split("_")[0] for g in GROUPS)  # e.g. "06+01"
OUT_DIR = f"/home/shadeform/specialist-vuln-merged-{combo_tag}-{MODEL_TAG}-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")
base = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

first_dir = f"/home/shadeform/specialist-vuln-{GROUPS[0]}-{MODEL_TAG}-lora"
model = PeftModel.from_pretrained(base, first_dir, adapter_name=GROUPS[0])
for g in GROUPS[1:]:
    model.load_adapter(f"/home/shadeform/specialist-vuln-{g}-{MODEL_TAG}-lora", adapter_name=g)

weights = [1.0 / len(GROUPS)] * len(GROUPS)
model.add_weighted_adapter(adapters=GROUPS, weights=weights, adapter_name="merged", combination_type="linear")
model.set_adapter("merged")

model.save_pretrained(OUT_DIR, selected_adapters=["merged"])
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE merged [{combo_tag}] weight={1.0/len(GROUPS):.3f} -> {OUT_DIR}/merged")
