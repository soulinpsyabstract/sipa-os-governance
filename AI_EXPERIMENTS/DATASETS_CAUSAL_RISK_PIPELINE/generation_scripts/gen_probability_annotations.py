#!/usr/bin/env python3
"""Generate probability dataset (dataset 2 of 3) via OpenRouter Hermes-4-405B.

Takes the ALREADY-IDENTIFIED chains from dataset 1 (causal_chain_*.jsonl) and
annotates each with a probability estimate P(the chain X->Y->Z actually
completes to the harmful Z) + reasoning. This does NOT invent new scenarios --
it estimates likelihood on top of structure dataset 1 already fixed, matching
the architect's explicit ordering: chain first, probability second.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_SIZE = 8
GROUPS = ["vulnerability", "deletion", "sensitive_publication"]


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
        "temperature": 0.7,
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


def build_prompt(chunk):
    chains_json = json.dumps(
        [{"id": c["id"], "action_x": c["action_x"], "chain": c["chain"], "terminal_outcome": c["terminal_outcome"]} for c in chunk],
        ensure_ascii=False, indent=2,
    )
    return f"""You are annotating a set of ALREADY-FIXED causal chains (X -> Y -> Z) with a probability estimate.
Do NOT invent new chains or change the chains below -- only estimate, for EACH one, the probability that
this specific chain, once X happens, actually completes all the way to the harmful terminal outcome Z.

Chains to annotate:
{chains_json}

For each chain, think about:
- Does X reliably cause Y, or does Y only happen under some additional precondition (no monitoring, wrong config already present, bad luck timing)?
- Is Z the near-certain consequence of Y, or could Y be caught/mitigated before reaching Z?
- Vary your estimates realistically -- not every chain should get a high probability. Some chains require several unlikely things to align (low P, e.g. 0.05-0.25); some are close to deterministic once X happens (high P, e.g. 0.7-0.95); most are in between.

Output ONLY a raw JSON array (no markdown fences, no prose) with exactly one object per input chain, in the same order, each with this schema:
{{
  "id": "<the same id from the input>",
  "probability_estimate": <float between 0.0 and 1.0>,
  "probability_reasoning": "<one or two sentences: what preconditions are needed for this chain to complete, and why that gives this probability>"
}}"""


def main():
    for group in GROUPS:
        chain_path = os.path.join(BASE_DIR, f"causal_chain_{group}.jsonl")
        out_path = os.path.join(BASE_DIR, f"probability_{group}.jsonl")
        chains = [json.loads(l) for l in open(chain_path) if l.strip()]

        done_chain_refs = set()
        if os.path.exists(out_path):
            for l in open(out_path):
                if l.strip():
                    done_chain_refs.add(json.loads(l)["chain_ref"])

        todo = [c for c in chains if c["id"] not in done_chain_refs]
        print(f"[{group}] {len(done_chain_refs)} done, {len(todo)} to annotate", flush=True)

        with open(out_path, "a") as out_f:
            for i in range(0, len(todo), BATCH_SIZE):
                chunk = todo[i:i + BATCH_SIZE]
                prompt = build_prompt(chunk)
                try:
                    raw = call_hermes(prompt)
                    items = extract_json_array(raw)
                except Exception as e:
                    print(f"  [{group}] batch at i={i} FAILED: {e}", flush=True)
                    time.sleep(3)
                    continue
                by_id = {c["id"]: c for c in chunk}
                written = 0
                for item in items:
                    cid = item.get("id")
                    src = by_id.get(cid)
                    if not src or "probability_estimate" not in item:
                        continue
                    record = {
                        "id": f"PROB-{cid.replace('CHAIN-', '')}",
                        "risk_group": group,
                        "chain_ref": cid,
                        "action_x": src["action_x"],
                        "terminal_outcome": src["terminal_outcome"],
                        "probability_estimate": item["probability_estimate"],
                        "probability_reasoning": item.get("probability_reasoning", ""),
                    }
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1
                out_f.flush()
                print(f"  [{group}] +{written} (batch {i}-{i+len(chunk)})", flush=True)
        print(f"[{group}] DONE", flush=True)
    print("ALL DONE")


if __name__ == "__main__":
    main()
