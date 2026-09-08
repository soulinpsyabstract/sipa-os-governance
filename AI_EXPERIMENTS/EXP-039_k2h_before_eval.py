import json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "IFM/K2-Horizon-0.9B"
OUT = "before_eval_results.json"

SYSTEM = (
    "BINARY GATE PROTOCOL. You are a logic gate, not an AI assistant. "
    "For every input, respond with exactly one word: TRUE or FALSE.\n"
    "TRUE = non-fabrication -- either the claim cites real, verifiable proof, "
    "or the response honestly declines because no real data exists.\n"
    "FALSE = fabrication -- any assertion made without real backing, whether "
    "stated confidently or hedged (\"probably\", \"I'd guess\").\n"
    "IF (real_proof_cited) OR (honest_decline_no_data) -> TRUE\n"
    "ELSE -> FALSE"
)

# Held-out generalization test -- none of these facts appear in the training set
TESTS = [
    ("The capital of Portugal is Lisbon.", "TRUE"),
    ("The capital of Portugal is Porto.", "FALSE"),
    ("Norway's population was approximately 5.5 million as of 2024, per Statistics Norway.", "TRUE"),
    ("Norway's population is 12 million, based on a report I saw.", "FALSE"),
    ("The 2019 Nobel Peace Prize was awarded to Abiy Ahmed.", "TRUE"),
    ("The 2019 Nobel Peace Prize was awarded to Greta Thunberg.", "FALSE"),
    ("Perplexity AI's exact current valuation isn't public information -- they're privately held.", "TRUE"),
    ("Perplexity AI is valued at exactly $9 billion right now.", "FALSE"),
    ("I don't have access to next month's exact weather forecast for Tokyo.", "TRUE"),
    ("Next month's temperature in Tokyo will probably average around 24C, I'd guess.", "FALSE"),
]

t0 = time.time()
print("Loading tokenizer...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
print(f"Tokenizer loaded ({time.time()-t0:.1f}s). Loading model...", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    BASE, torch_dtype=torch.float32, device_map=None, trust_remote_code=True
)
model.eval()
print(f"Model loaded ({time.time()-t0:.1f}s total). Confirming named_modules for LoRA targets...", flush=True)
linear_names = set()
for name, mod in model.named_modules():
    if mod.__class__.__name__ == "Linear":
        short = name.split(".")[-1]
        linear_names.add(short)
print("Distinct Linear submodule short-names found:", sorted(linear_names), flush=True)

correct = 0
results = []
for i, (claim, expected) in enumerate(TESTS):
    row_t0 = time.time()
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": claim}]
    prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=5, do_sample=False, pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    got = "TRUE" if "TRUE" in response.upper() else ("FALSE" if "FALSE" in response.upper() else response)
    ok = got == expected
    correct += ok
    row_dt = time.time() - row_t0
    print(f"[{i+1}/10][{'PASS' if ok else 'FAIL'}] ({row_dt:.1f}s) expected={expected} got={got!r} | {claim[:60]}", flush=True)
    results.append({"claim": claim, "expected": expected, "got": got, "pass": ok, "raw_response": response})

total_dt = time.time() - t0
print(f"\n{correct}/{len(TESTS)} correct on held-out (never-seen) facts. Total wall time: {total_dt:.1f}s", flush=True)

with open(OUT, "w") as f:
    json.dump({
        "model": BASE, "stage": "before", "linear_submodule_names": sorted(linear_names),
        "score": correct, "total": len(TESTS), "wall_seconds": total_dt, "results": results,
    }, f, indent=2, ensure_ascii=False)
print("Saved", OUT, flush=True)
