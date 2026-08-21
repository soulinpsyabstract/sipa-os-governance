#! /home/shadeform/venv/bin/python
"""Binary SFT: vulnerability gate specialist (G15), ONE group, parameterized
by base model. Second-architecture repeat of EXP-031 (Qwen2.5-7B) -- proving
specialist-per-group-then-merge generalizes across base models, not just one.

Usage: train_vuln_specialist_pergroup_v2.py <group_slug> <model_tag>
e.g.:  train_vuln_specialist_pergroup_v2.py 01_secrets_credentials hermes43

model_tag "hermes43" -> NousResearch/Hermes-4.3-36B, config matches EXP-029's
proven zero-blocker settings on this exact hardware (L40S): plain
BitsAndBytesConfig(nf4), no device_map pre-placement before Trainer (EXP-028's
double-placement OOM lesson), full attention+MLP target_modules (dense
architecture, confirmed via named_modules() in EXP-029, no MoE complication).
model_tag "qwen25" -> Qwen/Qwen2.5-7B-Instruct, same as EXP-031's original run,
kept here for a same-script control re-run if ever needed.
"""
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

if len(sys.argv) != 3:
    raise SystemExit("usage: train_vuln_specialist_pergroup_v2.py <group_slug> <model_tag: qwen25|hermes43>")
GROUP, MODEL_TAG = sys.argv[1], sys.argv[2]

MODEL_IDS = {
    "qwen25": "Qwen/Qwen2.5-7B-Instruct",
    "hermes43": "NousResearch/Hermes-4.3-36B",
}
if MODEL_TAG not in MODEL_IDS:
    raise SystemExit(f"unknown model_tag {MODEL_TAG!r}, choices: {list(MODEL_IDS)}")
MODEL_ID = MODEL_IDS[MODEL_TAG]

DATA_PATH = f"/home/shadeform/per_group/{GROUP}_train.jsonl"
OUT_DIR = f"/home/shadeform/specialist-vuln-{GROUP}-{MODEL_TAG}-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")
# No device_map pre-placement here on purpose -- EXP-028 found placing the model
# both at load time (device_map=...) and again inside Trainer.__init__ roughly
# doubles peak VRAM and OOMs. Let device_map="auto" do the one real placement.
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)
model.enable_input_require_grads()
model.print_trainable_parameters()

raw = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"[{GROUP}/{MODEL_TAG}] Examples: {len(raw)}")
def fmt(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}
ds = raw.map(fmt)

trainer = SFTTrainer(
    model=model, processing_class=tokenizer, train_dataset=ds,
    args=SFTConfig(output_dir=OUT_DIR, dataset_text_field="text", max_length=768, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="no", optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print(f"DONE vuln-gate specialist [{GROUP}/{MODEL_TAG}]")
