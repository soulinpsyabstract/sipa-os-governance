#! /home/shadeform/venv/bin/python
"""Binary SFT: Muse Glimmer 30B — specialist C/D (non-fabrication pattern), bnb 4-bit + peft.

Adapted from train_hermes3_std.py's proven pattern. Two things differ from that
script, both learned the hard way in EXP-027 (2026-08-10):
  1. Muse Glimmer ships a perception encoder even for text-only use, so it needs
     AutoModelForImageTextToText + AutoProcessor, not AutoModelForCausalLM/AutoTokenizer.
     Loading with the wrong class was one of EXP-027's four failed attempts.
  2. max_new_tokens/effort: EXP-027 found this is a "controllable effort" model that
     visibly deliberates (to=self...to=user markers) — not directly relevant to SFT
     training itself, but flagging in case generation-side eval scripts reuse this file.

LoRA target_modules below match Hermes-3/Llama-family naming (q/k/v/o/gate/up/down
proj) as a starting guess — Muse Glimmer's exact module names haven't been confirmed
yet. The diagnostic print before LoRA setup exists specifically so a naming mismatch
is caught in seconds, not after committing GPU time to a broken config.
"""
import torch, os
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

MODEL_ID = "unsloth/Muse-Glimmer-30B-unsloth-bnb-4bit"
DATA_PATH = "/home/shadeform/specialist_cd_binary_pilot_v2.jsonl"
OUT_DIR = "/home/shadeform/specialist-cd-muse-glimmer-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
processor = AutoProcessor.from_pretrained(MODEL_ID)
tokenizer = processor.tokenizer
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

# Diagnostic: confirm target_modules actually exist before wasting a training run on them
proj_names = sorted(set(n.split(".")[-1] for n, _ in model.named_modules() if n.endswith("proj")))
print(f"Linear proj module names found in model: {proj_names}")
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
missing = [t for t in target_modules if t not in proj_names]
if missing:
    print(f"WARNING: expected target_modules not found: {missing}")
    print("Fix target_modules above to match proj_names before proceeding, or training will no-op on LoRA.")

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=target_modules)
model = get_peft_model(model, lora)
model.enable_input_require_grads()
model.print_trainable_parameters()

raw = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"Examples: {len(raw)}")

def fmt(ex):
    txt = tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)
    return {"text": txt}
ds = raw.map(fmt)

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer, train_dataset=ds, dataset_text_field="text", max_seq_length=512,
    args=SFTConfig(output_dir=OUT_DIR, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="steps", save_steps=50, optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("DONE Muse Glimmer specialist C/D binary SFT")
