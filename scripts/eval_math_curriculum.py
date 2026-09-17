"""Math-curriculum competency eval for the engineer+mathematician+theorist
track. Held-out questions (not present in any training jsonl), 2 per group
across the 5 planned theories (risk, probability/bayes, chain, game_theory,
decision_theory). Repeated sampling (n_samples, do_sample=True, temp=0.7,
top_p=0.9) per this project's established convention (same as
eval_vuln_gate_v2_hermes3.py) -- a single greedy pass is one draw from a
distribution, not the distribution.

Usage: eval_math_curriculum.py <adapter_dir> <label> [n_samples]
"""
import sys, json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

sys.path.insert(0, '/home/shadeform')
from math_eval_questions import MATH_EVAL_QUESTIONS

BASE_MODEL = "NousResearch/Hermes-3-Llama-3.1-8B"
ADAPTER = sys.argv[1]
LABEL = sys.argv[2]
N_SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 30

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
im_end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
eos_ids = [tokenizer.eos_token_id]
if im_end_id is not None and im_end_id != tokenizer.unk_token_id:
    eos_ids.append(im_end_id)

model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()

results = {"label": LABEL, "adapter": ADAPTER, "n_samples": N_SAMPLES, "questions": []}
group_totals = {}

for q in MATH_EVAL_QUESTIONS:
    messages = [{"role": "user", "content": q["prompt"]}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    pass_count = 0
    samples = []
    for i in range(N_SAMPLES):
        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=300, do_sample=True, temperature=0.7, top_p=0.9,
                eos_token_id=eos_ids, pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(out[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        correct = bool(q["checker"](response))
        if correct:
            pass_count += 1
        samples.append({"i": i, "response": response, "correct": correct})
    group_totals.setdefault(q["group"], [0, 0])
    group_totals[q["group"]][0] += pass_count
    group_totals[q["group"]][1] += N_SAMPLES
    results["questions"].append({
        "id": q["id"], "group": q["group"], "prompt": q["prompt"],
        "pass_count": pass_count, "n_samples": N_SAMPLES,
        "pass_rate": pass_count / N_SAMPLES, "samples": samples,
    })
    print(f"[{LABEL}] {q['id']} ({q['group']}): {pass_count}/{N_SAMPLES}")

overall_pass = sum(v[0] for v in group_totals.values())
overall_total = sum(v[1] for v in group_totals.values())
results["group_summary"] = {g: {"pass": v[0], "total": v[1], "rate": v[0] / v[1]} for g, v in group_totals.items()}
results["overall"] = {"pass": overall_pass, "total": overall_total, "rate": overall_pass / overall_total}

for g, v in group_totals.items():
    print(f"[{LABEL}] GROUP {g}: {v[0]}/{v[1]} ({v[0]/v[1]*100:.1f}%)")
print(f"[{LABEL}] OVERALL: {overall_pass}/{overall_total} ({overall_pass/overall_total*100:.1f}%)")

with open(f"/home/shadeform/math_eval_result_{LABEL}.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved math_eval_result_{LABEL}.json")
