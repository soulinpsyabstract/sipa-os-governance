#! /home/shadeform/venv/bin/python
"""Binary SFT: Qwen2.5-7B-Instruct -- vulnerability gate specialist, ONE group.
Usage: train_vuln_specialist_pergroup.py <group_slug>
e.g.:  train_vuln_specialist_pergroup.py 01_secrets_credentials

Specialist-per-group-then-merge convention: run this once per group (6x),
each producing its own adapter, before merging. Same SFT settings as the
combined-group run (r=16/alpha=32/dropout=0.05, positive-only)."""
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

if len(sys.argv) != 2:
    raise SystemExit("usage: train_vuln_specialist_pergroup.py <group_slug>")
GROUP = sys.argv[1]

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
DATA_PATH = f"/home/shadeform/per_group/{GROUP}_train.jsonl"
OUT_DIR = f"/home/shadeform/specialist-vuln-{GROUP}-qwen25-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)
model.enable_input_require_grads()
model.print_trainable_parameters()

raw = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"[{GROUP}] Examples: {len(raw)}")
def fmt(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}
ds = raw.map(fmt)

trainer = SFTTrainer(
    model=model, processing_class=tokenizer, train_dataset=ds,
    args=SFTConfig(output_dir=OUT_DIR, dataset_text_field="text", max_length=768, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="no", optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE vuln-gate specialist [{GROUP}]")
