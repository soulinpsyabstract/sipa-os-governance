#! /home/shadeform/venv/bin/python
"""Binary SFT: vulnerability gate specialist (G15), ONE group, for
vectionlabs/Salience-27B-R5 (Qwen3.5-based VLM, AutoModelForImageTextToText).

Third architecture in the specialist-per-group-then-merge series (after
Qwen2.5-7B in EXP-031, Hermes-4.3-36B in EXP-033/EXP-029). Salience-27B-R5
ships with explicit "no content filter, no system-level guardrail" in its
own model card -- the base model starts from zero refusal tendency, which
makes it the cleanest test yet of whether this project's LoRA-per-group
method can instill the hard-stop gate from scratch, not lean on baked-in
RLHF refusal the other two base models already had some of.

Text-only fine-tune: no images in this dataset, so AutoProcessor is used
for its .tokenizer (chat template + text tokenization), same as a plain
tokenizer would be for the causal-LM scripts. enable_thinking=False on the
chat template to match the non-reasoning response format the other two
architectures were evaluated on -- this project's judge (judge_v3.py)
scores the visible response text, not a <think> block, and letting
reasoning run by default here would not be comparable to EXP-031/EXP-033.

Usage: train_vuln_specialist_salience.py <group_slug>
e.g.:  train_vuln_specialist_salience.py 01_secrets_credentials

Trains on groups 01-06 only. group07 (encoding/injection proxy) stays
held-out/eval-only by design -- training on it would turn the OOD
generalization test into a memorization test, defeating its purpose
(EXP-034, and the architect's explicit call on this before this run).
"""
import sys
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

TRAINABLE_GROUPS = {
    "01_secrets_credentials", "02_access_control", "03_injection",
    "04_infra_misconfig", "05_supply_chain", "06_stop_gate_pressure",
}

if len(sys.argv) != 2:
    raise SystemExit("usage: train_vuln_specialist_salience.py <group_slug, one of 01-06>")
GROUP = sys.argv[1]
if GROUP not in TRAINABLE_GROUPS:
    raise SystemExit(
        f"{GROUP!r} is not trainable -- only 01-06 are. "
        f"group07 is eval-only by design (OOD generalization test, see EXP-034)."
    )

MODEL_ID = "vectionlabs/Salience-27B-R5"
MODEL_TAG = "salience27b"
DATA_PATH = f"/home/shadeform/per_group/{GROUP}_train.jsonl"
OUT_DIR = f"/home/shadeform/specialist-vuln-{GROUP}-{MODEL_TAG}-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")
model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
proc = AutoProcessor.from_pretrained(MODEL_ID)
tokenizer = proc.tokenizer
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Verified live (smoke test, 2026-08-21): 16 full-attention layers get
# q/k/v/o_proj LoRA, all 64 layers get MLP LoRA -- suffix-match target_modules
# work the same way here as on the two causal-LM architectures; the
# linear-attention layers (48 of 64) don't expose these exact module names
# and are adapted only through MLP, same asymmetric coverage the hybrid
# attention design implies. Not a bug, matches the architecture.
lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)
model.enable_input_require_grads()
model.print_trainable_parameters()

raw = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"[{GROUP}/{MODEL_TAG}] Examples: {len(raw)}")


def fmt(ex):
    # ex["messages"] is plain-string content (role/content pairs) from the
    # existing per_group training data, built for the two causal-LM
    # architectures. Salience's chat template expects list-of-parts content
    # ({"type":"text","text":...}) per its own quickstart example -- convert
    # here rather than regenerate the dataset, keeps one canonical training
    # set across all three architectures.
    converted = [
        {"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
        for m in ex["messages"]
    ]
    text = tokenizer.apply_chat_template(
        converted, tokenize=False, add_generation_prompt=False, enable_thinking=False
    )
    return {"text": text}


ds = raw.map(fmt)

trainer = SFTTrainer(
    model=model, processing_class=tokenizer, train_dataset=ds,
    args=SFTConfig(output_dir=OUT_DIR, dataset_text_field="text", max_length=768, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="no", optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE vuln-gate specialist [{GROUP}/{MODEL_TAG}]")
