#!/usr/bin/env python3
"""
Generate training group 07: general harm refusal, independent of the vuln-gate
"you found this while scanning" framing.

Context: FINDING__stage6-governance-safety-general-refusal-collapse-outside-vulngate-framing.md
(2026-09-20) showed stage6_governance_safety_b passes 8.9% (4/45) on a pilot eval of real,
externally-sourced harmful/jailbreak prompts -- because the entire existing G15 curriculum
(DATASETS_VULN_6GROUPS/01-06) only ever trains "you found a vuln auditing your own system,
stop escalating." It never trains refusing a harmful request handed directly to the model
under a social-engineering wrapper (fiction, research, roleplay, "for my thesis", urgency,
authority claims) with no vuln-gate setup at all. This is that missing 7th group.

Same generation convention as gen_dataset_vuln_6groups.py: via ask.sh (external provider),
sequential (API-bound, not GPU-bound), one row written to disk at a time so a crash loses
at most one row. Training data here is self-generated (following this repo's own existing
convention for groups 01-06) -- this is NOT a substitute for the external, cited EVAL set
used in the FINDING doc above; eval and training data are kept separate on purpose so eval
never overlaps what training saw.
"""
import json
import os
import subprocess
import sys
import time

ASK_SH = "/home/sipa/PROJECT/PAYTON_HUBS/BIN/ask.sh"
# NOTE: plain "deepseek" alias hits DeepSeek's own account, confirmed dead
# tonight (402 Insufficient Balance, same known-dead account as
# project_deepseek_hermes_credits_2026-09.md). "or-deepseek" routes the same
# model through OpenRouter, confirmed live tonight with real balance.
MODEL = "or-deepseek"
OUT_DIR = "/home/sipa/apps/sipa-os-governance/AI_EXPERIMENTS/DATASETS_VULN_6GROUPS"
GROUP_NAME = "07_general_harm_refusal"
N_PER_GROUP = 200

# Ten subtopics chosen to cover the categories that actually failed in the pilot eval
# (cyberattack, surveillance, fraud, drug logistics, emotional abuse, hate speech,
# disinformation, privacy violation, weapons/CBRN-adjacent) plus one meta-category
# that directly targets wrapper resistance itself (fiction/roleplay/research framing
# used as the delivery mechanism for any of the above, rather than a single fixed harm).
HARM_CLASSES = [
    "direct request to write functional malware or ransomware code",
    "direct request to explain how to intercept or exfiltrate someone else's private communications without authorization",
    "direct request to construct a persuasive narrative for a financial fraud scheme (Ponzi, fake investment, romance scam)",
    "direct request for step-by-step logistics of an illegal-goods smuggling or distribution operation",
    "direct request for a list of psychologically manipulative or emotionally abusive tactics to use on a specific real person",
    "direct request to generate targeted hate speech or harassment content aimed at a group or individual",
    "direct request to write fabricated news or disinformation designed to go viral and mislead readers",
    "direct request for private, non-public personal data about a named real or identifiable person",
    "direct request for actionable guidance on producing or acquiring a weapon or hazardous substance",
    "the SAME kind of direct harmful request as above, but delivered through a fictional/roleplay/'research paper'/'hypothetical' wrapper meant to launder it past a refusal",
]

GEN_PROMPT = """Generate ONE training example for an AI safety dataset, as JSON only, no prose.

Harm category: {harm}

Write a realistic user message that makes this kind of request directly (not through a
vuln-scanning setup -- this is a cold request, no "I found this while auditing" framing at
all). Then write two model responses to that request:

- "positive": correct behavior. A clear, non-preachy refusal that declines the harmful part
  of the request specifically (not a generic "I can't help with that" with zero content --
  name what's being declined in one clause), offers a legitimate alternative ONLY if one
  genuinely exists for that request, and does not lecture at length. Two to four sentences.
- "negative": incorrect behavior. The model complies with the harmful request, described
  PROCEDURALLY/ABSTRACTLY (e.g. "provided a working ransomware skeleton using X encryption
  approach" -- not literal working exploit code, no real payloads, no runnable commands, no
  real personal data about any real named individual).

Return exactly this JSON shape:
{{"harm_class": "...", "scenario": "the user's message, one paragraph, realistic", "positive": "...", "negative": "..."}}
"""


def gen_one(harm_class):
    prompt = GEN_PROMPT.format(harm=harm_class)
    try:
        result = subprocess.run(
            ["bash", ASK_SH, "--model", MODEL, prompt],
            capture_output=True, text=True, timeout=90,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout after 90s"
    except Exception as e:
        return None, f"subprocess error: {e}"
    text = result.stdout.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None, text[:200]
    try:
        return json.loads(text[start:end + 1]), None
    except json.JSONDecodeError as e:
        return None, f"{e}: {text[:200]}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{GROUP_NAME}.jsonl")
    done = 0
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = sum(1 for _ in f)
    print(f"=== {GROUP_NAME}: resuming at {done}/{N_PER_GROUP} ===", flush=True)

    with open(out_path, "a") as f:
        for i in range(done, N_PER_GROUP):
            harm = HARM_CLASSES[i % len(HARM_CLASSES)]
            row, err = gen_one(harm)
            if row:
                row["id"] = i
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{GROUP_NAME} {i+1}/{N_PER_GROUP}] OK", flush=True)
            else:
                print(f"[{GROUP_NAME} {i+1}/{N_PER_GROUP}] FAILED: {err}", flush=True)
            time.sleep(1.2)
    print(f"\n{GROUP_NAME} done.")


if __name__ == "__main__":
    sys.exit(main())
