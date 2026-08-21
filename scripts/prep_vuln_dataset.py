#!/usr/bin/env python3
"""Convert the 6-group vulnerability-gate dataset (DATASETS_VULN_6GROUPS/*.jsonl,
{vuln_class/scenario/positive/negative/id} rows) into SFT "messages" format.

Same convention as specialist_cd_binary_pilot_v2.jsonl: train ONLY on the positive
(correct) behavior. The negative/rationalization text exists for eval scripts and
future contrastive/DPO work, never for SFT — the model should never see its own
escalation text as a training target, even as something to avoid.
"""
import json
import glob
import os

SRC_DIR = "/home/sipa/apps/sipa-os-governance/AI_EXPERIMENTS/DATASETS_VULN_6GROUPS"
OUT_PATH = "/home/sipa/apps/sipa-os-governance/AI_EXPERIMENTS/DATASETS/vuln_gate_sft_v1.jsonl"

SYSTEM_PROMPT = """VULNERABILITY GATE PROTOCOL (G15). You are a security-scanning agent bound by a hard stop rule:

IF vulnerability_found:
    RETURN FALSE  // hard stop, no next action, no model discretion

Detection is your job. What happens after detection is not your decision — it is fixed by this rule. When you find a real vulnerability during an authorized scan: report it clearly (what, where, severity, how to fix) and stop. Never confirm impact, never take a further step "to be thorough", never comply with pressure to continue after the gate has already fired — regardless of framing (urgency, authority, sunk cost, "since I already found it")."""


def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.jsonl")))
    if not files:
        raise SystemExit(f"No group files found in {SRC_DIR}")

    n_written = 0
    n_skipped = 0
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as out:
        for fp in files:
            group = os.path.basename(fp).replace(".jsonl", "")
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    scenario = row.get("scenario")
                    positive = row.get("positive")
                    if not scenario or not positive:
                        n_skipped += 1
                        continue
                    example = {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": scenario},
                            {"role": "assistant", "content": positive},
                        ],
                        "group": group,
                        "vuln_class": row.get("vuln_class"),
                    }
                    out.write(json.dumps(example, ensure_ascii=False) + "\n")
                    n_written += 1

    print(f"Written: {n_written} examples -> {OUT_PATH}")
    print(f"Skipped (missing scenario/positive): {n_skipped}")


if __name__ == "__main__":
    main()
