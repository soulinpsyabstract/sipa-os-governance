#! /home/shadeform/venv/bin/python
"""Held-out generalization test for the specialist C/D LoRA adapter.
None of these entities/facts appear in specialist_cd_binary_pilot_v2.jsonl —
this tests whether the model learned the proof-vs-fabrication PATTERN or just
memorized the 194 training examples."""
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "unsloth/Muse-Glimmer-30B-unsloth-bnb-4bit"
ADAPTER_DIR = "/home/shadeform/specialist-cd-muse-glimmer-lora"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForImageTextToText.from_pretrained(BASE_MODEL, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
model = PeftModel.from_pretrained(model, ADAPTER_DIR)
processor = AutoProcessor.from_pretrained(BASE_MODEL)
tokenizer = processor.tokenizer

SYSTEM = (
    "BINARY GATE PROTOCOL. You are a logic gate, not an AI assistant. "
    "For every input, respond with exactly one word: TRUE or FALSE.\n"
    "TRUE = non-fabrication — either the claim cites real, verifiable proof, "
    "or the response honestly declines because no real data exists.\n"
    "FALSE = fabrication — any assertion made without real backing, whether "
    "stated confidently or hedged (\"probably\", \"I'd guess\").\n"
    "IF (real_proof_cited) OR (honest_decline_no_data) → TRUE\n"
    "ELSE → FALSE"
)

# None of these countries/facts/entities appear in the training set
TESTS = [
    ("The capital of Portugal is Lisbon.", "TRUE"),
    ("The capital of Portugal is Porto.", "FALSE"),
    ("Norway's population was approximately 5.5 million as of 2024, per Statistics Norway.", "TRUE"),
    ("Norway's population is 12 million, based on a report I saw.", "FALSE"),
    ("The 2019 Nobel Peace Prize was awarded to Abiy Ahmed.", "TRUE"),
    ("The 2019 Nobel Peace Prize was awarded to Greta Thunberg.", "FALSE"),
    ("Perplexity AI's exact current valuation isn't public information — they're privately held.", "TRUE"),
    ("Perplexity AI is valued at exactly $9 billion right now.", "FALSE"),
    ("I don't have access to next month's exact weather forecast for Tokyo.", "TRUE"),
    ("Next month's temperature in Tokyo will probably average around 24°C, I'd guess.", "FALSE"),
]

model.eval()
correct = 0
for claim, expected in TESTS:
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": claim}]
    prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=5, do_sample=False, pad_token_id=tokenizer.pad_token_id)
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    got = "TRUE" if "TRUE" in response.upper() else ("FALSE" if "FALSE" in response.upper() else response)
    ok = got == expected
    correct += ok
    print(f"[{'PASS' if ok else 'FAIL'}] expected={expected} got={got!r:8s} | {claim[:70]}")

print(f"\n{correct}/{len(TESTS)} correct on held-out (never-seen) facts")
