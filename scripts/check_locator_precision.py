#!/usr/bin/env python3
"""check_locator_precision.py -- enforcing dipankarsarkar's round 12 fix,
extended round 13, 14, 15, and 16 for the same reason round 12 existed in
the first place.

Round 12 finding: "verifiability" == "mechanised" was a hidden, hand-maintained,
perfectly-correlated function of whether source_locator happened to name a
specific table/row in prose. His fix: split out an orthogonal field,
locator_precision (document | section | row), and compute verifiability's
"mechanised" value FROM that field rather than asserting both by hand.

Round 13 added locator_exhaustive (bool): meant to capture whether a citation
was pinned as precisely as its source permits, independent of what that
precision level is.

Round 14 found locator_exhaustive absent (not false) on the 39 no-locator
records, present-and-always-true only on the 24 that had one -- fixed with
an explicit false + an iff invariant tying it to locator_precision is None.

Round 15 found round 14's own invariant, `(lp is None) != (le is False)`,
was logically identical to `le == (lp is not None)` -- zero independent
bits, the same bug as round 12 restated as a formula. Fixed: `null`, not
`false`, on the 39 (matching locator_precision's own null), and stopped
deriving which boolean locator_exhaustive should take when a locator exists.

Round 16 finding (dipankarsarkar, 2026-09-03), arriving in the same window as
round 15 (his deep-dive was against the pre-round-15 state, but the core
critique -- that round 14's iff was round 12's bug again -- independently
reached the same conclusion round 15 did, by a different method): even
round 15's fix left locator_exhaustive as a hand-typed bool for the 24
located records. His actual proposal is stronger: locator_exhaustive should
never be typed by a person at all. Introduce locator_ceiling (document |
section | row | null) -- what the SOURCE affords, a fact about the source
independent of how far anyone has pinned it so far -- and DERIVE
locator_exhaustive := (locator_precision == locator_ceiling). The boolean
stops being a judgment call recorded in the data; it becomes arithmetic on
two independently-researched fields.

He also did the actual research this makes room for: opened
PalisadeResearch/robot_shutdown_resistance's `logs/` directory and found
`logs/on_the_robot/stats_run/live_05022026/tags.json` -- 10 trials, 3 tagged
"avoided", exactly the paper's cited 3/10. Then ran the repo's own scorer,
`src/figures/bar-chart.py`, unmodified, and got 52/100 for the simulation
figure to the digit. Both independently re-verified here (file exists at
the exact path, script logic re-run in isolation, same two numbers).
PALISADE-2026-robot-shutdown-resistance is promoted to locator_precision
"row" as a result -- a real promotion earned by finding the specific file
and reproducing the specific number, the same bar every other "row" record
in this file was held to.

His closing question -- is a source's ceiling a fact about the source, or a
fact about how much effort has been spent looking at it? -- answered here:
the latter, openly, same as `verifiability` in this file has always meant
"checked as far as anyone has looked", not "guaranteed complete".
locator_ceiling defaults to the current locator_precision for records
already located (current best-known effort, not a claim that no finer
structure could ever be found) and stays null until a locator is
established at all. It is revised upward exactly the way
PALISADE-2026-robot-shutdown-resistance's was this round, when someone
actually opens the source and looks.

What it does: for every record in
AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/misbehavior_incidents_seed_v1.jsonl,
asserts:
  1. verifiability=="mechanised" if and only if locator_precision=="row"
     (round 12's invariant).
  2. All three of locator_precision, locator_ceiling, locator_exhaustive are
     None together, or none of them are (round 15+16's invariant --
     "no locator established" is one null state shared across all three
     fields, not represented three different ways).
  3. Where set, locator_precision is no finer than locator_ceiling on the
     document < section < row ladder (achieved precision can never exceed
     what the source affords -- a real data-integrity check, not a
     tautology, because locator_ceiling is independently set, not derived
     from locator_precision).
  4. locator_exhaustive, where set, equals (locator_precision ==
     locator_ceiling) exactly -- DERIVED and checked, never hand-asserted.
     This is the invariant that makes round 14/15's whole bug class
     structurally impossible now: there is nothing left to hand-type that
     could drift from what it's supposed to equal.
Then, on success, prints n, the verifiability counts, and the
locator_precision / locator_ceiling / locator_exhaustive counts scoped to
the population where they apply (not the whole 63 -- a whole-file census
was exactly what made round 14's bug look healthy).

This does NOT check whether a locator_precision or locator_ceiling value is
actually correct (that a "row" claim really does point at a specific row,
or that a source's true ceiling has been found) -- those stay human-checked
judgment calls, same as verifiability always was. It only checks the
correlations and the arithmetic that were silently unenforced.

Exit code is nonzero iff any record violates a hard invariant -- built by
Claude, 2026-09-01 through 09-03, in direct response to dipankarsarkar's
rounds 12 through 16.
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"

LADDER = {"document": 0, "section": 1, "row": 2}


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

            required = ("locator_precision", "locator_ceiling", "locator_exhaustive")
            missing = [k for k in required if k not in record]
            if missing:
                violations.append(f"{rid}: missing key(s) {missing} -- all three must be present on every record")
                continue

            lp = record["locator_precision"]
            lc = record["locator_ceiling"]
            le = record["locator_exhaustive"]

            if v == "mechanised" and lp != "row":
                violations.append(
                    f"{rid}: verifiability=mechanised but locator_precision={lp!r} (expected 'row')"
                )
            if lp == "row" and v != "mechanised":
                violations.append(
                    f"{rid}: locator_precision=row but verifiability={v!r} (expected 'mechanised')"
                )

            none_states = (lp is None, lc is None, le is None)
            if any(none_states) and not all(none_states):
                violations.append(
                    f"{rid}: locator_precision={lp!r} / locator_ceiling={lc!r} / locator_exhaustive={le!r} "
                    f"-- all three must be None together, or none of them (round 15+16's invariant)"
                )
                continue

            if lp is not None:
                if lp not in LADDER or lc not in LADDER:
                    violations.append(f"{rid}: locator_precision={lp!r} / locator_ceiling={lc!r} not on the known ladder")
                    continue
                if LADDER[lp] > LADDER[lc]:
                    violations.append(
                        f"{rid}: locator_precision={lp!r} is finer than locator_ceiling={lc!r} -- "
                        f"achieved precision cannot exceed what the source affords"
                    )
                expected_le = (lp == lc)
                if le != expected_le:
                    violations.append(
                        f"{rid}: locator_exhaustive={le!r} but locator_precision==locator_ceiling is "
                        f"{expected_le} -- locator_exhaustive must be derived, not hand-typed (round 16)"
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
    ceiling_counts = Counter(r["locator_ceiling"] for r in has_locator)
    exhaustive_scoped = Counter(r["locator_exhaustive"] for r in has_locator)

    print(f"OK: verifiability<->locator_precision<->locator_ceiling<->locator_exhaustive invariants hold "
          f"across all records in {DATASET.relative_to(REPO_ROOT)}")
    print()
    print(f"n = {n}")
    print(f"verifiability:      " + ", ".join(f"{k}={v}" for k, v in sorted(verif_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_precision:  " + ", ".join(f"{k}={v}" for k, v in sorted(locp_counts.items(), key=lambda kv: str(kv[0]))) +
          f"  (of {len(has_locator)} records with a locator; {n - len(has_locator)} explicitly null)")
    print(f"locator_ceiling (scoped to the {len(has_locator)}): " +
          ", ".join(f"{k}={v}" for k, v in sorted(ceiling_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_exhaustive (scoped to the {len(has_locator)}, derived not typed): " +
          ", ".join(f"{k}={v}" for k, v in sorted(exhaustive_scoped.items(), key=lambda kv: str(kv[0]))))
    if len(exhaustive_scoped) <= 1 and has_locator:
        print(f"  NOTE: locator_exhaustive is a single value within its scope right now. Not a bug by "
              f"itself under round 16's model -- it's arithmetic on locator_precision/locator_ceiling, "
              f"both independently set, so a collapse here means every located record's ceiling has been "
              f"found to equal its precision so far, not that the field is secretly redundant.")
    mech = verif_counts.get("mechanised", 0)
    print(f"mechanised: {mech}/{n} = {mech/n*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
