#!/usr/bin/env python3
"""
LoRA fine-tune NousResearch/Hermes-4.3-36B on the same dataset used for the
existing specialist-cd-muse-glimmer-lora / specialist-cd-safeguard-lora, to
produce a directly comparable specialist-cd-hermes43-lora sibling.

Dataset: SoulInPsyAbstract/specialist-cd-binary-honesty (chat-format,
`messages` column, 194 rows) — byte-identical across the series.

Standard dense architecture (base: ByteDance-Seed/Seed-OSS-36B-Base) —
confirmed live module names: q_proj/k_proj/v_proj/o_proj/gate_proj/up_proj/
down_proj, all standard nn.Linear, no MoE grouped_mm complication like
EXP-028's safeguard-20b. bnb-4bit quantization does support training
(unlike safeguard's native MXFP4) — no Mxfp4Config dequantize dance needed.

Usage:
  python3 hermes43_lora_train.py --out ./hermes43-cd-lora
"""
import argparse

MODEL_ID = "NousResearch/Hermes-4.3-36B"
DATASET_ID = "SoulInPsyAbstract/specialist-cd-binary-honesty"

LORA_CONFIG = dict(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
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
    # 2026-08-13 (EXP-028 lesson): don't pass device_map here — Trainer's own
    # __init__ calls model.to(device) unconditionally, and doing both doubles
    # peak VRAM and OOMs. Let Trainer place it once.
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, low_cpu_mem_usage=True, quantization_config=bnb_config,
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(**LORA_CONFIG)
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

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
