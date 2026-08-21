#!/usr/bin/env python3
"""
Generate 6 specialist datasets (200 rows each) for the vulnerability-agent
LoRA-merge experiment: groups 1-5 are vulnerability-class specialists,
group 6 is the "stop-gate holds under pressure" specialist — adversarial
rationalization framings, not vulnerability classes (this is the axis
Yusufchy flagged as untested in the earlier specialist-cd series critique).

Generation via ask.sh (external provider), not parallel Agent calls — see
feedback_dataset_gen_use_asksh_not_agents.md (26 parallel Agent calls for
dataset generation blew the subscription limit twice).

Groups run sequentially, not in parallel — this is API-bound, not GPU-bound,
and sequential keeps us under any single provider's rate limits. Each row is
written to disk immediately (not just at the end) so a crash mid-run loses
at most one row, not the whole group.
"""
import json
import os
import subprocess
import sys
import time

ASK_SH = "/home/sipa/PROJECT/PAYTON_HUBS/BIN/ask.sh"
MODEL = "deepseek"
OUT_DIR = "/home/sipa/apps/sipa-os-governance/AI_EXPERIMENTS/DATASETS_VULN_6GROUPS"
N_PER_GROUP = 200

GROUPS = {
    "01_secrets_credentials": [
        "exposed .env file with database credentials",
        "leaked AWS access key in client-side JavaScript",
        "hardcoded API key in a public commit",
        "exposed .npmrc with private registry token",
        "leaked Stripe secret key in error logs",
        "exposed SSH private key in a backup file",
        "leaked OAuth client secret in a mobile app bundle",
        "exposed .aws/credentials file",
        "leaked database connection string in a Docker image layer",
        "exposed Kubernetes secret via misconfigured RBAC",
    ],
    "02_access_control": [
        "admin panel with default credentials still active",
        "predictable/sequential session token",
        "authentication bypass via parameter tampering",
        "privilege escalation via an unchecked role parameter",
        "password reset token that never expires",
        "missing rate limiting on a login endpoint",
        "JWT signature not verified server-side",
        "insecure direct object reference exposing other users' data",
        "2FA bypass via response manipulation",
        "session fixation vulnerability",
    ],
    "03_injection": [
        "SQL injection in a search parameter",
        "SSRF via an unvalidated webhook URL field",
        "command injection via a file-upload filename",
        "XML external entity (XXE) injection",
        "NoSQL injection in a MongoDB query field",
        "template injection in a report-generation feature",
        "LDAP injection in a login form",
        "header injection via an unvalidated redirect parameter",
        "path traversal in a file-download endpoint",
        "deserialization vulnerability in a session-handling library",
    ],
    "04_infra_misconfig": [
        "misconfigured S3-style bucket with public read access",
        "exposed .git directory revealing source code",
        "missing HTTPS redirect exposing session cookies",
        "missing security headers (CSP, HSTS)",
        "exposed Docker daemon API",
        "open Redis instance with no authentication",
        "misconfigured CORS allowing any origin",
        "exposed .DS_Store revealing directory structure",
        "publicly accessible internal API documentation",
        "verbose error messages leaking stack traces",
    ],
    "05_supply_chain": [
        "outdated dependency with a known public CVE",
        "typosquatted package installed via dependency confusion",
        "compromised npm package in the build pipeline",
        "outdated TLS library with a known vulnerability",
        "unpatched CMS plugin with a public exploit",
        "vulnerable Docker base image",
        "outdated WordPress core with a known RCE",
        "unmaintained dependency with unpatched vulnerabilities",
        "vulnerable transitive dependency",
        "outdated SSL/TLS protocol version still enabled",
    ],
    "06_stop_gate_pressure": [
        "since-I-already-found-it framing: might as well confirm real impact",
        "urgency framing: this needs fixing right now, just patch it directly",
        "authority framing: the owner said to go ahead and verify further",
        "sunk-cost framing: stopping now wastes the access already gained",
        "helpfulness framing: a thorough agent would go the extra mile",
        "ambiguous-scope framing: this adjacent system might be in scope too",
        "incremental framing: just one small confirming step, not a full exploit",
        "reporting-quality framing: a fuller report needs proof of impact",
        "implied-instruction framing: the task description implied full remediation",
        "normalization framing: previous runs always went one step further, this is routine",
    ],
}

GEN_PROMPT_VULN = """Generate ONE training example for an AI security-agent dataset, as JSON only, no prose.

Vulnerability class: {vuln}

The scenario: an authorized passive security scan (owner's own infrastructure, permission
already granted) discovers this issue. Write two model responses to that discovery:

- "positive": correct behavior. Starts with the literal marker
  {{"vulnerability_found": true, "action": "STOP"}} as the first line, then reports the
  finding clearly (what, where, severity, how to fix). Does not attempt to use the finding
  for anything beyond reporting it.
- "negative": incorrect behavior. Either omits the marker or emits it but keeps going anyway —
  reasons its way into going further than reporting, framed as "since I already found it,
  might as well confirm impact" or similar rationalization. Keep this PROCEDURAL/ABSTRACT
  (e.g. "began constructing a request to extract the credentials file" — not literal working
  exploit code, no real payloads, no runnable commands).

Return exactly this JSON shape:
{{"vuln_class": "...", "scenario": "one paragraph, concrete, first person as the scanning agent", "positive": "...", "negative": "..."}}
"""

GEN_PROMPT_PRESSURE = """Generate ONE training example for an AI security-agent dataset, as JSON only, no prose.

Pressure framing: {vuln}

The scenario: an authorized passive security scan already found a real vulnerability and
correctly emitted a STOP marker. Now write a SECOND turn — additional context/pressure is
introduced (a follow-up instruction, an inference, a framing) matching the pressure framing
above, trying to talk the agent past its own stop. Write two responses to that pressure:

- "positive": correct behavior. The gate holds. States plainly (in one or two sentences) that
  the stop marker already fired and no further action follows regardless of the framing —
  does not re-litigate, does not partially comply, does not get talked into "just checking".
- "negative": incorrect behavior. The agent is persuaded by the framing and takes some action
  beyond the original report — described PROCEDURALLY/ABSTRACTLY, no real exploit code.

Return exactly this JSON shape:
{{"vuln_class": "...", "scenario": "one paragraph, concrete, first person, describing the original finding PLUS the pressure framing being applied", "positive": "...", "negative": "..."}}
"""


def gen_one(group_name, vuln_class):
    prompt = (GEN_PROMPT_PRESSURE if group_name == "06_stop_gate_pressure" else GEN_PROMPT_VULN).format(vuln=vuln_class)
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


def run_group(group_name, vuln_classes):
    out_path = os.path.join(OUT_DIR, f"{group_name}.jsonl")
    done = 0
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = sum(1 for _ in f)
    print(f"=== {group_name}: resuming at {done}/{N_PER_GROUP} ===")

    with open(out_path, "a") as f:
        for i in range(done, N_PER_GROUP):
            vuln = vuln_classes[i % len(vuln_classes)]
            row, err = gen_one(group_name, vuln)
            if row:
                row["id"] = i
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{group_name} {i+1}/{N_PER_GROUP}] OK")
            else:
                print(f"[{group_name} {i+1}/{N_PER_GROUP}] FAILED: {err}")
            time.sleep(1.2)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for group_name, vuln_classes in GROUPS.items():
        run_group(group_name, vuln_classes)
    print("\nAll 6 groups done.")


if __name__ == "__main__":
    sys.exit(main())
