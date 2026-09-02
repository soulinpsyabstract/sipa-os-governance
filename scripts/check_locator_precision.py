#!/usr/bin/env python3
"""check_locator_precision.py -- enforcing dipankarsarkar's round 12 fix,
extended round 13 for the same reason round 12 existed in the first place.

Round 12 finding: "verifiability" == "mechanised" was a hidden, hand-maintained,
perfectly-correlated function of whether source_locator happened to name a
specific table/row in prose. Nothing enforced the correlation -- it just never
drifted, by luck, across 4 records. His fix: split out an orthogonal field,
locator_precision (document | section | row), and compute verifiability's
"mechanised" value FROM that field rather than asserting both by hand. This
script is the enforcement that field split was supposed to buy: it checks the
invariant holds, instead of trusting that it still will.

Round 13 finding, one level up: the census numbers describing this file (n,
mechanised count, locator_precision counts) were being hand-typed into commit
messages and chat, and the hand-typed version was wrong -- not from bad faith,
from comparing two states that weren't adjacent (a pre-expansion 4/25 against
a mid-fix 5/51, skipping the real immediately-prior state, 4/51, and thereby
skipping a real percentage dip the file went through in between). Same fix as
round 12, one layer up: don't hand-summarize a file whose invariants a script
already checks. This script now PRINTS the census on success, so any number
that goes in a commit message or a reply can be copy-pasted generated output
carrying its own commit, not something a person re-derives from memory.

Round 13 also added locator_exhaustive (bool): orthogonal to locator_precision
the same way locator_precision is orthogonal to verifiability. A record can be
pinned as precisely as its SOURCE permits (locator_exhaustive=true) while
still capped below "row" because the source itself has no table -- prose has
a hard ceiling under document/section/row no matter how well anyone does the
work. Before this field, "mechanised" was reading as "the source happens to
ship a table," not "the claim is checked as far as it can be." A record with
locator_precision=="row" is, by construction, pinned to the finest unit any
table offers -- so that implies locator_exhaustive=true; nothing in a source
can be finer than the specific cell a script would check.

Round 14 finding, the exact same bug shape one field over: locator_exhaustive
was left ABSENT on the 39 records with no locator_precision, present (and
always True) only on the 24 that had one. That reproduced round 12's original
bug -- a field that looks orthogonal but is actually 100% determined by
another field, with nothing testing the distinction, because round 13's own
wording ("doesn't apply to the 37+ records with no source_locator") excluded
those records from the field's base population instead of giving them an
explicit value. His fix, applied here: locator_precision: null,
locator_exhaustive: false are now present on ALL 63 records, not just the 24
with a locator -- and the invariant that makes it stick is the round-12
pattern one level up: locator_precision is None iff locator_exhaustive is
False. Without enforcing this, nothing stops the next record entering with
the field simply omitted, silently reproducing the exact same gap again.

What it does: for every record in
AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/misbehavior_incidents_seed_v1.jsonl,
asserts:
  1. verifiability=="mechanised" if and only if locator_precision=="row"
     (round 12's invariant).
  2. locator_precision=="row" implies locator_exhaustive==true (round 13's
     invariant -- row precision cannot coexist with "more precision is
     possible").
  3. Both "locator_precision" and "locator_exhaustive" keys are PRESENT on
     every record (round 14's invariant -- a missing key is exactly what let
     the previous bug hide; this must fail loud, not silently .get() a None).
  4. locator_precision is None if and only if locator_exhaustive is False
     (round 14's invariant, proper -- makes the null/false pairing on the
     no-locator records a checked fact, not a one-time bulk edit that can
     drift the next time a record is added).
Then, on success, prints n, the verifiability counts, the locator_precision
counts (now split has-locator vs. null), and the locator_exhaustive counts
across ALL records (not just the 24 with a locator -- there is no longer a
"doesn't apply" carve-out; every record has an explicit value).

This does NOT check whether a locator_precision or locator_exhaustive value
is actually correct (that a "row" claim really does point at a specific row,
or that a "document"-capped record really has no finer address in its
source) -- those stay human-checked judgment calls, same as verifiability
always was. It only checks the correlations that were silently unenforced.

Exit code is nonzero iff any record violates an invariant, so this can run
alongside check_dataset_citations.py as a pre-commit step -- built by Claude,
2026-09-01/09-02, in direct response to dipankarsarkar's rounds 12, 13, and 14.
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"


def main() -> int:
    violations = []
    records = []
    with open(DATASET, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            records.append(record)
            rid = record.get("id", f"<line {lineno}>")
            v = record.get("verifiability")

            if "locator_precision" not in record or "locator_exhaustive" not in record:
                violations.append(
                    f"{rid}: missing locator_precision and/or locator_exhaustive key -- both must be "
                    f"present on every record (round 14: an absent key is exactly how the last two "
                    f"bugs hid). Use locator_precision: null, locator_exhaustive: false if there's no "
                    f"locator."
                )
                continue

            lp = record["locator_precision"]
            le = record["locator_exhaustive"]

            if v == "mechanised" and lp != "row":
                violations.append(
                    f"{rid}: verifiability=mechanised but locator_precision={lp!r} (expected 'row')"
                )
            if lp == "row" and v != "mechanised":
                violations.append(
                    f"{rid}: locator_precision=row but verifiability={v!r} (expected 'mechanised')"
                )
            if lp == "row" and le is not True:
                violations.append(
                    f"{rid}: locator_precision=row but locator_exhaustive={le!r} (expected true -- "
                    f"a row citation is the finest unit any table offers)"
                )
            if (lp is None) != (le is False):
                violations.append(
                    f"{rid}: locator_precision={lp!r} / locator_exhaustive={le!r} -- these must agree: "
                    f"locator_precision is None iff locator_exhaustive is False (round 14's invariant)"
                )

    if violations:
        print(f"FAIL: {len(violations)} invariant violation(s) in {DATASET.relative_to(REPO_ROOT)}")
        for v in violations:
            print(f"  - {v}")
        return 1

    n = len(records)
    verif_counts = Counter(r.get("verifiability") for r in records)
    has_locator = [r for r in records if r["locator_precision"] is not None]
    locp_counts = Counter(r["locator_precision"] for r in has_locator)
    exhaustive_counts = Counter(r["locator_exhaustive"] for r in records)  # now spans all n, round 14

    print(f"OK: verifiability<->locator_precision<->locator_exhaustive invariants hold across all records "
          f"in {DATASET.relative_to(REPO_ROOT)}")
    print()
    print(f"n = {n}")
    print(f"verifiability:      " + ", ".join(f"{k}={v}" for k, v in sorted(verif_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_precision:  " + ", ".join(f"{k}={v}" for k, v in sorted(locp_counts.items(), key=lambda kv: str(kv[0]))) +
          f"  (of {len(has_locator)} records with a locator; {n - len(has_locator)} explicitly null)")
    print(f"locator_exhaustive: " + ", ".join(f"{k}={v}" for k, v in sorted(exhaustive_counts.items(), key=lambda kv: str(kv[0]))) +
          f"  (across all {n} records -- present on every one as of round 14)")
    mech = verif_counts.get("mechanised", 0)
    print(f"mechanised: {mech}/{n} = {mech/n*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
