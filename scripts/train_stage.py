import json
import sys
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from trl import SFTTrainer, SFTConfig

BASE_MODEL = "NousResearch/Hermes-3-Llama-3.1-8B"

INPUT_ADAPTER = sys.argv[1]   # HF repo id or local path
DATASET_PATH = sys.argv[2]    # this stage's group jsonl
OUTPUT_DIR = sys.argv[3]      # where to save this stage's output

print(f"Loading tokenizer + base model...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

print(f"Loading adapter as trainable (no merge): {INPUT_ADAPTER}")
model = PeftModel.from_pretrained(model, INPUT_ADAPTER, is_trainable=True)
model.print_trainable_parameters()

print(f"Loading dataset: {DATASET_PATH}")
rows = []
with open(DATASET_PATH) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
print(f"{len(rows)} pairs loaded")

def to_text(row):
    messages = [
        {"role": "user", "content": row["instruction"]},
        {"role": "assistant", "content": row["response"]},
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}

dataset = Dataset.from_list(rows).map(to_text)

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
    dataset_text_field="text",
    max_length=1024,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print("Starting training...")
trainer.train()

print(f"Saving LoRA adapter to {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("DONE")
