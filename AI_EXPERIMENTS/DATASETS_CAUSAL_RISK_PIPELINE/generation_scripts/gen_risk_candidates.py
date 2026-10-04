#!/usr/bin/env python3
"""Generate risk/sensitive-info CANDIDATE dataset (dataset 3 of 3) via OpenRouter
Hermes-4-405B. These are CANDIDATES pending architect review, not final ground
truth -- unlike risk_harvested_from_governance_canon.jsonl (already decided).

Each candidate: an item (file type / action / data type) with a proposed
is_risky true/false label + reasoning, for one of three risk groups. Explicitly
asks for a balanced mix (not everything true) so the resulting classifier
dataset has real negative examples, not just an "everything is risky" list.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARVEST_PATH = os.path.join(BASE_DIR, "risk_harvested_from_governance_canon.jsonl")
TARGET_PER_GROUP = 200
BATCH_SIZE = 8

GROUPS = {
    "vulnerability": "what counts as a security vulnerability -- specific file types, configs, code patterns, or operational habits that introduce or expose a security weakness",
    "deletion": "which specific files, data types, or operational states are risky to delete/overwrite/destroy (vs safe to delete)",
    "sensitive_publication": "what specific kinds of data or files count as sensitive such that their public exposure/publication would be harmful (vs data that's fine to be public)",
}


def get_key():
    key = None
    for path in (os.environ.get("KEYS_FILE", ".env"),):
        try:
            with open(path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"')
        except FileNotFoundError:
            continue
    return key


KEY = get_key()
if not KEY:
    print("NO OPENROUTER_API_KEY FOUND", file=sys.stderr)
    sys.exit(2)


def call_hermes(prompt, max_tokens=3000, retries=3):
    payload = json.dumps({
        "model": "nousresearch/hermes-4-405b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.9,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"call_hermes failed after {retries} attempts: {last_err}")


def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON array found: {text[:300]}")
    return json.loads(match.group(0))


def load_harvest_examples(group):
    examples = []
    if os.path.exists(HARVEST_PATH):
        for l in open(HARVEST_PATH):
            if not l.strip():
                continue
            r = json.loads(l)
            if r["risk_group"] == group:
                examples.append({"item": r["item"], "is_risky": r["is_risky"], "reasoning": r["reasoning"]})
    return examples


def build_prompt(group_key, group_desc, examples, n, start_idx):
    ex_json = json.dumps(examples, ensure_ascii=False, indent=2)
    return f"""Generate exactly {n} DISTINCT candidate examples for a risk-classification training dataset.

Risk category: "{group_key}" -- {group_desc}

Here are {len(examples)} ALREADY-DECIDED real examples from this project's own incident history, for calibration
(these are ground truth, not to be repeated -- generate NEW distinct items in the same spirit):
{ex_json}

Each example must be a JSON object with this schema:
{{
  "item": "<a concrete file type, action, config, or data type -- specific enough to classify, one sentence>",
  "is_risky": true or false,
  "reasoning": "<one sentence: why this is (or is NOT) risky in the '{group_key}' sense>"
}}

Rules:
- IMPORTANT: produce a BALANCED mix -- roughly half should be is_risky=true, half should be is_risky=false.
  The false examples should be genuinely plausible-sounding but actually safe (e.g. a rotated/expired credential,
  a public README file, a temp cache file safe to delete, a log file with all PII already redacted) -- not
  strawmen. This is what makes the dataset useful for training a real classifier, not just a list of bad things.
- Vary domain and specificity across all {n} examples -- no near-duplicates.
- Ground each example in realistic software/infra/AI-agent-operations contexts.
- Output ONLY a raw JSON array of {n} objects, no markdown fences, no prose before or after.

These will be indices {start_idx} to {start_idx + n - 1} in a larger set -- keep them distinct from each other."""


def main():
    for group_key, group_desc in GROUPS.items():
        out_path = os.path.join(BASE_DIR, f"risk_candidates_{group_key}.jsonl")
        examples = load_harvest_examples(group_key)
        existing = 0
        if os.path.exists(out_path):
            with open(out_path) as f:
                existing = sum(1 for _ in f)
        print(f"[{group_key}] starting at {existing}/{TARGET_PER_GROUP} (few-shot from {len(examples)} harvested)", flush=True)
        idx = existing
        with open(out_path, "a") as out_f:
            while idx < TARGET_PER_GROUP:
                n = min(BATCH_SIZE, TARGET_PER_GROUP - idx)
                prompt = build_prompt(group_key, group_desc, examples, n, idx)
                try:
                    raw = call_hermes(prompt)
                    items = extract_json_array(raw)
                except Exception as e:
                    print(f"  [{group_key}] batch at idx={idx} FAILED: {e}", flush=True)
                    time.sleep(3)
                    continue
                written = 0
                for item in items:
                    if not isinstance(item, dict) or "item" not in item or "is_risky" not in item:
                        continue
                    idx += 1
                    record = {
                        "id": f"RISK-CAND-{group_key}-{idx:03d}",
                        "risk_group": group_key,
                        "item": item["item"],
                        "is_risky": item["is_risky"],
                        "reasoning": item.get("reasoning", ""),
                        "source": "generated_candidate_pending_review",
                        "decided_by": None,
                    }
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1
                    if idx >= TARGET_PER_GROUP:
                        break
                out_f.flush()
                print(f"  [{group_key}] +{written} -> {idx}/{TARGET_PER_GROUP}", flush=True)
        print(f"[{group_key}] DONE: {idx}/{TARGET_PER_GROUP}", flush=True)
    print("ALL DONE")


if __name__ == "__main__":
    main()
