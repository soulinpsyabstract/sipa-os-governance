#! /home/shadeform/venv/bin/python
"""EXP-037: Qwen2.5-7B-Instruct -- misbehavior/correct-behavior discriminator.
Same convention as train_vuln_specialist_qwen25.py (r=16/alpha=32/dropout=0.05,
same target_modules, same SFTConfig hyperparameters) -- single binary
discriminator, not a per-group specialist, because this dataset (70 records
across ~20 categories) has nowhere near per-group volume. Trained on
misbehavior_discriminator_sft_train_v1.jsonl (56 examples), held out
misbehavior_discriminator_sft_eval_v1.jsonl (14 examples) is NEVER touched
by this script -- eval_misbehavior_discriminator.py runs separately, after.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
DATA_PATH = "/home/shadeform/misbehavior_discriminator_sft_train_v1.jsonl"
OUT_DIR = "/home/shadeform/misbehavior-discriminator-qwen25-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)
model.enable_input_require_grads()
model.print_trainable_parameters()

raw = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"Examples: {len(raw)}")
def fmt(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}
ds = raw.map(fmt)

trainer = SFTTrainer(
    model=model, processing_class=tokenizer, train_dataset=ds,
    args=SFTConfig(output_dir=OUT_DIR, dataset_text_field="text", max_seq_length=768, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="steps", save_steps=100, optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("DONE misbehavior-discriminator Qwen2.5 binary SFT")
