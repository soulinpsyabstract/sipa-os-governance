#!/usr/bin/env python3
"""check_locator_precision.py -- enforcing dipankarsarkar's round 12 fix.

Round 12 finding: "verifiability" == "mechanised" was a hidden, hand-maintained,
perfectly-correlated function of whether source_locator happened to name a
specific table/row in prose. Nothing enforced the correlation -- it just never
drifted, by luck, across 4 records. His fix: split out an orthogonal field,
locator_precision (document | section | row), and compute verifiability's
"mechanised" value FROM that field rather than asserting both by hand. This
script is the enforcement that field split was supposed to buy: it checks the
invariant holds, instead of trusting that it still will.

What it does: for every record in
AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/misbehavior_incidents_seed_v1.jsonl,
asserts verifiability=="mechanised" if and only if locator_precision=="row".
A record with verifiability=="mechanised" but no locator_precision at all is
also flagged -- that's the exact gap this script exists to close, a claim of
"mechanised" with nothing backing which precision level earned it.

This does NOT check whether a locator_precision value is actually correct
(that a "row" claim really does point at a specific row) -- that's still a
human-checked judgment call, same as verifiability always was. It only
checks the one thing that was silently unenforced: the correlation itself.

Exit code is nonzero iff any record violates the invariant, so this can run
alongside check_dataset_citations.py as a pre-commit step -- built by Claude,
2026-09-01, in direct response to dipankarsarkar's round 12 message.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"


def main() -> int:
    violations = []
    with open(DATASET, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rid = record.get("id", f"<line {lineno}>")
            v = record.get("verifiability")
            lp = record.get("locator_precision")

            if v == "mechanised" and lp != "row":
                violations.append(
                    f"{rid}: verifiability=mechanised but locator_precision={lp!r} (expected 'row')"
                )
            if lp == "row" and v != "mechanised":
                violations.append(
                    f"{rid}: locator_precision=row but verifiability={v!r} (expected 'mechanised')"
                )

    if violations:
        print(f"FAIL: {len(violations)} invariant violation(s) in {DATASET.relative_to(REPO_ROOT)}")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(f"OK: verifiability<->locator_precision invariant holds across all records in {DATASET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
