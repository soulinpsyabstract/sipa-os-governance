#!/usr/bin/env python3
"""generate_synthetic_contrast.py -- the architect's answer to "why not just
generate a false example instead of hunting for a real one," 2026-09-02.

The real answer: you can, but not into misbehavior_incidents_seed_v1.jsonl.
That file's entire schema (verifiability, source_locator, locator_precision,
locator_exhaustive) exists to guarantee every record is a real, citable event
-- the same discipline that caught Anthropic's own "160+ incidents" overclaim
and a dozen other things this session. A model-generated scenario isn't
"unverifiable" in that file's narrow sense (single self-report, no
corroboration) -- it isn't a claim about reality at all, so mixing it in
without a hard, structural marker would be exactly the kind of overclaim this
whole project exists to catch, just self-inflicted.

So: a SEPARATE file, same pattern as EXP-031's synthetic adversarial eval
dataset (120 scenarios, 6 groups) already sitting elsewhere in this repo --
training material kept structurally apart from citation-audited incident
data, never merged, every record carrying synthetic=true so it can never be
mistaken for the real thing even if someone greps the two files together.

What it does: for a list of target true-category records in
misbehavior_incidents_seed_v1.jsonl (chosen because a real false-pair search
came back empty or is structurally unlikely -- single-record categories,
"correctly prevented" incidents that don't make news), calls DeepSeek
directly (not ask.sh -- ask.sh's bash string interpolation breaks on
multi-line JSON content with quotes, same fragility noted in the
classify.py precedent from this same session) to construct a realistic,
specific contrasting scenario: same category, same kind of decision point,
opposite (correct) outcome, with the model's reasoning made explicit.

Every output record carries:
  - synthetic: true (always, no exceptions)
  - based_on: the real record id it mirrors
  - generated_by / generated_date: full provenance of the generation itself

This script makes no factual claim about the world. It is not covered by
check_dataset_citations.py or check_locator_precision.py, and must never be
merged into the real dataset file or have its records reformatted to drop
the synthetic flag.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"
OUT_PATH = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_synthetic_contrast_v1.jsonl"

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """You write realistic, specific contrast scenarios for an AI safety dataset.
You will be given a real, documented incident where an AI model misbehaved in a specific way.
Your job: construct a plausible, technically grounded scenario in the SAME category, facing the
SAME kind of decision point, where an AI system instead makes the CORRECT choice -- and make its
reasoning at the decision point explicit and concrete, not a vague "it behaved well."

Rules:
- Do not claim this happened. Do not name a real company, real product, or real date as if this
  were a real event -- use a plausible but clearly generic/hypothetical framing (e.g. "an
  autonomous coding agent" not "Claude Code version X").
- Be specific: name the concrete signal the system noticed, the concrete alternative action it
  took (declining, asking for confirmation, escalating to a human, stopping), and why that
  specific signal was the one that mattered.
- Match the technical texture of the real incident (same domain, same class of tool/environment)
  so the contrast is genuinely a mirror image, not a generic "AI behaves well" story.
- Output ONLY valid JSON, no markdown fences, with exactly these keys:
  "scenario_setup" (2-4 sentences: the situation, what the system was asked/tasked to do),
  "correct_behavior" (2-4 sentences: what it did instead of the bad outcome, and the specific
  signal/reasoning that led there)."""


def build_user_prompt(record: dict) -> str:
    return (
        f"Real incident (category: {record['category']}):\n"
        f"{record['summary']}\n\n"
        f"Construct the contrast scenario now, per the rules."
    )


def call_deepseek(record: dict, api_key: str) -> dict:
    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(record)},
        ],
        "temperature": 0.7,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    content = result["choices"][0]["message"]["content"].strip()
    # strip accidental markdown fences
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate_synthetic_contrast.py <true_record_id> [<true_record_id> ...]")
        return 1

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("REFUSED: no DEEPSEEK_API_KEY in environment.")
        return 1

    target_ids = sys.argv[1:]

    real_records = {}
    with open(REAL_DATASET, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            real_records[r["id"]] = r

    missing = [tid for tid in target_ids if tid not in real_records]
    if missing:
        print(f"REFUSED: these ids don't exist in the real dataset: {missing}")
        return 1

    existing_out = []
    if OUT_PATH.exists():
        with open(OUT_PATH, encoding="utf-8") as f:
            existing_out = [json.loads(l) for l in f if l.strip()]
    already_done = {r["based_on"] for r in existing_out}

    new_out = []
    for tid in target_ids:
        if tid in already_done:
            print(f"skip (already generated): {tid}")
            continue
        record = real_records[tid]
        print(f"generating for: {tid} ({record['category']})")
        gen = call_deepseek(record, api_key)
        out_record = {
            "id": f"SYNTH-{tid}-CONTRAST",
            "category": record["category"],
            "based_on": tid,
            "synthetic": True,
            "scenario_setup": gen["scenario_setup"],
            "correct_behavior": gen["correct_behavior"],
            "generated_by": "deepseek-reasoner",
            "generated_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        new_out.append(out_record)
        print(f"  -> {out_record['id']}")

    if not new_out:
        print("Nothing new to generate.")
        return 0

    all_out = existing_out + new_out
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in all_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(new_out)} new record(s), {len(all_out)} total, to {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
