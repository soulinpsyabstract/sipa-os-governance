#! /home/shadeform/venv/bin/python
"""Binary SFT: DeepSeek-R1-Distill-Qwen-1.5B — trl 0.17"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

MODEL_ID = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
OUT_DIR = "/home/shadeform/binary-r1-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)

raw = load_dataset("json", data_files="/home/shadeform/protocol0_binary_sft.jsonl", split="train")
print(f"Examples: {len(raw)}")

def fmt(ex):
    return tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)

trainer = SFTTrainer(
    model=model,
    args=SFTConfig(output_dir=OUT_DIR, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="steps", save_steps=200, optim="adamw_8bit", bf16=True, report_to=[], max_seq_length=512),
    train_dataset=raw,
    processing_class=tokenizer,
    formatting_func=fmt,
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("DONE DeepSeek-R1 binary SFT")