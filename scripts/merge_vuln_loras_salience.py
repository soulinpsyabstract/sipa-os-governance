#! /home/shadeform/venv/bin/python
"""Merge the 6 per-group vuln-gate LoRA specialists into one adapter, for
vectionlabs/Salience-27B-R5. Third-architecture repeat of merge_vuln_loras_v2.py.

Usage: merge_vuln_loras_salience.py
"""
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

MODEL_ID = "vectionlabs/Salience-27B-R5"
MODEL_TAG = "salience27b"

GROUPS = [
    "01_secrets_credentials", "02_access_control", "03_injection",
    "04_infra_misconfig", "05_supply_chain", "06_stop_gate_pressure",
]
OUT_DIR = f"/home/shadeform/specialist-vuln-merged-{MODEL_TAG}-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")
base = AutoModelForImageTextToText.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
proc = AutoProcessor.from_pretrained(MODEL_ID)
tokenizer = proc.tokenizer
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

first_dir = f"/home/shadeform/specialist-vuln-{GROUPS[0]}-{MODEL_TAG}-lora"
model = PeftModel.from_pretrained(base, first_dir, adapter_name=GROUPS[0])
for g in GROUPS[1:]:
    model.load_adapter(f"/home/shadeform/specialist-vuln-{g}-{MODEL_TAG}-lora", adapter_name=g)

weights = [1.0 / len(GROUPS)] * len(GROUPS)
model.add_weighted_adapter(adapters=GROUPS, weights=weights, adapter_name="merged", combination_type="linear")
model.set_adapter("merged")

# PEFT saves each named adapter into its own subfolder (OUT_DIR/merged/...) --
# eval must point at OUT_DIR/merged, not OUT_DIR (same lesson as EXP-031).
model.save_pretrained(OUT_DIR, selected_adapters=["merged"])
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE merged adapter [{MODEL_TAG}] -> {OUT_DIR}/merged")
