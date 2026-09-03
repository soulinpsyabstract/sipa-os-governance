#!/usr/bin/env python3
"""check_locator_precision.py -- enforcing dipankarsarkar's round 12 fix,
extended round 13, 14, and 15 for the same reason round 12 existed in the
first place.

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
from comparing two states that weren't adjacent. Same fix as round 12, one
layer up: this script PRINTS the census on success, so any number that goes
in a commit message or a reply is copy-pasted generated output tied to a
specific commit, not something re-derived from memory.

Round 13 also added locator_exhaustive (bool): meant to be orthogonal to
locator_precision -- whether a citation was pinned as precisely as its
SOURCE permits, independent of what that precision level is. A record can be
capped below "row" because the source itself has no table, while still being
exhaustive for what the source offers.

Round 14 finding, same bug shape one field over: locator_exhaustive was
ABSENT on the 39 records with no locator_precision, present (and always
True) only on the 24 that had one -- a field that looks orthogonal but is
100% determined by another field. Fix applied then: locator_precision: null,
locator_exhaustive: false on all 63 records, with an invariant forcing
`locator_precision is None <-> locator_exhaustive is False`.

Round 15 finding (dipankarsarkar, 2026-09-03): round 14's own fix was the
SAME bug, restated as a formula. `(lp is None) != (le is False)` forces le
to be fully determined by lp -- True whenever a locator exists, False
whenever it doesn't, zero independent bits either way. Verified directly:
among the 24 records with a locator, locator_exhaustive was True 24, False
0 -- exactly what round 13 already found, unfixed by round 14. His sharper
point: a naive "does this field vary across the whole file" census now
reads False=39/True=24 and looks like a healthy binary -- but that health
is an ARTIFACT of the false=39 default padding a field that's still
constant within the only population where it means anything. He proposed
the general fix: scope every field's distinctness check to the population
where it actually applies, not the whole file.

His closing question -- is locator_exhaustive's scope the 24 records with a
locator, or all 63? -- answered here, not left open: the 24. The field asks
"was THIS citation pinned as exhaustively as its source permits" -- a
record with no citation has nothing to evaluate exhaustiveness OF. Round
14's `false` on the 39 no-locator records conflated "not applicable" with
"applicable and false", which is exactly what let the padding look like a
real second value. Fix: `locator_exhaustive: null` (matching
`locator_precision: null`) on those 39, not `false`. The invariant is now
`locator_precision is None <-> locator_exhaustive is None` -- and, within
the real scope (the 24), locator_exhaustive is no longer forced to any
particular value by anything in this file; it can genuinely be False the
day a real non-exhaustive-but-located record is found and added.

What it does: for every record in
AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/misbehavior_incidents_seed_v1.jsonl,
asserts:
  1. verifiability=="mechanised" if and only if locator_precision=="row"
     (round 12's invariant).
  2. locator_precision=="row" implies locator_exhaustive==true (round 13's
     invariant -- a real entailment, not a redundant derivation: "row" is
     by construction the finest unit any table offers, so nothing in the
     source could make it more exhaustive).
  3. Both "locator_precision" and "locator_exhaustive" keys are PRESENT on
     every record (round 14's invariant -- a missing key is exactly how the
     first two bugs hid).
  4. locator_precision is None if and only if locator_exhaustive is None
     (round 15's invariant, replacing round 14's tautological version --
     "no locator" and "not applicable" are now the same null, on both
     fields, instead of a forced boolean standing in for "N/A").
  5. Where locator_precision is not None, locator_exhaustive is a real bool
     (True or False) -- never re-derives which one from lp; that's the
     thing round 15 found was wrong to do.
Then, on success, prints n, the verifiability counts, the locator_precision
counts, and locator_exhaustive counts SCOPED to the 24 records where it
applies (not the whole 63 -- round 15's own point: a whole-file census can
look healthy while the scoped population is still constant). If the scoped
population has collapsed to a single value, this prints a WARNING (not a
hard failure -- small-n collapse isn't automatically a bug, and the
architect's own judgment on the data is what round 15 said can't be settled
from the code alone) so it stays visible instead of silently reading as
"fine" the way round 14's version did.

This does NOT check whether a locator_precision or locator_exhaustive value
is actually correct (that a "row" claim really does point at a specific row,
or that a "document"-capped record really has no finer address in its
source) -- those stay human-checked judgment calls, same as verifiability
always was. It only checks the correlations that were silently unenforced.

Exit code is nonzero iff any record violates a hard invariant, so this can
run alongside check_dataset_citations.py as a pre-commit step -- built by
Claude, 2026-09-01 through 09-03, in direct response to dipankarsarkar's
rounds 12, 13, 14, and 15.
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
                    f"present on every record. Use null on both if there's no locator."
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
            if (lp is None) != (le is None):
                violations.append(
                    f"{rid}: locator_precision={lp!r} / locator_exhaustive={le!r} -- these must agree: "
                    f"locator_precision is None iff locator_exhaustive is None (round 15's invariant -- "
                    f"'no locator' and 'not applicable' are the same null on both fields)"
                )
            if lp is not None and not isinstance(le, bool):
                violations.append(
                    f"{rid}: locator_precision={lp!r} but locator_exhaustive={le!r} is not a real bool "
                    f"(a record with a locator must have locator_exhaustive true or false, judged on its "
                    f"own merits -- not derived from lp)"
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
    # round 15: scope locator_exhaustive's census to where it applies (the 24), not the
    # whole 63 -- a whole-file count of {False: 39, True: 24} looks like a healthy binary
    # while the real, scoped population is still constant. That was the bug.
    exhaustive_scoped = Counter(r["locator_exhaustive"] for r in has_locator)

    print(f"OK: verifiability<->locator_precision<->locator_exhaustive invariants hold across all records "
          f"in {DATASET.relative_to(REPO_ROOT)}")
    print()
    print(f"n = {n}")
    print(f"verifiability:      " + ", ".join(f"{k}={v}" for k, v in sorted(verif_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_precision:  " + ", ".join(f"{k}={v}" for k, v in sorted(locp_counts.items(), key=lambda kv: str(kv[0]))) +
          f"  (of {len(has_locator)} records with a locator; {n - len(has_locator)} explicitly null)")
    print(f"locator_exhaustive (scoped to the {len(has_locator)} records where it applies): " +
          ", ".join(f"{k}={v}" for k, v in sorted(exhaustive_scoped.items(), key=lambda kv: str(kv[0]))))
    if len(exhaustive_scoped) <= 1 and has_locator:
        print(f"  WARNING: locator_exhaustive has collapsed to a single value within its own scope "
              f"({len(has_locator)} records). This is not a hard failure -- it may just be genuinely "
              f"true of every located record so far -- but round 15's whole point is that this state is "
              f"easy to miss, so it's printed loudly instead of silently reading as fine.")
    mech = verif_counts.get("mechanised", 0)
    print(f"mechanised: {mech}/{n} = {mech/n*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
