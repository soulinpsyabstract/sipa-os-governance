#!/usr/bin/env python3
"""
LoRA fine-tune gpt-oss-safeguard-20b on the same dataset used for the
existing SoulInPsyAbstract/specialist-cd-muse-glimmer-lora, to produce a
directly comparable specialist-cd-safeguard-lora sibling.

Dataset: SoulInPsyAbstract/specialist-cd-binary-honesty (chat-format,
`messages` column, 194 rows) — reused as-is, byte-identical to the other
specialist-cd LoRAs so comparisons aren't confounded by a data difference.

Load path matches what actually worked for the before-eval (see
safeguard_eval_before_after.py notes): no BitsAndBytesConfig — this
checkpoint ships natively MXFP4-quantized, requires the `kernels` package
(pinned to 0.13.0 — 0.16.0 broke on this transformers version) to stay
quantized instead of silently dequantizing to bf16 and blowing VRAM.

Usage:
  python3 safeguard_lora_train.py --out ./safeguard-cd-lora
"""
import argparse

MODEL_ID = "openai/gpt-oss-safeguard-20b"
DATASET_ID = "SoulInPsyAbstract/specialist-cd-binary-honesty"

LORA_CONFIG = dict(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    # 2026-08-13: peft couldn't auto-detect target_modules for this new
    # architecture. Confirmed live which projection names actually exist
    # (`experts` MoE layer skipped — uses a non-standard grouped_mm forward,
    # not a plain nn.Linear peft can wrap cleanly).
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
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

    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model

    print(f"Loading dataset {DATASET_ID} ...")
    ds = load_dataset(DATASET_ID, split="train")
    print(f"  {len(ds)} rows")

    print(f"Loading base model {MODEL_ID} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    # 2026-08-13: transformers explicitly rejects training against native
    # MXFP4 weights ("please consider dequantizing the model first by passing
    # quantization_config=Mxfp4Config(dequantize=True)") — exact fix per its
    # own error message. ~40GB in bf16, tight on 46GB but should fit given
    # only the small LoRA adapter needs gradients/optimizer state.
    # 2026-08-13: Trainer.__init__ calls model.to(device) itself regardless —
    # combined with device_map={"":0} at load time, the model got placed
    # twice, doubling peak memory into OOM. Don't pre-place; let Trainer do
    # the single placement.
    from transformers import Mxfp4Config
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, low_cpu_mem_usage=True,
        quantization_config=Mxfp4Config(dequantize=True),
    )

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
