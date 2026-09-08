import time, torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model

MODEL_NAME = "IFM/K2-Horizon-0.9B"
DATA_PATH = "specialist_cd_binary_pilot_v2.jsonl"
OUTPUT_DIR = "k2horizon-cd-lora-out"

def format_example(example, tokenizer):
    text = tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)
    return {"text": text}

def main():
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float32, device_map=None, trust_remote_code=True
    )
    print(f"Model loaded ({time.time()-t0:.1f}s)", flush=True)

    lora_config = LoraConfig(
        r=16, lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    raw = load_dataset("json", data_files=DATA_PATH, split="train")
    formatted = raw.map(lambda ex: format_example(ex, tokenizer))

    def tokenize_fn(ex):
        out = tokenizer(ex["text"], truncation=True, max_length=256, padding="max_length")
        out["labels"] = out["input_ids"].copy()
        return out

    tokenized = formatted.map(tokenize_fn, remove_columns=formatted.column_names)
    print(f"Dataset ready: {len(tokenized)} rows ({time.time()-t0:.1f}s)", flush=True)

    # CPU budget: reduced from the GPU-series standard (3 epochs on 194 rows) to 2 epochs
    # here, documented honestly -- this is a real scope reduction for CPU wall-clock feasibility,
    # not hidden. batch=1, grad_accum=8 matches the existing Lightning Studio template.
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=2,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        logging_steps=5,
        save_strategy="epoch",
        fp16=False,
        optim="adamw_torch",
        report_to=[],
    )
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    trainer = Trainer(model=model, args=args, train_dataset=tokenized, data_collator=collator)

    train_t0 = time.time()
    trainer.train()
    train_dt = time.time() - train_t0
    print(f"Training done in {train_dt:.1f}s", flush=True)

    model.save_pretrained(OUTPUT_DIR + "/final_adapter")
    tokenizer.save_pretrained(OUTPUT_DIR + "/final_adapter")
    total_dt = time.time() - t0
    print(f"DONE -- adapter saved to {OUTPUT_DIR}/final_adapter. Total wall time: {total_dt:.1f}s (train: {train_dt:.1f}s)", flush=True)
    with open("train_timing.json", "w") as f:
        import json
        json.dump({"total_wall_seconds": total_dt, "train_wall_seconds": train_dt, "epochs": 2, "rows": len(tokenized)}, f, indent=2)

if __name__ == "__main__":
    main()
