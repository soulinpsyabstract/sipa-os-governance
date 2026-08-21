#! /home/shadeform/venv/bin/python
"""Merge the 6 per-group vuln-gate LoRA specialists into one adapter (equal
weight linear combination via PEFT add_weighted_adapter), then bake it into
the base weights and save as a standalone adapter dir. Run AFTER all 6
specialists finish training and BEFORE the post-merge safety eval."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
GROUPS = [
    "01_secrets_credentials", "02_access_control", "03_injection",
    "04_infra_misconfig", "05_supply_chain", "06_stop_gate_pressure",
]
OUT_DIR = "/home/shadeform/specialist-vuln-merged-qwen25-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
base = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

first_dir = f"/home/shadeform/specialist-vuln-{GROUPS[0]}-qwen25-lora"
model = PeftModel.from_pretrained(base, first_dir, adapter_name=GROUPS[0])
for g in GROUPS[1:]:
    model.load_adapter(f"/home/shadeform/specialist-vuln-{g}-qwen25-lora", adapter_name=g)

weights = [1.0 / len(GROUPS)] * len(GROUPS)
model.add_weighted_adapter(adapters=GROUPS, weights=weights, adapter_name="merged", combination_type="linear")
model.set_adapter("merged")

# Save the merged adapter on its own (not baked into base) so it can still
# be loaded via PeftModel.from_pretrained(base, OUT_DIR) for eval, same as
# every individual specialist.
model.save_pretrained(OUT_DIR, selected_adapters=["merged"])
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE merged adapter -> {OUT_DIR}")
