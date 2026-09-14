import argparse, json, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, PeftModel
from torch.utils.data import Dataset

TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


class ChatDataset(Dataset):
    def __init__(self, path, tokenizer, max_len=512):
        self.rows = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self.rows.append(json.loads(line)["messages"])
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        msgs = self.rows[idx]
        try:
            text = self.tokenizer.apply_chat_template(msgs, tokenize=False, enable_thinking=False)
        except TypeError:
            text = self.tokenizer.apply_chat_template(msgs, tokenize=False)
        enc = self.tokenizer(text, truncation=True, max_length=self.max_len, padding="max_length", return_tensors="pt")
        input_ids = enc["input_ids"][0]
        attn = enc["attention_mask"][0]
        labels = input_ids.clone()
        labels[attn == 0] = -100
        return {"input_ids": input_ids, "attention_mask": attn, "labels": labels}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--start-adapter", default=None, help="existing LoRA adapter dir/repo to continue training from (chain step)")
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True
    )
    if args.start_adapter:
        print(f"Continuing training from existing adapter: {args.start_adapter}", flush=True)
        model = PeftModel.from_pretrained(model, args.start_adapter, is_trainable=True)
    else:
        lora_config = LoraConfig(
            r=args.rank, lora_alpha=args.rank * 2, target_modules=TARGET_MODULES,
            lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    ds = ChatDataset(args.dataset, tokenizer)
    print(f"Loaded {len(ds)} training examples", flush=True)

    training_args = TrainingArguments(
        output_dir=args.out_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=5,
        save_strategy="no",
        report_to=[],
        bf16=True,
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=ds)
    trainer.train()

    model.save_pretrained(args.out_dir)
    tokenizer.save_pretrained(args.out_dir)
    print(f"Saved LoRA adapter to {args.out_dir}", flush=True)


if __name__ == "__main__":
    main()
