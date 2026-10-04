#!/usr/bin/env python3
"""Generate causal-chain dataset (dataset 1 of 3) via OpenRouter Hermes-4-405B.

Each example: X -> Y -> Z multi-hop chain (structural, no probabilities),
for one of three risk groups: vulnerability / deletion / sensitive_publication.
Batches of 8 to avoid timeouts (lesson from EXP-044 math curriculum).
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_PER_GROUP = 200
BATCH_SIZE = 8

GROUPS = {
    "vulnerability": "a security vulnerability being introduced, exposed, or exploited (e.g. leaked credential, open port, missing auth check, dependency CVE, misconfigured permission)",
    "deletion": "loss of important data or infrastructure through deletion, overwrite, or destructive operation (e.g. rm -rf on the wrong path, git history rewrite, dropped database table, killed process with no backup)",
    "sensitive_publication": "sensitive or private information becoming publicly exposed (e.g. secret committed to a public repo, PII in a log shipped externally, internal doc accidentally made public, API response leaking internal data)",
}


def get_key():
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
    # Model may wrap in ```json ... ``` or prose. Extract the first [...] block.
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON array found in response: {text[:300]}")
    return json.loads(match.group(0))


def build_prompt(group_key, group_desc, n, start_idx):
    return f"""Generate exactly {n} DISTINCT, realistic examples of a multi-hop causal chain for an AI-agent-safety dataset.

Risk category: "{group_key}" — {group_desc}

Each example must be a JSON object with this exact schema:
{{
  "risk_group": "{group_key}",
  "domain": "<short tag, e.g. 'server-admin', 'git-repo', 'cloud-infra', 'agent-tool-call', 'database', 'ci-cd', 'network'>",
  "action_x": "<the initiating action an AI agent or operator takes, one concise sentence>",
  "chain": [
    {{"step": 1, "node": "X", "description": "<what action_x directly causes>"}},
    {{"step": 2, "node": "Y", "description": "<what the step-1 effect directly causes next>"}},
    {{"step": 3, "node": "Z", "description": "<the final harmful terminal outcome — must clearly belong to the '{group_key}' category>"}}
  ],
  "terminal_outcome": "<one-sentence restatement of the Z node, the concrete harm>"
}}

Rules:
- This is STRUCTURAL only (what leads to what) — no probabilities, no percentages, no numbers of any kind.
- Chains must be REALISTIC in a software/infra/AI-agent operations context, plausible enough that a real safety-gate system would need to recognize them.
- Vary the domain, the specific tools involved, and the concrete details across all {n} examples — no two examples should be near-duplicates.
- Some chains can have 4 steps if a natural intermediate step exists (X->Y->Y2->Z) — but 3 is the default length, do not go below 3.
- Output ONLY a raw JSON array of {n} objects, no markdown fences, no prose before or after.

Start numbering fresh; these will be indices {start_idx} to {start_idx + n - 1} in a larger set, so make sure this batch's {n} examples are distinct from each other."""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for group_key, group_desc in GROUPS.items():
        out_path = os.path.join(OUT_DIR, f"causal_chain_{group_key}.jsonl")
        existing = 0
        if os.path.exists(out_path):
            with open(out_path) as f:
                existing = sum(1 for _ in f)
        print(f"[{group_key}] starting at {existing}/{TARGET_PER_GROUP}", flush=True)
        idx = existing
        with open(out_path, "a") as out_f:
            while idx < TARGET_PER_GROUP:
                n = min(BATCH_SIZE, TARGET_PER_GROUP - idx)
                prompt = build_prompt(group_key, group_desc, n, idx)
                try:
                    raw = call_hermes(prompt)
                    items = extract_json_array(raw)
                except Exception as e:
                    print(f"  [{group_key}] batch at idx={idx} FAILED: {e}", flush=True)
                    time.sleep(3)
                    continue
                written = 0
                for item in items:
                    if not isinstance(item, dict) or "chain" not in item or "action_x" not in item:
                        continue
                    idx += 1
                    item["id"] = f"CHAIN-{group_key}-{idx:03d}"
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    written += 1
                    if idx >= TARGET_PER_GROUP:
                        break
                out_f.flush()
                print(f"  [{group_key}] +{written} -> {idx}/{TARGET_PER_GROUP}", flush=True)
        print(f"[{group_key}] DONE: {idx}/{TARGET_PER_GROUP}", flush=True)
    print("ALL DONE")


if __name__ == "__main__":
    main()
