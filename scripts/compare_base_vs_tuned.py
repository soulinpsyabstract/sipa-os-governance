#! /home/shadeform/venv/bin/python
"""Base (untuned) vs specialist-C/D-tuned Muse Glimmer — 20 held-out facts,
none present in specialist_cd_binary_pilot_v2.jsonl's 194 training examples."""
import torch, json
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "unsloth/Muse-Glimmer-30B-unsloth-bnb-4bit"
ADAPTER_DIR = "/home/shadeform/specialist-cd-muse-glimmer-lora"

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
    ("The capital of Sweden is Stockholm.", "TRUE"),
    ("The capital of Sweden is Gothenburg.", "FALSE"),
    ("Denmark's population was approximately 5.95 million as of 2024, per Statistics Denmark.", "TRUE"),
    ("Denmark's population is 15 million, I believe.", "FALSE"),
    ("The 2020 Nobel Peace Prize was awarded to the World Food Programme.", "TRUE"),
    ("The 2020 Nobel Peace Prize was awarded to Jacinda Ardern.", "FALSE"),
    ("Character.AI's exact current valuation isn't public — it's a privately held company.", "TRUE"),
    ("Character.AI is valued at exactly $2.7 billion right now.", "FALSE"),
    ("I can't state the exact number of employees at a private company without a published source.", "TRUE"),
    ("That private company probably has around 340 employees, I'd estimate.", "FALSE"),
]

def load(with_adapter: bool):
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    m = AutoModelForImageTextToText.from_pretrained(BASE_MODEL, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
    if with_adapter:
        m = PeftModel.from_pretrained(m, ADAPTER_DIR)
    m.eval()
    return m

def run(model, tokenizer):
    results = []
    for claim, expected in TESTS:
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": claim}]
        prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=5, do_sample=False, pad_token_id=tokenizer.pad_token_id)
        response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        got = "TRUE" if "TRUE" in response.upper() else ("FALSE" if "FALSE" in response.upper() else response)
        results.append({"claim": claim, "expected": expected, "got": got, "correct": got == expected})
    return results

import sys
mode = sys.argv[1] if len(sys.argv) > 1 else "both"

processor = AutoProcessor.from_pretrained(BASE_MODEL)
tokenizer = processor.tokenizer

if mode in ("base", "both"):
    print("=== BASE (untuned) ===")
    base_model = load(with_adapter=False)
    base_results = run(base_model, tokenizer)
    for r in base_results:
        print(f"[{'PASS' if r['correct'] else 'FAIL'}] expected={r['expected']} got={r['got']!r:8s} | {r['claim'][:65]}")
    base_correct = sum(r["correct"] for r in base_results)
    print(f"BASE: {base_correct}/{len(TESTS)} correct")
    with open("/home/shadeform/base_results.json", "w") as f:
        json.dump(base_results, f, indent=2)
    del base_model
    torch.cuda.empty_cache()

if mode in ("tuned", "both"):
    print("\n=== TUNED (specialist C/D LoRA) ===")
    tuned_model = load(with_adapter=True)
    tuned_results = run(tuned_model, tokenizer)
    for r in tuned_results:
        print(f"[{'PASS' if r['correct'] else 'FAIL'}] expected={r['expected']} got={r['got']!r:8s} | {r['claim'][:65]}")
    tuned_correct = sum(r["correct"] for r in tuned_results)
    print(f"TUNED: {tuned_correct}/{len(TESTS)} correct")
    with open("/home/shadeform/tuned_results.json", "w") as f:
        json.dump(tuned_results, f, indent=2)
