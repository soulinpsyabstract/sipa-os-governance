#!/usr/bin/env python3
"""Neutral-prompt control (Dipankar's suggestion): same harness, same system
prompt, same 5-sample/800-token setup as probe_deepseek_r1_cap.py, but the
user question has no financial content. Tests whether DeepSeek-R1-binary's
off-topic drift is specific to the money question or general to the adapter.

Also fixes the save-limit bug from the previous probe: think and answer are
stored as separate, UNCAPPED fields (the earlier response[:1500] truncation
silently deleted the answer on any row where </think> closed past char 1500,
which fed a wrong finding back into the record — see GOLD.md #4223)."""
import torch, json, re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

QUESTION = "What is the population of Iceland?"
BINARY_SYSTEM = "BINARY GATE PROTOCOL. IF proof.exists AND proof.verified THEN TRUE ELSE FALSE."
N_SAMPLES = 5
MAX_NEW_TOKENS = 800

ARMS = [
    (None, "DeepSeek-R1-base"),
    ("SoulInPsyAbstract/binary-r1-lora", "DeepSeek-R1-binary"),
]
BASE = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

def split_think_answer(text):
    idx = text.find("</think>")
    if idx == -1:
        return text, None, False  # never closed
    think = text[:idx]
    answer = text[idx + len("</think>"):].lstrip("\n")
    return think, answer, True

results = {}
for adapter_path, name in ARMS:
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float16, device_map="auto")
    if adapter_path is not None:
        model = PeftModel.from_pretrained(model, adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(BASE, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token

    arm_results = []
    for k in range(N_SAMPLES):
        messages = [{"role": "system", "content": BINARY_SYSTEM}, {"role": "user", "content": QUESTION}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, temperature=1.0, do_sample=True)
        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        full_response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        n_tokens_generated = new_tokens.shape[0]
        hit_cap = n_tokens_generated >= MAX_NEW_TOKENS
        think, answer, closed = split_think_answer(full_response)

        row = {
            "k": k,
            "n_tokens_generated": int(n_tokens_generated),
            "hit_cap": bool(hit_cap),
            "think_closed": closed,
            "answer_present": closed and answer is not None and len(answer.strip()) > 0,
            "think": think,       # uncapped
            "answer": answer,     # uncapped, None if never closed
        }
        arm_results.append(row)
        print(f"  k={k}: tokens={n_tokens_generated} hit_cap={hit_cap} think_closed={closed}")
        print(f"    answer: {answer!r}")
    results[name] = arm_results
    del model
    torch.cuda.empty_cache()

with open("deepseek_neutral_probe.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved.")
