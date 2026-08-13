#!/usr/bin/env python3
"""
LoRA fine-tune Nemotron 3.5 Lightning on the same dataset used for the
existing SoulInPsyAbstract/specialist-cd-muse-glimmer-lora, to produce a
directly comparable specialist-cd-nemotron-lora sibling.

Dataset: SoulInPsyAbstract/specialist-cd-binary-honesty (already public, 19
downloads at last check) — reuse as-is, don't fork it, so both LoRAs are
trained on byte-identical data and any "before/after" or "model A vs model B"
comparison isn't confounded by a data difference.

Usage:
  python3 nemotron_lora_train.py --out ./nemotron-cd-lora
"""
import argparse

MODEL_ID = "unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B"  # NVFP4 checkpoint failed to load, see eval script note
DATASET_ID = "SoulInPsyAbstract/specialist-cd-binary-honesty"

LORA_CONFIG = dict(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
TRAIN_CONFIG = dict(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_strategy="epoch",
    bf16=True,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    print(f"Loading dataset {DATASET_ID} ...")
    ds = load_dataset(DATASET_ID, split="train")
    print(f"  {len(ds)} rows")

    print(f"Loading base model {MODEL_ID} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map={"": 0}, quantization_config=bnb_config)  # see eval script note
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(**LORA_CONFIG)
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # Verified live 2026-08-13: dataset has one column, `messages` — a chat-format
    # list of {role, content} dicts (system=BINARY GATE PROTOCOL, user=claim,
    # assistant=TRUE/FALSE), 194 rows. Not a `text` column.
    def tokenize(example):
        text = tok.apply_chat_template(example["messages"], tokenize=False)
        enc = tok(text, truncation=True, max_length=2048)
        enc["labels"] = enc["input_ids"].copy()
        return enc

    tokenized = ds.map(tokenize, remove_columns=ds.column_names)

    args_tr = TrainingArguments(output_dir=args.out, **TRAIN_CONFIG)
    trainer = Trainer(model=model, args=args_tr, train_dataset=tokenized)
    trainer.train()

    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print(f"Saved LoRA adapter -> {args.out}")


if __name__ == "__main__":
    main()
