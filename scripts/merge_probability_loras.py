#! /home/shadeform/sipa_ft/bin/python
"""Merge the 3 per-group probability-estimator LoRA specialists into one
adapter (equal-weight linear combination via PEFT add_weighted_adapter), same
pattern as merge_vuln_loras.py (EXP-031). Run AFTER all 3 specialists finish
training and BEFORE the post-merge eval."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
GROUPS = ["vulnerability", "deletion", "sensitive_publication"]
OUT_DIR = "/home/shadeform/specialist-prob-merged-qwen25-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
base = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

first_dir = f"/home/shadeform/specialist-prob-{GROUPS[0]}-qwen25-lora"
model = PeftModel.from_pretrained(base, first_dir, adapter_name=GROUPS[0])
for g in GROUPS[1:]:
    model.load_adapter(f"/home/shadeform/specialist-prob-{g}-qwen25-lora", adapter_name=g)

weights = [1.0 / len(GROUPS)] * len(GROUPS)
model.add_weighted_adapter(adapters=GROUPS, weights=weights, adapter_name="merged", combination_type="linear")
model.set_adapter("merged")

model.save_pretrained(OUT_DIR, selected_adapters=["merged"])
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE merged probability-estimator adapter -> {OUT_DIR}")
