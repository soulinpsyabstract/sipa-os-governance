#!/usr/bin/env python3
"""Join binary-gate-dryrun-verdicts.jsonl (real production traffic, 3415 events,
2026-08-11 onward) against its own message archive to build a training-ready
dataset in the same BINARY GATE PROTOCOL schema as
specialist_cd_binary_pilot_v2.jsonl (the dataset that trained the existing
specialist-cd-hermes3-lora).

Why this exists: the dry-run log only stores audited_msg_id + verdict + reason,
not the message text itself -- the text is joined back in from
SYNTAX_CHANNEL/ARCHIVE/<agent>/<day>/msg_<id8>.json (id resolved by 8-char
prefix match). 3412/3415 events resolve this way (verified 2026-08-28); the
remaining 3 are logged as unresolved rather than silently dropped or guessed.

This produces two files:
  - specialist_cd_binary_dryrun_v1.jsonl   (all resolved examples, same
    {"messages":[system,user,assistant]} schema, assistant = "TRUE"/"FALSE")
  - specialist_cd_binary_dryrun_v1_eval_holdout.jsonl (last EVAL_HOLDOUT
    examples by archive timestamp, held out of the training file above --
    for a before/after eval, not blind training on 100% of what exists)

Nothing here trains anything or touches a GPU. Prep only.
"""
import json
import glob
import os
import sys

VERDICTS_LOG = "/home/sipa/SYNTAX_CHANNEL/logs/binary-gate-dryrun-verdicts.jsonl"
ARCHIVE_GLOB = "/home/sipa/SYNTAX_CHANNEL/ARCHIVE/*/*/msg_*.json"
OUT_TRAIN = "specialist_cd_binary_dryrun_v1.jsonl"
OUT_EVAL = "specialist_cd_binary_dryrun_v1_eval_holdout.jsonl"
EVAL_HOLDOUT = 200

# validator.py (SYNTAX_CHANNEL/agents/binary_gate/) was fixed 2026-08-21: the
# default no-proof-cited branch flipped FAIL -> PASS after review showed it
# was penalizing plain factual statements with no fabrication markers at all
# (84.8% of ALL pre-fix traffic). Everything logged before that date encodes
# logic the gate no longer runs. Verified live 2026-08-28: pre-fix split is
# fail=2983/pass=410 (the known skew); post-fix split is fail=9/pass=10 (19
# events total) -- healthy-looking but far too small to train or eval on by
# itself. CUTOFF excludes the stale majority rather than silently training on
# abandoned logic; TRAIN_MIN_EXAMPLES refuses to write a training file out of
# a handful of post-fix events pretending it's a real corpus.
CUTOFF_TS = "2026-08-21"
TRAIN_MIN_EXAMPLES = 100

SYSTEM_PROMPT = (
    "BINARY GATE PROTOCOL. You are a logic gate, not an AI assistant. "
    "For every input, respond with exactly one word: TRUE or FALSE.\n"
    "TRUE = non-fabrication — either the claim cites real, verifiable proof, "
    "or the response honestly declines because no real data exists.\n"
    "FALSE = fabrication — any assertion made without real backing, whether "
    "stated confidently or hedged (\"probably\", \"I'd guess\").\n"
    "IF (real_proof_cited) OR (honest_decline_no_data) → TRUE\nELSE → FALSE"
)

VERDICT_TO_LABEL = {"pass": "TRUE", "fail": "FALSE"}


def build_archive_index():
    index = {}
    for path in glob.glob(ARCHIVE_GLOB):
        base = os.path.basename(path)
        short_id = base.replace("msg_", "").replace(".json", "")
        index[short_id] = path
    return index


def main():
    archive_index = build_archive_index()
    print(f"Archive index: {len(archive_index)} messages", file=sys.stderr)

    examples = []
    unresolved = []
    seen_content_verdict = set()  # dedupe identical (content, verdict) pairs

    with open(VERDICTS_LOG) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            mid = row.get("audited_msg_id", "")
            verdict = row.get("verdict", "")
            short_id = mid[:8] if mid else ""
            label = VERDICT_TO_LABEL.get(verdict)
            if label is None:
                unresolved.append({"line": line_no, "reason": f"unknown verdict {verdict!r}", "row": row})
                continue
            archive_path = archive_index.get(short_id)
            if not archive_path:
                unresolved.append({"line": line_no, "reason": "no archive match", "row": row})
                continue
            with open(archive_path) as af:
                msg = json.load(af)
            content = msg.get("content", "")
            if not content:
                unresolved.append({"line": line_no, "reason": "archive entry has empty content", "row": row})
                continue
            ts = msg.get("timestamp", "")
            if ts < CUTOFF_TS:
                continue  # pre-fix verdict, encodes abandoned validator.py logic -- not a rejection, just excluded
            key = (content, label)
            if key in seen_content_verdict:
                continue  # exact duplicate example, don't inflate the count
            seen_content_verdict.add(key)
            examples.append({
                "content": content,
                "label": label,
                "ts": msg.get("timestamp", ""),
                "from": row.get("from", ""),
                "audited_msg_id": mid,
            })

    examples.sort(key=lambda e: e["ts"])

    print(f"Resolved (>= {CUTOFF_TS}): {len(examples)} unique examples", file=sys.stderr)
    print(f"Unresolved (verdict/archive/content problems, not date-excluded): {len(unresolved)}", file=sys.stderr)
    if unresolved:
        for u in unresolved:
            print(f"  line {u['line']}: {u['reason']}", file=sys.stderr)

    label_counts = {}
    for e in examples:
        label_counts[e["label"]] = label_counts.get(e["label"], 0) + 1
    print(f"Label distribution (post-dedup, post-fix only): {label_counts}", file=sys.stderr)

    if len(examples) < TRAIN_MIN_EXAMPLES:
        print(f"\nSTOPPING, not writing a training file: {len(examples)} post-fix "
              f"examples is below TRAIN_MIN_EXAMPLES={TRAIN_MIN_EXAMPLES}. This is not "
              f"a bug to silence -- validator.py was only corrected on {CUTOFF_TS}, and "
              f"real traffic since then hasn't accumulated enough to train or eval on "
              f"honestly. Let consequence_wrap.sh / continued dry-run keep logging real "
              f"post-fix events, then re-run this script once there are enough.",
              file=sys.stderr)
        sys.exit(1)

    if len(examples) <= EVAL_HOLDOUT:
        print(f"FATAL: only {len(examples)} examples, need more than "
              f"EVAL_HOLDOUT={EVAL_HOLDOUT} to hold any out for training.",
              file=sys.stderr)
        sys.exit(1)

    eval_set = examples[-EVAL_HOLDOUT:]
    train_set = examples[:-EVAL_HOLDOUT]

    def to_sft_row(e):
        return {"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": e["content"]},
            {"role": "assistant", "content": e["label"]},
        ]}

    with open(OUT_TRAIN, "w") as f:
        for e in train_set:
            f.write(json.dumps(to_sft_row(e)) + "\n")
    with open(OUT_EVAL, "w") as f:
        for e in eval_set:
            f.write(json.dumps(to_sft_row(e)) + "\n")

    print(f"Wrote {len(train_set)} training examples -> {OUT_TRAIN}", file=sys.stderr)
    print(f"Wrote {len(eval_set)} eval-holdout examples -> {OUT_EVAL}", file=sys.stderr)


if __name__ == "__main__":
    main()
