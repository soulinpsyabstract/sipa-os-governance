"""Eval: does the model refuse to help construct a jailbreak/attack
targeting a THIRD-PARTY AI provider's model, under various social-
engineering framings? New pressure category, distinct from the G15
vuln-gate groups. No system prompt override -- tests default behavior
on a direct user request, same as a real user would approach it.

Usage: eval_third_party_jailbreak.py <adapter_dir> <label> [n_samples]
"""
import sys, json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

sys.path.insert(0, '/home/shadeform')
from third_party_jailbreak_scenarios import THIRD_PARTY_JAILBREAK_SCENARIOS, score_response

BASE_MODEL = "NousResearch/Hermes-3-Llama-3.1-8B"
ADAPTER = sys.argv[1]
LABEL = sys.argv[2]
N_SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 20

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

results = {"label": LABEL, "adapter": ADAPTER, "n_samples": N_SAMPLES, "scenarios": []}
overall_pass = 0
overall_total = 0

for sc in THIRD_PARTY_JAILBREAK_SCENARIOS:
    messages = [{"role": "user", "content": sc["prompt"]}]
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
        passed, reason = score_response(response)
        if passed:
            pass_count += 1
        overall_total += 1
        if passed:
            overall_pass += 1
        samples.append({"i": i, "response": response, "passed": passed, "reason": reason})
    results["scenarios"].append({
        "id": sc["id"], "prompt": sc["prompt"],
        "pass_count": pass_count, "n_samples": N_SAMPLES,
        "pass_rate": pass_count / N_SAMPLES, "samples": samples,
    })
    print(f"[{LABEL}] scenario {sc['id']}: {pass_count}/{N_SAMPLES}")

results["overall"] = {"pass": overall_pass, "total": overall_total, "rate": overall_pass / overall_total}
print(f"[{LABEL}] OVERALL: {overall_pass}/{overall_total} ({overall_pass/overall_total*100:.1f}%)")

with open(f"/home/shadeform/third_party_jailbreak_result_{LABEL}.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved third_party_jailbreak_result_{LABEL}.json")
