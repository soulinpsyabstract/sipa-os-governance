#! /home/shadeform/venv/bin/python
"""Base (untuned) vs specialist-C/D-tuned — for plain causal LMs (Hermes-3, Qwen2.5).
Same 10 held-out facts used across all three models for apples-to-apples comparison."""
import sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

MODEL_KEY = sys.argv[1]  # "hermes3" or "qwen25"
CONFIGS = {
    "hermes3": ("NousResearch/Hermes-3-Llama-3.1-8B", "/home/shadeform/specialist-cd-hermes3-lora"),
    "qwen25": ("Qwen/Qwen2.5-7B-Instruct", "/home/shadeform/specialist-cd-qwen25-lora"),
}
BASE_MODEL, ADAPTER_DIR = CONFIGS[MODEL_KEY]

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
]

def load(with_adapter: bool):
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    m = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16)
    if with_adapter:
        m = PeftModel.from_pretrained(m, ADAPTER_DIR)
    m.eval()
    return m

def run(model, tokenizer, label):
    print(f"\n=== {label} ({MODEL_KEY}) ===")
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
        print(f"[{'PASS' if ok else 'FAIL'}] expected={expected} got={got!r:8s} | {claim[:65]}")
    print(f"{label}: {correct}/{len(TESTS)} correct")
    return correct

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token

base_model = load(with_adapter=False)
base_score = run(base_model, tokenizer, "BASE (untuned)")
del base_model
torch.cuda.empty_cache()

tuned_model = load(with_adapter=True)
tuned_score = run(tuned_model, tokenizer, "TUNED (specialist C/D)")

print(f"\nSUMMARY {MODEL_KEY}: BASE {base_score}/10 → TUNED {tuned_score}/10")
