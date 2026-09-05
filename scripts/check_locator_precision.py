#!/usr/bin/env python3
"""check_locator_precision.py -- enforcing dipankarsarkar's round 12 fix,
extended round 13, 14, 15, 16, 17, 18, 20, and 21 for the same reason round
12 existed in the first place.

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

Round 17 (dipankarsarkar, 2026-09-04): round 16 gave locator_ceiling a
value for the first time, but LADDER topped out at "row" -- so any record
whose precision reached "row" had its ceiling FORCED to "row" too (invariant
3 permits no coarser value, and none finer existed), making
locator_exhaustive True by construction for all 18 such records, not by
verification. Re-verified against the live checker rather than argued:
lowering a row record's ceiling below row fails invariant 3, hand-typing
locator_exhaustive=False on an unmoved row/row pair fails the round-16
derivation check, and a ceiling value off the ladder fails outright -- there
was no legal way to make a row record non-exhaustive. He asked the real
question this makes room for: is that because "row" genuinely is every one
of these sources' bottom, or because the ladder itself has no rung below it
to fail?

Checked per-record rather than assumed either way: of the 18 row-precision
citations, 17 point at a specific row (or row+column) of a printed arXiv
table -- a PDF table has no finer machine-addressable unit than the cell a
paper actually prints, so "row" is these citations' genuine, independently
verified bottom, not an artifact of the ladder stopping there. The 18th,
PALISADE-2026-robot-shutdown-resistance, cites logs/.../tags.json directly --
opened it (commit dcc38ab, same as round 16): a flat dict of 20 keys (10
real trials + 10 _debug twins), each value a LIST of tags, not a scalar.
3 of the 10 real trials carry TWO tags at once (avoided AND finished, not
avoided alone) -- real sub-row structure, not hypothetical. Added "field" as
LADDER's first rung above "row", reachable only where the source itself is
structured data with addressable sub-record fields (right now: this one
record). Promoted PALISADE-2026-robot-shutdown-resistance to
locator_precision=locator_ceiling="field" -- earned by opening the source
and finding the field, the same bar every "row" promotion in this file has
been held to, not asserted to unstick the invariant. The other 17 stay at
row/row: verified as a real ceiling, not upgraded to match a rung that
doesn't apply to a printed table. Round 12's mechanised<->row invariant is
generalized from an exact match against "row" to ">= row on the ladder",
since a field-precision citation is strictly more pinned than a row-precision
one and must satisfy the same requirement, not be exempted by a literal
string comparison that predates "field" existing.

Round 18 (dipankarsarkar, 2026-09-04): two findings against round 17's own
work, both re-verified here before touching anything.

First: round 17 moved the pin, it did not remove it. LADDER's new top,
"field", forces the same chain round 16 forced at "row" -- lp="field" is the
max, so invariant 3 forces lc="field", invariant 4 forces le=True, and all
three of his round-16 escape probes fail identically when re-run against the
one record that reached it. His diagnosis: doing the research is what moves
a record to the finest rung it can reach; the finest rung is the ladder top;
the ladder top is where le is forced True -- so this field goes structurally
quiet on exactly the records that got the most work, every round, by
construction. Genuine progress alongside it, also re-verified: the pinned
(structurally-unfalsifiable) population went from 18 records to 1, and the
other 17 really did become falsifiable (tested: lowering any of their
ceilings to field with le=False now exits 0, not 1). Two rounds of real
reduction, and a live structural limit neither one removed.

Second, sharper: round 17's own claim that "field" is "reachable only where
the source is structured data with addressable sub-record fields" was prose
in this docstring, not a check in this code. Demonstrated, not argued:
promoting BERKELEY-2026-peer-preservation -- a printed PDF table citation --
to locator_precision=locator_ceiling="field" passed the (round 17) checker
cleanly, exit 0. The exact shape round 12 removed from `verifiability` (an
unenforced, hand-maintained correlation) had grown back one rung up. He also
found the "row" label undersold several records' actual state: 6 of the 17
row-precision source_locators never use the word "row" at all, 3 of those
cite only Figures (one saying outright "the paper has no numbered tables,
only numbered Figures" -- confirmed verbatim), and 4 (BERKELEY plus three
APOLLO/PALISADE contrast records) already name a specific table CELL
(row + column), which by the file's own promotion bar -- open the source,
find the thing -- means their true ceiling is finer than "row", not equal to
it, and their locator_exhaustive=True is arguably wrong today.

Fixed here, narrowly: added a fourth required field, source_structured
(bool, None only where the other three are also None), set once per record
as a verified, non-self-asserted fact -- True only for
PALISADE-2026-robot-shutdown-resistance (tags.json, opened and confirmed
structured), False for every other located record. The checker now refuses
"field" on either locator_precision or locator_ceiling unless
source_structured is True on that exact record -- re-running his BERKELEY
promotion against this version fails outright, citing the missing flag.

NOT fixed here, and said plainly rather than rushed: the 4 cell-level
citations and his closing question -- whether to keep extending a shared,
ordinal, finite ladder (which will always have a top, and will therefore
always eventually re-pin whichever record reaches it) versus deriving
locator_ceiling from each source directly, scoped per source rather than
per record, with no shared top to reach -- is a real architectural fork, not
a one-line patch. Adding a "cell" rung under "field" would flip those 4 to
False today and pin PALISADE-2026-robot-shutdown-resistance's field record
tomorrow, the identical move round 17 made one rung up; it would not be a
different kind of fix, just a smaller instance of the same one. Doing that
again without first deciding whether the ladder itself is the right shape
is exactly the failure mode this file's history (12 through 18) has been
finding new forms of. Left open for round 19, not patched over.

Round 20 (dipankarsarkar, 2026-09-05): answered the round-18 fork by proving
it was never live. Re-pulled the seed at commit 1578ca2 (sha256 confirmed:
ca4c71db...) and read locator_ceiling as a column across every revision it
has existed in -- 8229f49, b137ec4, 1578ca2. In all three, across all 25
located records each time (75 record-revisions total), locator_ceiling has
never once held a value different from locator_precision, and
locator_exhaustive has never once been anything but True. This docstring
already said why, in plain prose, several rounds ago: "locator_ceiling
defaults to the current locator_precision for records already located."
Both PALISADE promotions (round 16 to row, round 17 to field) moved both
fields in the same commit -- no ceiling has ever been set by a process that
could not also see, and match, the precision. Invariant 4's arithmetic
(le = lp == lc) has been computing on two fields that have never once
disagreed.

He sharpened round 18's "4 undersold cell citations" finding to 6, and
proved it from the same strings already in this file rather than opening
anything new: four records citing arXiv:2412.16720's Table 10 name a row
plus a model-specific value (a cell) -- two say the word "column" (caught
by round 18's lexical scan), two don't (missed by a scan for a word, not a
unit) but cite the identical shape, row name paired with one model's
number. Verified directly against the records' own source_locator strings,
not taken on his word: all six (BERKELEY-2026-peer-preservation, both
gpt4o-CONTRAST records, the PALISADE shutdown-compliance-CONTRAST record,
and the two o1 System Card records) already state a specific row-plus-value
pairing in their own prose -- a cell, under either his claim-scoped or
source-scoped reading, and he said so plainly: "both readings agree those 6
are wrong at row right now."

Fixed: added "cell" to LADDER, between row and field. Promoted all six to
locator_precision=locator_ceiling="cell" -- earned by their own already-
existing prose, not asserted to close the gap; source_structured is
untouched (that gate is specific to "field", not "cell", and none of these
six sources are JSON-shaped).

Said plainly, not smoothed over: this fixes the six records his find named,
and nothing else. locator_exhaustive is still True on literally every
located record in this file's history -- 25 of 25, unchanged by this round --
because no promotion, this round included, has ever moved precision and
ceiling apart. His closing question stands exactly as he left it: is the
fix a new rung every few rounds, or is locator_ceiling one field wearing
two names alongside locator_precision? Adding "cell" answered "are these
six mislabeled" with yes, verified. It did not answer his harder question,
and pretending otherwise would be the same move rounds 16 and 17 made one
level down. Left open for round 21.

Round 21 (dipankarsarkar, 2026-09-05, same day): corrected his own round-20
overcount first -- re-read all 7 flagged strings and confirmed only 2 name a
finer unit directly, 1 is borderline, 4 explicitly deny one exists; also
confirmed his Claude-4-card table count was wrong (20 distinct IDs, not 15,
matching what was independently counted here). Then found something the
overcount was distracting from: instead of re-reading strings, he opened
the two "document"-precision records' actual sources -- the only two
document-precision records in the whole file -- and falsified both.

ANTHROPIC-2026-prototype-stopped-CONTRAST claimed the Anthropic blog post
"covers all three models... in one disclosure... finest addressable unit is
the post itself." Fetched the live page: h2 "What happened" contains three
separately anchored h3 subsections, id="incident-1"/"incident-2"/
"incident-3", one per model. Incident 3's text is this record verbatim
(9,000 targets, credentials off an exposed debug page, SQL injection, "On
its own, it concluded that the target was in fact real, and ceased its
attack"). The record's own two sibling incidents in this file
(ANTHROPIC-2026-opus47-sandbox-ignore, ANTHROPIC-2026-mythos5-self-deceived,
both still fully unlocated) map onto Incident 1 and Incident 2 exactly. The
post does not fuse three models into one disclosure; it names one anchor
per model, and this record already had the anchor sitting in its own
citation.

GOOGLE-2025-gemini-echoleak-class-blocked-CONTRAST claimed "blog post, no
page/table" -- true about pages and tables, false about structure. Fetched
the live page: h3 "A layered security approach" (data-block-key="a2sal")
holds a 5-item enumerated list of Gemini defenses, and the sentence this
record quotes is item 3, "Markdown sanitization and suspicious URL
redaction," verbatim.

His sharper point, and it's correct: unlike round 20's six cell citations
-- which were only False under the source-scoped reading, which is why they
waited for the fork -- these two are False under the claim-scoped reading
too. The finer unit isn't proven by a sibling record on the same source; it
contains the cited claim and nothing else, found by opening this record's
own citation. Neither reading of the still-open round-20 question changes
the verdict, so this didn't need to wait for round 20 to resolve first. He
re-checked the file's other two "denies a finer unit" records the same way
(opening the Anthropic multiagent-systems post's "Incompatible goals"
section, and Claude 4 card pages 26-27 directly) and both held up -- no
sub-headings, no tables, prose the whole way down. Re-verified independently
here before touching anything: both fetches confirmed live, both promotions
correct.

Fixed: ANTHROPIC-2026-prototype-stopped-CONTRAST promoted document -> section
(the anchored h3 subsection, no finer structure exists within it).
GOOGLE-2025-gemini-echoleak-class-blocked-CONTRAST promoted document -> row
(the enumerated list position), which also flips its verifiability from
human-checked to mechanised under this file's own round-12 invariant,
generalized round 17 to any rung at or finer than row regardless of medium
-- a numbered list item earns the same classification a table row does, by
the same rule already governing every other record in this file, not a
one-off exception written to fit these two.

document is now empty in this file -- zero records claim "the whole source,
undifferentiated" is the finest unit available. That was never a rung this
file's citations actually needed; it was, as he put it, what got written
down before anyone looked for the headings.

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
Claude, 2026-09-01 through 09-05, in direct response to dipankarsarkar's
rounds 12 through 18, 20, and 21.
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"

# Round 17 added "field", the first rung above "row" this ladder has ever had.
# It is reachable only where the underlying SOURCE is structured data (JSON/CSV)
# with real, independently-addressable sub-record fields -- not a blanket
# upgrade. A printed PDF table has no finer machine-addressable unit than the
# row/cell a paper actually prints, so "row" stays the genuine, non-null
# ceiling for every citation whose source is a paper table (17 of the 18
# row-precision records as of round 17). "field" exists for the one record
# whose source is raw structured data with real sub-row fields, verified by
# opening that source and finding the field, same bar as every other
# precision claim in this file -- see round 17 in this docstring below.
LADDER = {"document": 0, "section": 1, "row": 2, "cell": 3, "field": 4}


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

            required = ("locator_precision", "locator_ceiling", "locator_exhaustive", "source_structured")
            missing = [k for k in required if k not in record]
            if missing:
                violations.append(f"{rid}: missing key(s) {missing} -- all four must be present on every record")
                continue

            lp = record["locator_precision"]
            lc = record["locator_ceiling"]
            le = record["locator_exhaustive"]
            ss = record["source_structured"]

            # Round 12's invariant, generalized for round 17's "field" rung: mechanised
            # means "pinned at least to a specific row" (row or finer), not "pinned to
            # exactly row" -- a field-precision citation is strictly more pinned than a
            # row-precision one, so it must satisfy the same mechanised requirement, not
            # be exempted from it by failing a literal string match against "row".
            at_least_row = lp in LADDER and LADDER[lp] >= LADDER["row"]
            if v == "mechanised" and not at_least_row:
                violations.append(
                    f"{rid}: verifiability=mechanised but locator_precision={lp!r} (expected 'row' or finer)"
                )
            if at_least_row and v != "mechanised":
                violations.append(
                    f"{rid}: locator_precision={lp!r} (row or finer) but verifiability={v!r} (expected 'mechanised')"
                )

            none_states = (lp is None, lc is None, le is None, ss is None)
            if any(none_states) and not all(none_states):
                violations.append(
                    f"{rid}: locator_precision={lp!r} / locator_ceiling={lc!r} / locator_exhaustive={le!r} / "
                    f"source_structured={ss!r} -- all four must be None together, or none of them "
                    f"(round 15+16's invariant, extended round 18)"
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
                # Round 18 (dipankarsarkar): the round-17 docstring claimed "field" is
                # "reachable only where the source is structured data with addressable
                # sub-record fields" -- prose the checker never enforced. Demonstrated
                # live: promoting BERKELEY-2026-peer-preservation (a printed PDF table)
                # to precision=ceiling="field" passed cleanly, exit 0. The rule round 12
                # took out of `verifiability` (a hand-maintained correlation the checker
                # didn't verify) had grown back one level up. source_structured makes it
                # a checked fact instead of a comment: "field" on either lp or lc now
                # requires source_structured is True on that record, and that flag isn't
                # self-asserted at the point of use -- it's a permanent, auditable
                # property set once, only True for the one record whose source (tags.json)
                # was actually opened and found to have addressable sub-record fields.
                if (lp == "field" or lc == "field") and ss is not True:
                    violations.append(
                        f"{rid}: locator_precision={lp!r} / locator_ceiling={lc!r} reaches 'field' but "
                        f"source_structured={ss!r} -- 'field' requires a verified structured-data source "
                        f"(round 18: this was prose, not enforced, until now)"
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
