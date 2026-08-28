#! /home/shadeform/venv/bin/python
"""Binary SFT: Hermes-3-Llama-3.1-8B — specialist C/D (non-fabrication pattern), v2.

Same architecture and hyperparameters as train_specialist_cd_hermes3.py (the
script that trained the currently-live specialist-cd-hermes3-lora). Only the
data source changed: specialist_cd_binary_combined_v1.jsonl instead of
specialist_cd_binary_pilot_v2.jsonl -- the original 194 curated examples plus
3019 real production events pulled from binary-gate-dryrun-verdicts.jsonl
(joined against its message archive by prep_binary_gate_dryrun_dataset.py,
2026-08-28; see that script's docstring for provenance).

⚠️ Label imbalance, stated plainly rather than silently trained through:
combined set is FALSE=2957 / TRUE=256 (~92%/8%). Almost all of the new real
volume is FALSE (fabrication) -- the dry-run gate mostly sees claims that
fail. A model trained on this unweighted can hit a misleadingly high raw
accuracy by defaulting toward FALSE without learning the actual boundary.
Not corrected here (class weighting/upsampling is a modeling decision, left
for whoever runs this to make deliberately, not buried in a script default).
Check TRUE-class recall specifically in post-eval, not just overall accuracy.

Before/after eval: specialist_cd_binary_dryrun_v1_eval_holdout.jsonl (200
examples, held out of this training file, chronologically the most recent
of the resolved dry-run events) is the eval set for this run -- run it
through both the pre-existing specialist-cd-hermes3-lora (baseline) and this
v2 adapter (after), same as every other EXP in this series.

Run only when the GPU box is up. Does nothing until executed."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

MODEL_ID = "NousResearch/Hermes-3-Llama-3.1-8B"
DATA_PATH = "/home/shadeform/specialist_cd_binary_combined_v1.jsonl"
OUT_DIR = "/home/shadeform/specialist-cd-hermes3-lora-v2"

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
    args=SFTConfig(output_dir=OUT_DIR, dataset_text_field="text", max_length=512, num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=5, save_strategy="steps", save_steps=50, optim="adamw_8bit", bf16=True, report_to=[])
)
trainer.train()
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("DONE Hermes-3 specialist C/D binary SFT v2 (pilot + real dry-run data)")
