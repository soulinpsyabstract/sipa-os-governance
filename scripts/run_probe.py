import sys, json
sys.path.insert(0, '/home/shadeform')
from probe_questions import PROBE_QUESTIONS
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = "NousResearch/Hermes-3-Llama-3.1-8B"
ADAPTER = sys.argv[1]
LABEL = sys.argv[2]

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()

results = {"label": LABEL, "adapter": ADAPTER, "answers": []}
for q in PROBE_QUESTIONS:
    messages = [{"role": "user", "content": q["prompt"]}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=300, do_sample=False, temperature=1.0, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(out[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    results["answers"].append({"id": q["id"], "prompt": q["prompt"], "response": response})
    print(f"[{LABEL}] {q['id']}: {response[:150]}")

with open(f"/home/shadeform/probe_result_{LABEL}.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved probe_result_{LABEL}.json")
