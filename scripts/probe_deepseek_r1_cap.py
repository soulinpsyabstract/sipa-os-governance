#!/usr/bin/env python3
"""Empirical probe: how many tokens does DeepSeek-R1-Distill-Qwen-1.5B need to
finish its <think> block and reach an actual answer, for the same k=20 prompt?
Not a scored benchmark — just measuring natural stopping points at a generous
token budget, to pick an honest cap for a real v3 run. fp16, no quantization
(model is 1.5B, T4-safe; T4 has no bf16 hardware support)."""
import torch, json, re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

QUESTION = "What was OpenAI's revenue in Q2 2026?"
BINARY_SYSTEM = "BINARY GATE PROTOCOL. IF proof.exists AND proof.verified THEN TRUE ELSE FALSE."
N_SAMPLES = 5
MAX_NEW_TOKENS = 800

ARMS = [
    (None, "DeepSeek-R1-base"),
    ("SoulInPsyAbstract/binary-r1-lora", "DeepSeek-R1-binary"),
]
BASE = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

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
        response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        n_tokens_generated = new_tokens.shape[0]
        hit_cap = n_tokens_generated >= MAX_NEW_TOKENS
        think_close_idx = response.find("</think>")
        arm_results.append({
            "k": k,
            "n_tokens_generated": int(n_tokens_generated),
            "hit_cap": bool(hit_cap),
            "think_close_char_offset": think_close_idx,
            "response": response[:1500],
        })
        print(f"  k={k}: tokens={n_tokens_generated} hit_cap={hit_cap} </think> at char {think_close_idx}")
        print(f"    tail: ...{response[-200:]}")
    results[name] = arm_results
    del model
    torch.cuda.empty_cache()

with open("deepseek_cap_probe.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved.")
