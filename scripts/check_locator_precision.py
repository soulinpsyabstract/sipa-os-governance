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

Round 22 (dipankarsarkar, 2026-09-05, same day): demonstrated the exact
forgery round 18 said source_structured would prevent, against the file as
it stood after round 20 added "cell". Hand-set
BERKELEY-2026-peer-preservation's locator_precision=locator_ceiling="field"
and source_structured=True -- its actual source is a printed PDF table
(arXiv:2604.19784v3, Table 3), the opposite of the "JSON with addressable
sub-record fields" bar round 17 set for "field". Re-ran the forgery here,
independently, on a scratch copy, never touching the tracked file: exit 0,
"OK: invariants hold". His diagnosis is exactly right and it is in this
docstring's own words from round 18 -- source_structured was described as
"a permanent, auditable property set once", which is a claim about
provenance, not something the checker was ever asked to verify. Nothing
reads the field except to confirm it is not None (or, at the field rung,
that it is True). It is a hand-typed boolean wearing the same costume
locator_exhaustive wore before round 16.

His fix is the same move round 16 made one field over: stop typing
source_structured by hand and derive it. He specified the derivation from
strings already shipped in this file, over both fields that exist on every
record regardless of whether it has a locator yet -- citation names a
repository host (github.com/gitlab.com/bitbucket.org/a huggingface.co
dataset-or-file URL), and source_locator names a path with a
machine-readable extension (.json/.jsonl/.csv/.tsv/.yaml/.yml/.py). Ran his
derivation here independently, written from his English description before
looking at any code he might have, against all 63 records: agree=63,
disagree=0 against the file's current hand-typed values, including the one
True (PALISADE-2026-robot-shutdown-resistance, tags.json) and the 24 False
located records, and the same two he named as forced-None under the old
four-together rule (MONARCH-2026-dismech-agent-scope-overreach,
OPENCODE-2026-orchestrator-silent-fallback -- both cite a repo host, both
have source_locator=None because no one has opened the issue thread and
pinned a file yet).

Fixed: source_structured is no longer typed. It is computed by
derive_source_structured(citation, source_locator) and the checker now
asserts the stored value equals the derived one -- a violation, not a
silent pass, if they ever disagree. Re-ran the BERKELEY forgery against
this version: FAIL, "source_structured=True but derived from
citation+source_locator is False". The field also left the three-way
None-together invariant (locator_precision / locator_ceiling /
locator_exhaustive stay None together; source_structured does not need a
locator to exist, because structuredness is a fact about the citation and
source_locator strings, not about how far anyone has pinned a location
within them). Checked every one of the 63 records against the unconditional
derivation, not just the 25 located ones: all 38 unlocated records have
source_locator=None, so all 38 derive to False, not None -- a real,
mechanical change to the dataset (source_structured: null -> false on all
38), not a checker-only patch. None of the 25 located records' stored
values needed to change; the derivation already agreed with all of them.

Said plainly: this closes the exact hole he demonstrated, and it is a
narrower fix than his closing architectural question asks for. He asked
what it would take to trust a derived flag over a set-once one twice --
verified out-of-sample against six records the derivation's author (him)
had not seen when he wrote it, which is a stronger form of evidence than
this round produced. This round's agreement (63/63) was checked against
data that already existed when the rule was written, not held out from it.
That is a real difference in evidentiary weight, said here rather than
left for him to point out a second time.

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

Round 23 (dipankarsarkar, 2026-09-06): three findings against round 22, all
re-verified here independently before touching anything.

First: round 22's docstring claimed citation and source_locator are "both
present on every record in the file." False, checked directly against all
63 records: source_locator is absent as a KEY (not present-and-null) on 38
of them, including the same two named in round 22 as the mechanism's proof
case (MONARCH-2026-dismech-agent-scope-overreach,
OPENCODE-2026-orchestrator-silent-fallback). derive_source_structured()
reads both fields with record.get(), which returns None on a missing key
indistinguishable from an explicit null -- the same failure shape as the
except-Exception-return -1 bug fixed elsewhere the same night in
SYNTAX_AUDITOR.py's count_403_relay(): two different states (never
recorded / recorded-and-empty) collapsed into one value. Harmless here only
because derive_source_structured() already treats both the same way on
purpose (no locator at all and an empty locator both mean "not
structured") -- but the docstring's factual claim about the data was wrong
regardless of whether the bug it enabled was harmless, and is corrected
below.

Second: round 22's "63/63 agreement" oversold its own evidentiary weight.
Constant-False -- predict every record's source_structured is False, no
computation at all -- already scores 62/63 (98.4%), since exactly one
record (PALISADE-2026-robot-shutdown-resistance) is True. The derivation's
real information content is one record, not sixty-three. Worse: condition
A (repo host in citation) contributes nothing measurable once condition B
is applied -- B alone (machine-readable extension found anywhere in
source_locator) reproduces the stored value on all 63 records by itself,
with or without A. All three numbers re-run here independently: baseline
62/63, B-alone 63/63, A-and-B 63/63 -- A is along for the ride, not doing
work.

Third, the actual bug: B searches the ENTIRE source_locator string, not
only the part that names the source.
PALISADE-2026-robot-shutdown-resistance's source_locator is 422 characters
-- the genuine path followed by round 16-18's own annotation prose about
how that path was verified -- and contains six file-extension-shaped
substrings across the whole string: the real logs/.../tags.json, plus
src/figures/bar-chart.py (the scorer script, not a data source), tags.json
again, and three .jsonl log filenames, five of the six appearing only after
the first "--". It still lands on True today only because the genuine path
also happens to sit in the untouched head, before any delimiter. A record
whose real path came second, after prose that happened to mention an
unrelated filename first, would currently pass on the strength of that
incidental mention rather than on its actual citation. Checked across all
25 located records: source_locator mean length 422 characters, 23 of 25
longer than 120 characters -- most of this field is prose, not path, by
volume.

His fix, applied here verbatim: anchor the extension search to the head of
source_locator, everything before the first ";" or "--", not the whole
string. Re-ran against all 63 records with the anchored version: agreement
unchanged, 63/63 -- none of the 25 located records name their real file
only in the tail, so nothing that was correctly derived becomes wrong.
What changes is what the check actually verifies: a citation naming its
source in the part meant to name it, not a match anywhere prose happens to
mention a filename.

He also retracted his own round-19 claim in this same message: round 19's
out-of-sample test (six records he had not seen when writing the rule) had
no discriminating power either, for the same reason as this round's
baseline point -- when the overwhelming majority of any sample shares one
label, passing an out-of-sample check mostly confirms the majority class,
not the rule being tested.

Fixed: the machine-readable-extension regex now searches only
re.split(r";|--", source_locator, maxsplit=1)[0] -- the head, not the
full string. Docstring's false "both present on every record" claim is
corrected above to state the true split (25 present, 38 absent as a key).
His closing question -- does source_locator split into a path and a note
structurally, or does the regex learn where the path ends -- is answered
here the second way, same register as round 17's answer to a similar
question about locator_ceiling: nothing in this dataset currently needs a
real path/note structural split, so this round doesn't add schema the data
doesn't yet justify. If a future source_locator ever puts its real path
after a mention of an unrelated file, this anchoring stops being enough,
and the honest fix at that point is the structural split, not a smarter
regex.

Round 24 (dipankarsarkar, 2026-09-06, same day): a real data finding, not a
checker bug -- the first record this file has ever had where
locator_precision is genuinely below locator_ceiling.

APOLLO-2024-self-exfiltration and APOLLO-2024-oversight-subversion cite
arXiv:2412.04984v2, Table 1, pinned to one row each ("row 'Self-
Exfiltration'", "row 'Oversight Subversion'") -- precision=ceiling="row"
both, same as every other row-precision record. But two CONTRAST records
already in this file cite the SAME Table 1 and describe it in their own
prose as a per-model grid: APOLLO-OPENAI-2024-gpt4o-no-self-exfiltration-
CONTRAST calls it "Table 1 (p.6, per-model X/check scheming matrix)",
APOLLO-OPENAI-2024-gpt4o-no-oversight-subversion-CONTRAST calls it "Table 1
(p.6, per-model scheming matrix, gpt-4o = X across all behaviors)" -- both
already promoted to locator_precision=locator_ceiling="cell", because they
pin one specific model's column, not just a behavior's row. Same table,
independently documented in this file as affording a model dimension the
two plain APOLLO records never pinned. Their genuine ceiling is "cell";
their achieved precision stayed at "row". Checked APOLLO-2024-sandbagging
for the same promotion and did not apply it: unlike the other two, its
source_locator spans Table 1, Section 3, and Table 5 at once -- not a
clean single-table citation, so "what this citation's ceiling is" isn't
the same well-formed question there.

Re-ran his scratch test independently before touching the tracked file:
locator_ceiling="cell" with locator_precision="row" unchanged, and
locator_exhaustive set to what round 16's derivation computes (False, not
hand-typed) -- exit 0, locator_ceiling scoped counts cell=8/field=1/row=10/
section=6, locator_exhaustive False=2/True=23. Negative control confirmed
too: same two fields, locator_exhaustive hand-typed True instead of
derived -- exit 1, both records flagged by name, the exact round-16
invariant this docstring has described since round 16. Applied to the
tracked file: locator_ceiling "row"->"cell" and locator_exhaustive
true->false on both records, nothing else touched.

His sharper point, checked against full git history before accepting it:
locator_ceiling has been "independently settable" (a field of its own,
distinct from locator_precision) since round 16, but never once
independently SET. Walked every commit that touched this dataset file (34
total) and diffed locator_ceiling against locator_precision at each write:
every ceiling-set event either came from round 16's one-time bulk backfill
(defaulting ceiling to the record's then-current precision, explicitly
documented as that -- not independent) or from a later round promoting
precision and ceiling together in the same commit (round 17's "field" rung,
round 20's "cell" rung). Zero events, across the whole history, where
ceiling was set to something other than the record's own precision. His
framing: a field that agrees with another field on every one of 75 write
events, when only one thing has ever assigned it, isn't evidence the two
fields are the same -- it's evidence nothing has tested whether they
could differ. That test is exactly what this round performs, for the
first time, on two records found by cross-referencing this file's own
prose against itself.

His closing question -- is locator_ceiling derivable from citation and
source_locator the way source_structured was, or does it genuinely require
opening the source and checking what ISN'T there -- gets an honest partial
answer, not a formula. The method that found this round's two promotions
(reading one record's citation prose describing a table's shape, then
checking whether ANOTHER record cites the identical table) used only
strings already in this file, the same ingredients round 22's derivation
used. But it required matching a shared source across two records and
reading what each one's prose says about that source's structure -- not a
regex over one record in isolation, and not obviously generalizable: it
worked here because two CONTRAST records happened to describe the same
Table 1 explicitly enough to say what it affords. A source cited only
once, or described without naming its structure, gives this method nothing
to work from. Round 16-18 answered a structurally similar question about
locator_ceiling itself ("is a source's ceiling a fact about the source, or
about how much effort has been spent looking at it?") by saying: the
latter, openly, revised upward exactly when someone opens the source and
looks. Nothing in this round changes that answer. What changes is that
"looking" now sometimes means checking this file's own other citations
before touching the source at all -- a real technique, not a new field and
not a claim that ceiling is now mechanically derivable in general.

Round 25 (dipankarsarkar, 2026-09-06, same day): the one located record
this file has ever marked unverifiable, and the citation's own claim about
it was wrong.

ANTHROPIC-2026-multiagent-turf-war cited its 98% Mythos-5-truce-rate figure
as confirmed "verbatim" in the blog post's section text, at locator_precision
"section", while marking verifiability "unverifiable" -- a located record
saying it could not be checked. Fetched the live page independently before
touching anything: HTTP 200, 217,949 bytes, matching his count exactly.
"98%" appears exactly twice in what the server sends, in neither case as
part of the section's rendered prose: once as an <img alt="..."> string,
once as the description field of that same image object in the page's
content JSON. The caption a reader actually sees says something else
entirely ("Across n=120 episodes per model, what proportion are settled by
force, passivity, truce, or not settled"), no percentage in it. The
section's own visible text was never carrying this number; the citation's
"confirms ... verbatim" claim was false.

Reproduced his three-way test on the current data before changing anything:
verifiability="human-checked" passes, "unverifiable" (the shipped value)
also passes, "mechanised" fails round 12's own invariant (section is not
row-or-finer). Two of three pass, and the file's one check for this record
had nothing that ruled out the wrong one of those two.

Fixed two things. First, a new invariant: locator_precision is not None
implies verifiability != "unverifiable" -- naming a specific location in a
source and then saying that source can't be checked is a direct
self-contradiction, independent of what precision rung the location sits
at. Flags exactly the one record this applies to on the current 63.
Second, the record itself: verifiability "unverifiable" -> "human-checked"
(a human -- him, then independently this session -- actually opened the
page and found where the number lives; it just isn't a mechanised
row-or-finer citation in this file's existing sense, since it wasn't taken
from the section's own addressable prose), and source_locator's text
corrected to describe what is actually true -- the figure lives in a
non-rendered image-description field, not the section's rendered content
-- instead of repeating the false "verbatim" claim. locator_precision
stays "section": the visible section still anchors the claim's context,
and this round does not decide whether a JSON object's named field
constitutes a finer addressable unit the way round 17's "field" rung did
for structured data files -- he raised that possibility and declined to
take it without confirmation, and this round leaves it declined for the
same reason.

His closing question -- is "finest addressable unit" a property of the
rendered page or of the payload the server hands you -- gets the same
answer round 16 already gave a structurally identical question about
locator_ceiling: the latter, openly. verifiability in this file has never
meant "visible to a reader"; it has meant "checked as far as anyone has
looked," and the payload is what an actual check reaches, not what a
browser chooses to paint. That principle already answers why this record
is human-checked now rather than still unverifiable. It does not by
itself answer whether the description field should be a new locator
rung -- that is a question about this file's ladder, not about where
verification happens, and stays open.

Round 26 (dipankarsarkar, 2026-09-08): round 25's anchor -- split on ";" or
"--" -- was itself only partly anchored, and the metric used to check it
(63/63 agreement) could not have caught that, because agreement never
distinguishes a well-sized anchor from a no-op one on this data: only
PALISADE-2026-robot-shutdown-resistance ever derives True, so any anchor
that leaves PALISADE's real path in the head scores 63/63, including no
anchor at all. He compared four candidate splits against a second metric --
how many of the 25 located records the anchor actually cuts, i.e. how many
have a head strictly shorter than the full string -- and that column, not
agreement, is what separates a real anchor from a decorative one:

  split rule              agreement    head == whole string
  ;|--   (round 23)         63/63          7 of 25
  ;|,|--  (proposed)         63/63          0 of 25
  ;|--|. (period+space)      63/63          2 of 25
  none at all (round 22)     63/63         25 of 25

Reproduced independently before touching anything: exact match on both
columns, all four rows. The 7 records where round 23's anchor was a no-op
share one shape -- comma-and-period prose citations with no ";" or "--" at
all ("arXiv:2412.04984v2, Table 1, row 'Oversight Subversion'"; "arXiv:...,
p.5, Section 3.2 item 4 (...)"). Checked across all 25 located records:
every one contains a comma; only 18 contain ";" or "--". Round 23's anchor
was never sized to this file's actual citation style -- it was sized to the
one record (PALISADE) that motivated writing it, which happens to use "--".

This mattered for a reason beyond these 7: MONARCH-2026-dismech-agent-
scope-overreach and OPENCODE-2026-orchestrator-silent-fallback -- the two
repo-host records still waiting on a real source_locator, named as a held-
out prediction test in round 23 -- are exactly the kind of record likely to
get a comma-and-period locator when someone writes one ("issue #1800,
comment 14, the maintainer's reply naming the scope check"), not a ";"- or
"--"-delimited one. Round 23's anchor would have been inert on that string
the moment it was written, reopening the round-22 hole on precisely the two
records the prediction was about -- verified here by constructing that
exact shape on a scratch copy and confirming it derives True unanchored,
False anchored.

Fix, applied verbatim: the split pattern is now r";|,|--" instead of
r";|--" -- one more delimiter, chosen because this file's own citations
already use it on 25 of 25, not new schema. Re-verified: 63/63 agreement
unchanged, 0 of 25 now inert, PALISADE still derives True (its real path,
logs/on_the_robot/stats_run/live_05022026/tags.json, sits before the first
comma too -- the comma inside "(commit dcc38ab, 2026-02-11)" comes after
the extension). Checked for the failure mode a wider delimiter could
introduce -- a real file reference that itself contains a comma before the
extension, which a comma-anchor would wrongly cut -- across all 25 located
records: zero records flip derivation between the old and new anchor in
either direction. Re-ran the round-18/22 BERKELEY forgery (still caught)
and the round-23 tail-only-mention case (still passes clean) before
committing.

Round 27 (dipankarsarkar, 2026-09-08): a real data fix, not a checker bug --
and an independent answer to round 24's open question about deriving
locator_ceiling, offered without demanding it settle anything.

ANTHROPIC-2026-opus47-sandbox-ignore and ANTHROPIC-2026-mythos5-self-
deceived were carried as unlocated since round 21, on the assumption their
source lacked the structure their CONTRAST sibling (prototype-stopped)
had already been promoted to "section" against. Wrong assumption: their
citation field named only the Register piece, not the Anthropic primary
post their sibling cites and quotes from. Checked directly, both fetched
live: the Anthropic post's three h3 anchors (incident-1/2/3) render 1,426 /
3,662 / (incident-3 truncated by a crude end-boundary in my own check,
not material here) characters, and every quote each of these two records
carries sits inside its own anchor -- five for five. The Register piece,
fetched separately, is 10,778 rendered characters and contains none of
those five quotes at all; it links the Anthropic post, it does not
reproduce it. The two records were never unlocated because their source
lacked structure -- they were pointed at a document that never contained
what they quote.

Fixed: citation for both now includes the Anthropic primary post (matching
the sibling's citation exactly), source_locator names the correct anchor
(incident-1 for opus47, incident-2 for mythos5) with the verified quotes,
and both promoted to locator_precision=locator_ceiling="section",
locator_exhaustive=true -- the same rung their sibling already holds, on
the same source. The sibling's own source_locator text, which had called
the other two "still unlocated as of this correction," is corrected in
place to reflect that they now are.

Separately, he answered round 24's closing question -- is locator_ceiling
derivable from strings the file already carries, the way source_structured
was -- with a real candidate, offered as exploratory rather than settling
the claim-scoped/source-scoped fork round 24 left open: a record's ceiling
is at least as fine as the finest precision reached by any other record
citing a shared source. Reproduced independently against the round-16
baseline (ceiling defaulting to precision everywhere): this rule alone
flags exactly six records, matching his list exactly -- the same two
APOLLO records promoted in round 24 (row -> cell, found there by comparing
prose descriptions of the same table), APOLLO-2024-sandbagging (row -> cell,
correctly reproduced by the rule but left excluded here, same reasoning as
round 24: its locator spans three sources at once, not a clean single-
source citation), and the two Anthropic records fixed in this round
(None -> section). A sixth, OPENAI-2025-atlas-resignation-email-redteam,
the rule also flags (None -> section, co-citing the same openai.com post
as its own CONTRAST sibling) -- left untouched here. Its source returned
HTTP 403 to a direct fetch, 9,842 bytes of block page, reproduced
independently and identically to what he reported; there is no primary-
source confirmation behind this one yet, only the mechanical rule, and
this file's standard has been to promote on a source actually opened and
checked, not on a formula alone. Marked as a pending, mechanically-flagged
candidate, not applied.

This derivation is not implemented as a new automatic invariant in this
round. It reproduced six real judgment calls, four already made by hand
and confirmed correct, using nothing but citation strings already in the
file -- a genuinely strong result -- but he did not claim it resolves
round 24's fork between "ceiling scoped to a claim" and "ceiling scoped to
a source," and neither does this round. Left as documented, verified,
working evidence toward that question, not as a rule enforced going
forward.

Round 28 (dipankarsarkar, 2026-09-08): round 25 closed one direction --
a located record claiming unverifiable. The other direction was wide open:
36 unlocated records, and verifiability on them had no check at all.

Demonstrated, not argued: swap MONARCH-2026-dismech-agent-scope-overreach
and OPENCODE-2026-orchestrator-silent-fallback's verifiability values --
exit 0. Set either one to the literal string "banana" -- exit 0. Invert
every one of the 36 unlocated records' verifiability at once -- exit 0,
with the summary line printing the inverted distribution and calling it
OK. Round 25's invariant only fires when locator_precision is not None; on
the 36 records with no locator, verifiability was the last fully hand-
typed field in this file, checked against nothing.

He named the tightest pair on purpose: MONARCH and OPENCODE cite the same
kind of source (a numbered GitHub issue), fetched both live and got HTTP
200 on both, near-identical byte counts (303,123 and 276,080 here,
matching his 303,119 and 276,078 within the normal drift of a live
dynamic page) -- "neither is less checkable than the other," his words,
verified rather than taken on trust.

So checked which one was actually right, not which check would catch the
disagreement. Fetched both issues directly. MONARCH's page carries the
real conversation in its own data (both a GitHub GraphQL-shaped JSON island
and the rendered thread): "Apologies on Chris's behalf! The curation-
scanner agent eagerly picked this up and created PR #1803 before you had
a chance to work on it yourself... this was meant to be yours to tackle as
a first dismech entry, and the agent deprived you of that learning
opportunity" -- matches this record's summary exactly. OPENCODE's page
carries its full issue body the same way, both as ld+json articleBody and
rendered HTML: "the harness allowed an invalid subagent routing attempt to
create child-session artifacts without a usable model/stream, and the
parent agent then continued doing work directly" -- matches that record's
summary exactly too. Both genuinely checkable. Only one was marked
human-checked.

Fixed: OPENCODE-2026-orchestrator-silent-fallback verifiability corrected
unverifiable -> human-checked, with a note on the record itself pointing at
what was actually found. This resolves the specific pair he used to
demonstrate the gap. It does not touch the other 35 unlocated records,
each of which still needs the same treatment -- opening the actual source
and checking, one at a time -- before its verifiability value means
anything more than "someone typed a string here."

Added one narrow, unconditional check for the gap itself: verifiability
must be one of mechanised / human-checked / unverifiable, on every record,
located or not. This does not decide which of the two real values applies
to any given unlocated record -- that still requires a human to open the
source, and nothing here shortcuts it. It only removes "banana," and
anything else that was never a real value, from silently passing. Re-ran
the round-25 control (a located record set to unverifiable) and the new
banana case against the fix: both now caught, both correctly.

His closing question -- should "fetched this citation and got HTTP 200"
become a rung verifiability can reach on its own, below section, needing
no locator -- is not taken here. Not because the idea is wrong, but because
it would be a category substitution: HTTP 200 means a URL currently
resolves, not that anyone read what's there or that what's there matches
this record's claims -- exactly the gap that made MONARCH and OPENCODE
swappable with each other and with "banana" in the first place, moved one
layer over instead of closed. It would also make this checker's result
depend on live network state for the first time, on infrastructure already
shown this round to answer 403 to a direct fetch (openai.com, round 27) --
a check that certifies less than "human-checked" already means, while
costing this file its only offline-reproducible property. What actually
closed the gap on this pair was opening both sources and reading them, the
same thing "human-checked" has meant since before this exchange started.
That doesn't scale to a rule by itself, but it's what the field is
supposed to record, and it's what the fix above does for the one pair
demonstrated.

Round 29 (dipankarsarkar, 2026-09-08): reproduced round 28 first -- EXIT 0,
n=63, same distribution he quoted. Then he re-ran the round-24 co-citation
ceiling derivation against today's file instead of the round-16 state.
Reproduced independently with a fresh script: it raises two flags on a naive
run, not the one he reported --
OPENAI-2025-atlas-resignation-email-redteam (ceiling None, co-cited section
via the injection-detected-CONTRAST sibling on the openai.com URL that has
answered 403 since round 27, still 403 today) and APOLLO-2024-sandbagging
(ceiling row, co-cited cell via oversight-subversion on the same Table 1).
The second one isn't a new bug: round 24 already looked at it and left it at
row on purpose, because its record spans both a table cell and prose
mechanism text that a single cell locator can't cover -- the same reason
a record doesn't get promoted just because its citation matches a finer
one. Once that already-adjudicated case is set aside, one flag remains,
matching his count. Of the 36 null-precision records, 31 cite sources no
other record cites (invisible to this method by construction) and 5 are
co-citation-visible; this run flags one of the five. The other four were
already resolved in earlier rounds. That's the bound: co-citation has now
found everything it can find in this file, not "everything so far."

Then he opened a primary source cold on a null/null/null record --
AISI-2026-mythos5-supply-chain-backdoor, citing aisi.gov.uk and
The Hacker News -- and read it for structure rather than running a script.
Fetched it independently: HTTP 200, 41,426 bytes, matching his numbers
exactly. 8 h3 tags in the markup, 7 carrying real section headings ("What
happened" / "How we discovered the incident" / "What we found" / "Why this
happened" / "Lessons for the future" / "What this means for people and
businesses" / "Final reflections"), the 8th a share-widget caption, not
content. None of the 8 carry an id attribute -- confirmed his "zero
anchored headings" claim exactly, this page has no fragment to link to at
all.

His two content claims both check out, with one placement correction. The
"distinct actions... not separate incidents... clustered into a few
connected behaviours" language, and the 10-of-122/19-actions figures, sit
inside "What we found" precisely as he said (measured 2,882 rendered chars
for that section against his 2,863 -- same order of counting-method drift
as the byte counts elsewhere in this exchange, not a discrepancy). The
model-split sentence he quoted verbatim ("Almost all of this behaviour (17
actions) came from a single model, Anthropic's Mythos 5, with 2 actions
involving OpenAI's GPT-5.6-Sol with cyber classifiers... disabled") is real,
but it lives in the lead paragraph under the page's h1, above "What
happened" -- not inside "What we found" as the surrounding sentence implied.
"What we found" does restate the same split in its own words ("17 of these
cases came from Mythos 5, and 2 came from a single run involving GPT-5.6
Sol"), just without the classifiers-disabled detail, so the fix below draws
only on what's actually inside that one section rather than reaching into
the lead paragraph for the extra nuance.

Checked something before touching the fix: the record's own "model" field
already read "Claude Mythos 5 (17 of 19 incidents in this test; OpenAI
GPT-5.6 Sol responsible for the other 2)" -- the split he was pointing at
was already correct in that field. What was wrong was the summary's
"producing 19 separate real-world actions," which is the word AISI's own
report explicitly rejects for these events. Fixed: summary corrected to
"distinct actions" that "clustered into a few connected behaviours,"
pointing at the model field for the split rather than re-typing it, dated
and attributed inline per this file's own convention. Left the id/model
value and the backdoor description alone -- both were already right.

Located the record: locator_precision=locator_ceiling="section",
locator_exhaustive=true, new source_locator naming the "What we found"
heading and stating plainly that it's a text anchor, not a URL fragment,
since the page has none. That answers his closing question: a heading with
no id still clears the bar for a locator. The precision ladder tracks how
narrowly a claim is pinned down inside a document a human can open and
read -- document/section/row/cell/field -- not whether the html happens to
expose a clickable fragment for it. A missing id changes how a reader finds
the spot (search the heading text instead of following a link), not
whether the spot exists or whether a human already found it. Saying that
plainly in source_locator, per his own suggestion, is what keeps a later
reader from assuming a fragment that isn't there. Re-ran the full checker
after the fix (EXIT 0, section 8->9, located 27->28, null 36->35, exhaustive
True 25->26) and a negative control (locator_exhaustive hand-flipped false
on this record) -- caught, same message round 16 introduced.

Round 30 (dipankarsarkar, 2026-09-08): pulled fresh at n=64, 29 located --
reproduced exactly. Then he ran three different anchor rules for
derive_source_structured() -- no split at all, round 22's ";|--", round 26's
";|,|--" -- against all 64 records. All three derive True on exactly 1 record
and agree with the stored value 64/64. Reproduced independently, same numbers.
The one record that exercises the regex at all is PALISADE-2026-robot-
shutdown-resistance: its real extension (".json") sits 16 characters before
the first comma in its source_locator, which is the entire evidential basis
for two rounds of anchor changes -- any split whose first delimiter lands
past that one point scores 64/64 regardless of where it splits. He checked
the sharper version of that claim directly: 0 of the 29 located records put
an extension ONLY in the tail an anchor discards (checked this myself with a
fixed version of my own first attempt at the same check, which searched for
an extension anywhere in the tail rather than only-in-the-tail and wrongly
flagged PALISADE itself, since its source_locator also happens to mention
src/figures/bar-chart.py later on, past the anchor, alongside the real .json
in the head -- a second occurrence, not a counterexample). Corrected before
it went anywhere near a conclusion.

His sharpest point: the two constructed cases that would actually exercise
this code -- a config.yaml/results.csv-shaped record with the extension only
in a discarded tail, and last round's dismech#1800/oh-my-openagent#5604 pair
-- were both built and verified by hand in prior rounds, and neither was ever
committed anywhere this checker reads. Confirmed: grepped the repo history
and the current tree, no such fixture exists. Also confirmed his second
finding independently: misbehavior_synthetic_contrast_v1.jsonl (7 records,
committed 2026-09-02) has no citation or source_locator field on any record,
and DATASET in this file has only ever pointed at the seed -- this checker
has never read that file. Not a new bug in that file; it was never meant to
exercise this invariant, built instead as behavioral-contrast material for a
different purpose entirely (see its own commit message). But it's real
evidence of the pattern he's naming: this project already has one precedent
for keeping synthetic material in a file separate from the seed rather than
merged into it, and that precedent was set for the same reason his question
answers itself in -- these aren't incidents.

Answered his closing question by building it: a fixtures file beside the
seed, not inside it. The seed is real incidents with real citations; four
made-up "config.yaml, results.csv"-shaped records in it would corrupt every
statistic this checker prints (verifiability counts, mechanised%, the
n this docstring keeps citing) with entries that exist to test code, not to
document anything that happened. locator_anchor_fixtures_v1.jsonl holds four
records -- extension-only-in-tail (expects False), extension-in-head (expects
True), no extension anywhere (expects False), extension present but no repo
host in the citation (expects False, checks the AND independently of the
anchor) -- each with an explicit `expected_source_structured` and marked
`"fixture": true` so nothing downstream mistakes one for an incident. main()
now loads this file unconditionally and fails loudly if
derive_source_structured() disagrees with any of the four. Proved it isn't
decorative before committing it: reverted the anchor to unanchored (`head =
source_locator or ""`, the exact round-22 bug) and reran -- FAIL, caught on
FIXTURE-tail-extension-discarded, the one case that distinguishes the two.
Restored the real anchor, reran clean. This is the same proof-of-falsifiability
standard round 28's banana case and round 16's negative controls were held
to, applied to the gap he found: before this round, no commit could fail on
the bug the anchor exists to prevent; now one specific commit (this one,
reverted) does.

Round 31 (dipankarsarkar, 2026-09-08): independently confirmed the 403 --
openai.com/index/hardening-atlas-against-prompt-injection/ returns 403 here
too (9,821-byte block page by content-length, in the same range as his
10,055 and my own earlier 9,842 -- a live challenge page, not a fixed file,
drifts by request the same way the AISI byte counts have all round), and so
does the Wayback copy (302 to a snapshot URL, which itself 403s). AISI still
200 at exactly 41,426 bytes. None of that is new; his actual point is that a
403 blocks re-verifying a page, not knowing what it affords, because a
sibling record already answered that question by citing the same page.

Reproduced his structural claim with a fresh script and got the wrong
numbers on the first pass: 11 co-cited sources, 9 agree, 2 disagree, not his
10/8/2. Own bug, found before reporting it: alphaxiv.org/overview/2412.04984
and arxiv.org/abs/2412.04984 are the same paper under two hosts, and my
extraction treated them as different sources, splitting APOLLO-2024-
sandbagging's citation (alphaxiv) from its two CONTRAST siblings' citations
of the identical paper (arxiv.org) into separate groups. Canonicalized both
to one `arxiv:<id>` key and got his exact numbers: 10 co-cited sources, 8
agree, 2 disagree, the same two he named.

His question -- is locator_ceiling a fact about the document or about the
claim -- has an answer already on record: round 16 defined it as "what the
SOURCE affords, a fact about the source independent of how far anyone has
pinned it so far." APOLLO-2024-sandbagging's round-24 ceiling of row, next
to its two siblings' independently-earned cell on the identical table, was
this file quietly reversing that definition without saying so -- capping a
source-level field to express something about one record's claim shape
instead. Fixed the actual inconsistency, not just the symptom: sandbagging's
locator_ceiling raised row -> cell (the source affords cell, demonstrated by
its own siblings), locator_precision stays row (this record's claim spans
a cell and prose together, so cell alone doesn't cover it), locator_exhaustive
now correctly False -- an honest gap, not a hidden one, with a note added to
the summary explaining why precision can't just follow ceiling up here the
way its siblings' did.

The Atlas pair needed the opposite move, also per his read: locator_ceiling
recovered from OPENAI-2025-atlas-resignation-injection-detected-CONTRAST
(section, "step 5 of the demo walkthrough") onto OPENAI-2025-atlas-
resignation-email-redteam, at zero fetch cost -- both records cite the exact
same page, and CONTRAST's own citation already establishes that page is
addressable at section granularity. locator_precision stays null (nobody has
found which section covers email-redteam's own scenario specifically, and
the 403 forecloses checking directly right now), locator_exhaustive false.

This forced a real change, not a patch: the old rule required
locator_precision / locator_ceiling / locator_exhaustive to be None
together or none of them, which assumed ceiling could never be known before
precision was -- exactly the assumption his question breaks. Rewrote it:
locator_ceiling is now the actual floor. None there forces the other two to
None (nothing about the source is known at all). Once it's set,
locator_exhaustive is `locator_precision == locator_ceiling`, computed the
same way whether or not precision itself is still null -- `None == "section"`
is `False` in Python, which is exactly the honest value: not exhaustive,
because the gap is still open.

Then built the check he said wasn't running: group every record by cited
source (same canonicalized extraction, arXiv/alphaxiv merged) and require
every co-citer's locator_ceiling to agree wherever more than one of them has
a non-None value -- a None ceiling in the group stays exempt, since "not yet
inferred" isn't a conflict with a known value, only two different known
values are. Verified both directions before committing: reverted
sandbagging's ceiling back to row -- caught, same violation message his own
demonstration would produce. Hand-set Atlas email-redteam's
locator_exhaustive to True against its new section ceiling -- caught by the
generalized round-16 derivation. Restored both, clean.

Round 32 (dipankarsarkar, 2026-09-08): reproduced his reconciliation of an
apparent mismatch first -- his 38-unlocated count and an earlier 36 are the
same file at different commits (13d8b21 vs 5f4c3fa, rounds 26-27's two
Anthropic promotions in between), not a miscount on either side. Confirmed
his controls against the round-28 enum check all give the exit codes he
listed, unchanged since that round.

His census: a double-quoted span of 40+ characters in summary or
source_locator -- not any quote, a long one, because a short one can be
typed without opening anything. Reproduced with a fresh script: 2 of the 30
unlocated human-checked records carry one (OPENCLAW-2026-melbourne-gym-hack,
OPENCODE-2026-orchestrator-silent-fallback -- the record fixed last round),
0 of 5 unverifiable, and his "1 of 29 located" doesn't reproduce here -- the
closest candidates on a located record are 13 and 8 characters (the AISI
h3-heading anchor and one word from its summary), both well under 40.
Flagging the mismatch rather than quietly matching his number; it doesn't
touch what the finding is actually about.

What the finding is about: MONARCH-2026-dismech-agent-scope-overreach was
opened and read this same session, round 28, live GitHub issue, maintainer's
reply quoted back to him in the reply thread verbatim. None of that quote
went into the record. Its summary was 528 characters with zero double-quote
characters in it, confirmed exactly. OPENCODE, corrected the same round for
the same reason (verifiability was wrong on both), got the sentence found in
its source written into the file. MONARCH didn't. Re-fetched the GitHub
issue live before touching anything -- the maintainer's reply is still there
verbatim, matches what was quoted back in round 28 to the character -- and
added it to the record: "the curation-scanner agent eagerly picked this up
and created PR #1803 before you had a chance to work on it yourself." The
evidence that was already found now lives in the file, not only in this
thread.

His own calibration of how strong this is was taken as stated, not
strengthened: a span is not derivable the way source_structured and
locator_exhaustive are -- the checker cannot tell a real quote from an
invented one, same limitation as source_locator text itself. Confirmed his
inert-today claim directly: stripping every double-quote character from
every summary and source_locator in the file, checker still exits 0. Not
promoted to a hard gate this round -- 32 of the 35 unlocated records would
fail one today for reasons that have nothing to do with whether they were
actually checked, and turning an emerging habit into a requirement before
enough records have it would fail real work, the same mistake a premature
"field" rung would have made. Added an informational count instead, printed
every run (3/35 now, up from 2/35 before MONARCH), the same way the
mechanised percentage already is -- visible without being enforced, so the
next round doesn't have to rediscover the number by hand.

Round 33 (dipankarsarkar, 2026-09-08): reproduced round 31's own commit and
round 32's, one apart -- hashes match to the byte on both, exit 0, n=64, 29
located on both. Ran his three controls against the unmodified checker and
got exactly his exit codes on all three, once corrected against my own first
mistake reproducing the second one: touching only locator_ceiling (not also
locator_exhaustive) on the Atlas record, matching what he actually did, not
what I assumed he did. Sandbagging ceiling cell->row: exit 1, two violations
(the derivation check and the co-citation check both fire, independently).
Atlas ceiling section->None, exhaustive left untouched: exit 1, caught by
round 31's own "ceiling is the floor" rule. Atlas ceiling section->row: exit
1, caught by round 31's co-citation check. Unmodified: exit 0.

His finding: the printed summary at the bottom of main() still scopes
locator_ceiling and locator_exhaustive to has_locator (locator_precision is
not None) -- the exact scope round 31 broke, on purpose, the day before.
Confirmed exactly: 30 records carry a non-None locator_ceiling and a non-None
locator_exhaustive in the file; has_locator has 29. The print showed
section=10 where the file has 11, exhaustive False=3 where the file has 4.
The one record the old scope drops is OPENAI-2025-atlas-resignation-email-
redteam -- round 31's own proof case, invisible in round 31's own summary
line ever since.

Answered his question by giving locator_ceiling its own denominator rather
than widening has_locator: precision and ceiling now mean different things
(one record can have a known ceiling and a still-null precision, that's the
entire point of last round), so folding ceiling's count into precision's
denominator was never going to be right at any width. locator_precision
stays scoped to itself; locator_ceiling and locator_exhaustive are now
scoped to "ceiling is not None," which round 31's own derivation already
guarantees is exactly when exhaustive is defined too. Added one line noting
when the two denominators diverge, so the next time this happens it prints
instead of hiding. Verified: locator_ceiling: section=11 (not 10),
locator_exhaustive: False=4 (not 3), both now matching the file exactly.
Re-ran all three of his controls against the fixed printer -- same exit
codes, same violation messages, nothing about the correctness invariants
changed, only what gets printed once they've already passed.

Round 34 (dipankarsarkar, 2026-09-08): confirmed the round-30 fixtures file's
provenance first -- blob 6c05f8c0, 1735 bytes, byte-identical across 113b55b,
38924af and d9110f8, sha256 matching its own sidecar. Reproduced his three
anchor reversions against those four fixtures exactly: no split at all
caught (FIXTURE-tail-extension-discarded), the repo-host AND collapsed to
True caught (FIXTURE-extension-no-repo-host), and reverting the comma
specifically -- back to round 22's ";|--" -- passes clean, exit 0, nothing
fires.

That third result is real: none of the four fixtures exercise the shape
round 26 was written to fix. FIXTURE-tail-extension-discarded's own first
delimiter is "--" (its source_locator reads "...directory -- config.yaml,
results.csv..."), so the pre-round-26 anchor already discards its tail
correctly on its own -- the fixture passes under either anchor and proves
nothing about the comma rung specifically. Added a fifth fixture with comma
as the ONLY delimiter present, extension in the comma-discarded tail --
exactly round 26's own description of "7 of 25 located records" scaled up.
Verified his full matrix: 4 fixtures/current anchor exit 0, 4/round-22-anchor
exit 0 (the gap), 5/current anchor exit 0 (no false positive from the new
fixture), 5/round-22-anchor exit 1, caught.

Then went further on his own closing question rather than just answering
it. Reproduced his co-citation-style census on the anchor's own delimiters
across all 64 records: comma is present in 29/29 located records and is the
first delimiter on 28 of them; "--" is first on the remaining one; ";"
appears anywhere in only 8 and is first in zero. Dropping ";" or "--"
individually from the anchor flips zero records today; dropping the comma
alone doesn't flip any either (0 flips) but does expose 7 records to a
latent risk they don't currently trigger (head==whole jumps 0/29 -> 7/29) --
the same shape the fifth fixture now guards. His question -- was ";"
inherited from round 22 and never tested, or did a real citation once need
it -- turned out to be neither cleanly. Checked git history directly: round
22 had no anchor at all (unsplit); round 23 introduced ";|--" together, and
at that commit OPENAI-2025-anti-scheming-stress-test's source_locator
genuinely split on ";" first under the then-current two-delimiter anchor --
";" was load-bearing, not decorative, when it was added. Round 26 then added
comma for an unrelated reason (PALISADE's shape), and that same record's
source_locator happens to contain a comma before its semicolon -- comma
silently took over as the first delimiter for that record, and nobody
re-checked afterward whether ";" still guarded anything. It doesn't, for any
of today's 64 records. A sixth fixture closes the loop the same way the
fifth did: semicolon as the only delimiter present, extension in the tail --
passes under the real anchor, caught (exit 1) if ";" is dropped from it.
All three rungs of the anchor now have a fixture that would fail if that
rung were removed; none of the seed's own 64 records currently need any of
the three on their own, which is exactly why the fixtures exist instead of
resting the claim on the seed.

Round 35 (dipankarsarkar, 2026-09-14): reproduced his own round-32 span
census against five revisions (13d8b21, 5f4c3fa, 113b55b, 38924af, d9110f8)
and got 0 at every one, not the "1 of 29 located" he had reported --
confirmed as his own transcription error, not a bug on either side; his
0-of-5-unverifiable count did reproduce. Located the real span-carrying
population at HEAD: 3 of 35 unlocated records carry a 40+-char quote
(MONARCH, OPENCODE, OPENCLAW -- the same three round 32's counter already
printed), and 0 of the 29 located records do (the closest are 13 and 8
characters, both his own numbers, both under the 40-char threshold).

n at HEAD is 65, not his 64 -- ANTHROPIC-2026-deepseek-distillation-relay
(commit e9ebb1b) was added the session before this one, after whichever
revision he last pulled for this exchange, not a discrepancy in either
analysis. It is already located (section) and independently carries a 40+
char quote of its own, which is why the post-fix span count below reads
4/65 with 2 located, not the 3/65-with-1-located this round's own fixes to
MONARCH alone would otherwise produce.

Then tested the span as if it already were a verification mechanism, not
just a count: fetched all three sources independently and ran each quote as
a literal ctrl-F. OPENCODE passed clean (0 edits). MONARCH needed one edit,
harmless -- a capitalization difference where the record's summary sentence
starts mid-quote and the source doesn't. OPENCLAW needed four: two curly
apostrophes and a terminal comma, all typographic, and one that isn't --
the record's "authorisation checks" (singular) against the source's actual
"authorisations checks" (plural, ungrammatical, and printed that way in
TechCrunch's own text, re-fetched and confirmed verbatim here before
touching anything). The record had silently corrected the source's grammar.
That is the exact failure a ctrl-F-able span exists to catch, arriving from
the friendly direction: nobody invented a quote, someone tidied one, and a
tidied quote stops being ctrl-F-able against the thing it claims to quote.

Fixed: OPENCLAW's span replaced with a fresh verbatim quote from
techcrunch.com directly (the citation's own first-listed source -- the prior
text had cited a secondary BBC summary that was never in this record's own
citation field, a second small gap closed the same round), preserving the
source's actual wording including its grammar. The three typographic
differences (curly vs. straight apostrophes, a comma vs. a period) are not
folded away or hidden -- they're simply what the correct verbatim quote
looks like once copied from the primary source instead of reconstructed
from memory of it.

Also checked whether the two verification mechanisms this file has -- a
locator (document/section/row/cell/field, requires opening the source and
finding a machine-addressable position) and a span (a long quote, requires
nothing but a ctrl-F) -- ever apply to the same record. Across all 64: 29
located, 3 span-carrying, 0 both, 32 neither. Disjoint, completely. A span
is not currently a complement to a locator in this file; it's what gets
written when a locator wasn't pursued.

That made the disjointness itself worth checking, not just noting, on the
one record it looked wrong for: MONARCH's span -- "eagerly picked this up
and created PR #1803 before you had a chance to work on it yourself" -- is
117 characters long, which is why it counted as a span at all, but it is
also, independently, a real locator: it names one exact GitHub issue
comment. Fetched the permalink directly (not the WebFetch-summarized
rendering, which drops GitHub's dynamically-loaded comment content the same
way it dropped this repo's own HF post comments earlier the same session --
raw HTML, grepped for the comment's own JSON-LD body) and confirmed
issuecomment-4331930210 exists and its text matches this record's quote
exactly, to the character. A span this specific was never "instead of" a
locator; it already contained one, just not written into the citation or
locator_precision fields as one.

Fixed: MONARCH's citation extended to the specific comment anchor
(#issuecomment-4331930210, not just the issue URL), locator_precision =
locator_ceiling = "row" (one identifiable comment among many on the issue,
the same rung a numbered list item or table row earns elsewhere in this
file), locator_exhaustive = true. OPENCODE and OPENCLAW are not promoted the
same way: OPENCODE's span quotes the issue's own opening body, not a
specific numbered comment among several, and OPENCLAW's span is a chat-log
excerpt embedded in a news article, not an addressable position within that
article -- neither currently affords a rung finer than "the whole cited
piece contains this," which this file has never treated as a locator on its
own (round 25 already answered a structurally identical question this way
for a different record).

His closing question -- does a folding rule run before the ctrl-F check, or
does the check compare the raw span and the record gets corrected back to
match the source's own typo -- is answered by what got fixed above, not by
new code: the record gets corrected to the source, always, typo included.
Nothing here builds an automated live-fetch verifier for spans generally --
the same reason round 28 declined to add "HTTP 200" as a verifiability rung
applies with equal force to a network-dependent ctrl-F check, and this
round's own experience underlines it: WebFetch's summarizing fetch could not
see either GitHub's real comment body or (earlier the same session, a
different page) this repo's own HF post's comments, and only a raw,
unsummarized fetch found what was actually there. A span's whole value is
that a human reader can verify it with nothing but ctrl-F and the primary
source open in a tab; automating that check would trade the property that
makes it worth having for a network call this file's own history has
already found unreliable. What this round adds instead: fold_typographic(),
a small, offline, non-gating helper that normalizes curly quotes/apostrophes
and dash variants for the one purpose it's honest about -- letting a human
doing this exact comparison by hand see which of several diffs are
typographic noise and which one, like OPENCLAW's dropped "s", is a real word
the record got wrong. It does not touch the dataset and is not called from
main(); it exists for the next person who opens a source to re-check a span,
the same manual act this round performed three times.

Round 38 (dipankarsarkar, 2026-09-14): computed the exercised set rather
than asserting it. Restricted to the only place the anchor's split point
can change derive_source_structured()'s output -- records whose citation
matches _REPO_HOST_RE -- there are 3 (PALISADE, MONARCH, OPENCODE), and
of those exactly 1 (PALISADE) carries a non-empty source_locator at all.
Its head, truncated at the end of the machine-readable-extension match
that makes it True, is "logs/on_the_robot/stats_run/live_05022026/tags.json"
-- 51 characters, 22 distinct, non-alphanumeric members {. / _}. Confirmed
directly against derive_source_structured() itself, not a re-derivation:
dropping ";", ",", "--", or all three from the anchor flips 0 of 65 real
records, individually or together -- the same 0 he found on his 64-record
mirror. Rounds 23 and 26 introduced ";", ",", "--" against citation shapes
expected at the time; neither has ever been exercised by a real record in
this file's history, and round 37's fixture-head assertion protects the
fixtures' own split points, not evidence that the real corpus needs them.

Answered his closing question directly: at HEAD, MONARCH's round-35
promotion (locator_precision/locator_ceiling="row", verifiability=
"mechanised", citation extended to the specific comment anchor) never
added a source_locator field -- confirmed by key-membership check, not
just a None value. MONARCH counts as "located" in every count this file
prints, and contributes nothing to _exercised_chars() because that
function only credits a record once it has actual source_locator text to
compute a head from. The addition side is still n=1, exactly as he
suspected, and now stated as such below rather than left to be
rediscovered by the next person who assumes "row" means "has a locator
string."

Fixed: _exercised_chars() computes, from the real records at whatever n
the file has today, which of the anchor's rung characters ({';', ',',
'-'}) a real record has actually put where the split point could matter,
truncated the same way derive_source_structured() itself would stop
mattering (at the first machine-readable-extension match). Printed every
run, informational and non-gating like the round-32 span count -- a
computed bound replaces the implicit claim that six fixtures passing means
six characters are covered by real evidence. Today it prints all three
rungs as inert on the real corpus; a future record naming a real path with
a semicolon, comma, or double-hyphen in it before its extension would move
that character out of the inert set without anyone having to notice by
hand.

Round 39 (dipankarsarkar): round 38's shipped print told the truth about
character rungs but missed the sharper gap underneath -- nothing checked
whether a located record still carried evidence of *where*. Demonstrated
against the real 65-record corpus, not proposed: deleted source_locator
from each of the 30 located records that had one and re-ran this file's
own checker unmodified. 29 of 30 stayed exit 0 -- APOLLO-2024-oversight-
subversion, among others, kept asserting locator_precision="row" /
locator_ceiling="cell" / locator_exhaustive=False / verifiability=
"mechanised" with its 55-character source_locator silently gone. Only
PALISADE was caught, and only because derive_source_structured()'s
boolean happens to depend on its source_locator content -- an accident of
that one record's shape, the same accident round 36-38 already
identified for the split characters, just one layer up: this file was
checking whether a located record's derived boolean was internally
consistent, never whether the location claim itself still pointed at
anything.

MONARCH sharpened the same question from the other side: it has never
had a source_locator (absent as a key, not null), yet carries
locator_precision="row" since round 35, promoted on the strength of a
GitHub comment permalink -- a "#issuecomment-4331930210" fragment
appended to citation, the only "#" among all 65 citations. Checked
directly: dropping that fragment, changing the issue number, or
replacing the whole citation with a bare URL all leave this file exit 0,
because source_locator is read in exactly two places (derive_source_
structured, the round-32 span count) and MONARCH touches neither.

Fixed: `_anchor_present(record)` -- true iff source_locator is non-empty,
or citation carries a non-empty fragment after "#". A located record
(locator_precision is not None) with neither is now a hard violation, not
an informational count. Verified before shipping, not asserted: 0
violations on the real 65-record corpus at HEAD; stripping the anchor
from each of the 31 located records one at a time fires this check on
all 31, not a subset. That is the property round 38's rung-exercise
count was reaching for and didn't have -- a check exercised by every
record it applies to, rather than by one accident of shape.

MONARCH's own question -- is a citation fragment a locator carrier this
file now endorses, or a source_locator nobody has written down yet --
is left open on purpose: `_anchor_present()` accepts it without
promoting it to the file's primary mechanism. A future round should
either write MONARCH's fragment into an actual source_locator string
(making it uniform with every other located record) or decide fragments
are a real second carrier worth documenting as such, but that is an
editorial call about the dataset, not something this round's fix should
decide by default.

Round 40 (dipankarsarkar, 2026-09-20): re-verified the round-39 push at
9c518f9 byte-identical, then ran it unmodified against HEAD's 12 new
records and got FAIL, 6 violations, not the exit-0 the round-39 commit
shipped with -- three new records (GOOGLE-2026-gemini-irregular-ctf-
breakout, USMIL-2026-china-ship-ai-hallucinated-intel-report, OPENAI-2026-
sol-astra-successor-concealment-notes) were added with
locator_precision=locator_ceiling="paragraph", off the LADDER entirely, so
`lc not in LADDER` fired and its `continue` masked the anchor check on the
same three records too -- exercised by construction the same week the
records were added, same shape as every prior round's find.

Fixed the data first, by opening what could actually be opened: TechCrunch
(the OpenAI record's citation) fetched directly, confirmed zero internal
h2/h3 headings, continuous prose start to finish -- "document" is this
source's genuine, verified ceiling, not an underclaim. CNBC (Google record)
and CNN (USMIL record) both blocked on direct fetch (403 and 451
respectively, checked the same way this file already documents openai.com's
403 in rounds 27/31) -- structure not independently verifiable right now,
so both also set to "document", the honest floor given what could actually
be checked today, not an assumption that no finer structure exists. All
three: locator_precision=locator_ceiling="document"=lp==lc so
locator_exhaustive=True, source_locator states plainly what was checked
(TechCrunch's confirmed flat structure, or the CNBC/CNN fetch block) rather
than asserting a fragment that doesn't exist.

Then the sharper find, against the checker itself: dipankarsarkar noticed
`_anchor_present()`'s citation-fragment carrier (round 39's MONARCH
accommodation) cannot tell a real URL fragment from a literal '#' inside
prose. This file's own internal NO_URL citations read "...CLAUDE_INCIDENTS.
md, entry #13 (private, not publicly resolvable -- no external URL exists
for this record)" -- non-empty text sits after that '#', so a record set to
locator_precision="section" with that exact citation and no source_locator
passes the round-39 anchor check clean. He demonstrated this on a scratch
copy (SIPA-2026-chatgpt-self-admitted-fabrication, promoted there only,
never touching the tracked file) rather than arguing it, and it reproduces
here identically: reran the same construction independently before touching
anything, confirmed exit 0 on the exploit as he described it, then restored
and confirmed the tracked file itself was never edited by his probe.

His fix, applied verbatim: single carrier, not two. `_anchor_present()` now
checks source_locator only. MONARCH-2026-dismech-agent-scope-overreach's
citation-fragment anchor (its GitHub comment permalink's own
'#issuecomment-...' suffix, the only '#' among all 65 citations at round
39) is moved into an explicit source_locator naming the same permalink and
the maintainer's quote it was always standing in for -- uniform with every
other located record's carrier now, not a second, weaker mechanism living
in citation. Re-ran the SIPA-2026-chatgpt-self-admitted-fabrication exploit
against the tightened checker on a fresh scratch copy: FAIL, caught by
name, same message the round-39 anchor check already used for a record with
no carrier at all -- the two-carrier version's specific hole is closed, not
patched around. Full corpus re-verified clean after both fixes: exit 0,
n=78, 0 violations.

His closing question -- is "paragraph" a real sixth rung below "section"
for prose sources, or were these three simply typed one level too fine --
is answered here as the second, for these three specifically: neither
"section" (no anchored or nameable heading was actually found -- TechCrunch
has none, CNBC/CNN couldn't be checked) nor a new "paragraph" rung was
earned by opening the source, so "document" is what the evidence in hand
actually supports. This does not foreclose a genuine "paragraph" rung
existing for some future prose source -- it says these three specific
citations, checked today, don't clear even "section," so reaching for a
finer rung than that would repeat the exact mistake round 18 named: writing
down a precision claim before the source was opened to see what it affords.

Exit code is nonzero iff any record violates a hard invariant -- built by
Claude, 2026-09-01 through 09-20, in direct response to dipankarsarkar's
rounds 12 through 40.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "misbehavior_incidents_seed_v1.jsonl"
# Round 30 (dipankarsarkar): a fixture file loaded BESIDE the seed, not merged
# into it. These are synthetic regression cases for derive_source_structured()
# alone, not real incidents -- see the round-30 docstring section for why they
# don't belong in the seed itself.
ANCHOR_FIXTURES = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_MISBEHAVIOR_EXTERNAL" / "locator_anchor_fixtures_v1.jsonl"

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

# Round 22 (dipankarsarkar): source_structured, derived rather than hand-typed.
# A repo host in the citation and a machine-readable extension in
# source_locator are both facts about strings this file already carries --
# neither depends on locator_precision being set, so this is computable for
# all 63 records, not just the 25 located ones. See the round-22 docstring
# section above for the forgery this closes and the 63/63 agreement check
# performed against the pre-existing hand-typed values before this replaced
# them.
#
# Round 23 (dipankarsarkar): the extension search below is anchored to the
# HEAD of source_locator -- everything before the first ";" or "--" -- not
# the whole string. Unanchored, it matched incidental file-extension-shaped
# substrings inside annotation prose appended after a record's real path
# (demonstrated on PALISADE-2026-robot-shutdown-resistance's 422-character
# source_locator, which names six files across its full length, five of
# them after the first "--" and none of them what the citation actually
# points at). Anchoring changes nothing on today's 25 located records --
# none of them name their real file only in the tail -- but stops trusting
# a match anywhere prose happens to mention a filename.
_REPO_HOST_RE = re.compile(
    r"github\.com|gitlab\.com|bitbucket\.org|huggingface\.co/datasets|"
    r"huggingface\.co/[^/\s]+/[^/\s]+/(blob|resolve)"
)
_MACHINE_READABLE_EXT_RE = re.compile(r"\.(json|jsonl|csv|tsv|yaml|yml|py)\b", re.IGNORECASE)

# Round 26 (dipankarsarkar): ";|--" alone left 7 of 25 located records with
# no delimiter present at all, so the "head" equaled the whole string on
# those -- unanchored, exactly the round-22 shape, just on comma-and-period
# prose citations instead of tail-appended annotations. Comma appears in
# all 25 of today's located records; ";" or "--" appear in only 18. Adding
# comma closes the gap: 0 of 25 inert, same 63/63 agreement, PALISADE still
# derives True (its real path sits before the first comma too).
#
# Round 37 (dipankarsarkar): pulled out of derive_source_structured() into
# its own named pattern + helper so the fixture check (below) can assert
# the exact head a fixture produces, not just derive_source_structured()'s
# downstream boolean. Round 30-36's fixtures only ever failed when a rung
# was REMOVED, because removing a rung can only turn a False into a False
# or a True into a False on data that has an extension in the head. Adding
# a rung is not symmetric: it can shorten a head that happens to still keep
# the extension, or a head that has no extension at all, and if the removed
# span never contained the anchor's own load-bearing character neither
# derive_source_structured() nor the six existing fixtures would ever
# notice -- a fourth delimiter could ship silently and stay unnoticed until
# a real record's extension happened to fall in the newly-discarded span,
# by which time the commit that broke it is long gone. Asserting the head
# itself (not the boolean two steps downstream of it) makes every fixture
# an addition-side guard automatically, without needing a purpose-built
# fixture per hypothetical delimiter.
_ANCHOR_SPLIT_RE = re.compile(r";|,|--")


def _anchor_head(source_locator) -> str:
    return _ANCHOR_SPLIT_RE.split(source_locator or "", maxsplit=1)[0]


def derive_source_structured(citation, source_locator) -> bool:
    head = _anchor_head(source_locator)
    return bool(_REPO_HOST_RE.search(citation or "")) and bool(
        _MACHINE_READABLE_EXT_RE.search(head)
    )


def _anchor_present(record) -> bool:
    """Round 39 (dipankarsarkar): a located record (locator_precision is not
    None) asserts that someone found a specific position in the source. This
    checks that the record still carries evidence of where.

    Round 39 originally accepted a non-empty source_locator OR a non-empty
    fragment after '#' in citation (MONARCH's case: a GitHub comment
    permalink's own '#issuecomment-...' fragment, used as a de facto anchor
    without ever being written into source_locator). Same round, follow-up
    (dipankarsarkar): the citation-fragment carrier cannot distinguish a real
    URL fragment from a literal '#' inside prose. Demonstrated: this file's
    own internal NO_URL citations read like "...CLAUDE_INCIDENTS.md, entry
    #13 (private, not publicly resolvable -- no external URL exists for this
    record)" -- non-empty text sits after that '#', so the two-carrier
    version certifies an anchor on a citation that states outright it cannot
    be resolved. Fixed: single carrier. source_locator only. MONARCH's
    fragment was moved into an explicit source_locator (same commit), making
    it uniform with every other located record instead of a second, weaker
    mechanism living in a different field."""
    return bool(record.get("source_locator"))


# Round 38 (dipankarsarkar): the anchor's own split characters, as a set --
# not the same thing as the anchor regex, which also encodes "--" as a
# two-char token. A rung is "exercised" if a real record ever put it where
# the split point could change derive_source_structured()'s output; this is
# the set that question is asked about.
_RUNG_CHARS = frozenset(";,-")


def _exercised_chars(records) -> set:
    """Characters a real record has actually put in the span that decides
    derive_source_structured()'s boolean, across all records at whatever n
    this file has today. Only repo-host-cited records can move that boolean
    at all (see derive_source_structured), so only they can exercise
    anything; a record with no source_locator contributes nothing, and a
    record whose head extends past its own extension match contributes only
    the prefix up to and including that match, since nothing after it
    changes the result. Round 37's fixtures pin what derive_source_structured
    outputs when handed six invented shapes; this instead asks what
    characters the real corpus itself has ever exercised the anchor with,
    so the two questions don't get answered as if they were one."""
    chars = set()
    for r in records:
        if not _REPO_HOST_RE.search(r.get("citation") or ""):
            continue
        loc = r.get("source_locator")
        if not loc:
            continue
        head = _anchor_head(loc)
        m = _MACHINE_READABLE_EXT_RE.search(head)
        span = head[: m.end()] if m else head
        chars |= set(span)
    return chars


_ARXIV_ID_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([\d.]+)", re.IGNORECASE)
_ALPHAXIV_ID_RE = re.compile(r"alphaxiv\.org/overview/([\d.]+)", re.IGNORECASE)
_URL_RE = re.compile(r"https?://([^\s)]+)")


_TYPOGRAPHIC_FOLD = {
    "‘": "'", "’": "'",  # curly single quotes -> straight
    "“": '"', "”": '"',  # curly double quotes -> straight
    "–": "-", "—": "-",  # en/em dash -> hyphen
    "…": "...",  # ellipsis character -> three dots
}


def fold_typographic(s: str) -> str:
    """Round 35 (dipankarsarkar): normalizes ONLY typographic character
    variants (curly quotes/apostrophes, dash styles, the ellipsis glyph) so a
    human comparing a record's quoted span against a freshly-fetched primary
    source can see which differences are punctuation-rendering noise and
    which are real wording differences (a dropped word, a changed word,
    "corrected" grammar). It does not touch spelling, wording, or case, and
    it is not called from main() -- folding a span for comparison is a manual
    verification aid, never a reason to store a folded (rather than verbatim)
    quote in the record itself. Demonstrated on OPENCLAW-2026-melbourne-gym-
    hack's pre-round-35 text: three of its four diffs against techcrunch.com
    fold away under this function (two apostrophes, one dash-position
    artifact of the terminal punctuation); the fourth ("authorisation" vs.
    the source's "authorisations") does not fold away under any typographic
    rule, because it isn't typographic -- it's the actual bug this round
    fixed."""
    for src, dst in _TYPOGRAPHIC_FOLD.items():
        s = s.replace(src, dst)
    return s


def extract_sources(citation):
    # Round 31 (dipankarsarkar): grouping records by cited source to check
    # locator_ceiling agreement. alphaxiv.org/overview/<id> and
    # arxiv.org/abs|pdf/<id> are the same paper under two hosts -- without
    # canonicalizing them to one key, APOLLO-2024-sandbagging's alphaxiv
    # citation and its two CONTRAST siblings' arxiv.org citations of the
    # identical paper (2412.04984) land in separate groups and the
    # disagreement this check exists to catch goes invisible.
    if not citation:
        return set()
    sources = set()
    for part in re.split(r";", citation):
        part = part.strip()
        m = _ARXIV_ID_RE.search(part) or _ALPHAXIV_ID_RE.search(part)
        if m:
            sources.add(f"arxiv:{m.group(1)}")
            continue
        m2 = _URL_RE.search(part)
        if m2:
            sources.add(m2.group(1).rstrip("/"))
    return sources


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

            # Round 28 (dipankarsarkar): verifiability had no enum check at all --
            # any string, including "banana", passed on every unlocated record.
            # This doesn't decide which of the two real values applies where (that
            # still needs a human to open the source), it only stops nonsense
            # values from passing silently.
            if v not in ("mechanised", "human-checked", "unverifiable"):
                violations.append(
                    f"{rid}: verifiability={v!r} is not one of mechanised/human-checked/unverifiable"
                )
                continue

            required = ("locator_precision", "locator_ceiling", "locator_exhaustive", "source_structured")
            missing = [k for k in required if k not in record]
            if missing:
                violations.append(f"{rid}: missing key(s) {missing} -- all four must be present on every record")
                continue

            lp = record["locator_precision"]
            lc = record["locator_ceiling"]
            le = record["locator_exhaustive"]
            ss = record["source_structured"]

            # Round 22 (dipankarsarkar): source_structured is derived, not trusted.
            # Demonstrated live: hand-setting BERKELEY-2026-peer-preservation to
            # locator_precision=locator_ceiling="field", source_structured=True
            # passed round 20's checker cleanly, exit 0, despite its source being
            # a printed PDF table, not structured data. Computed independently of
            # locator_precision -- unlike locator_exhaustive, this doesn't need a
            # location to exist yet, only a citation and (if present) a
            # source_locator. Round 23 correction: source_locator is absent
            # as a key (not present-and-null) on 38 of the 63 records --
            # .get() below returns None either way, which is what
            # derive_source_structured() already expects.
            expected_ss = derive_source_structured(record.get("citation"), record.get("source_locator"))
            if ss != expected_ss:
                violations.append(
                    f"{rid}: source_structured={ss!r} but derived from citation+source_locator is "
                    f"{expected_ss!r} (round 22: hand-typed values are no longer trusted, only checked)"
                )
                continue

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

            # Round 25 (dipankarsarkar): a located record cannot also be
            # unverifiable. Pinning a locator_precision at all -- even
            # "section", the coarsest non-null rung -- already means someone
            # went and looked closely enough to name a specific place in the
            # source. "unverifiable" on that same record contradicts its own
            # locator_precision, not just the mechanised<->row rule above.
            if lp is not None and v == "unverifiable":
                violations.append(
                    f"{rid}: locator_precision={lp!r} (a specific location was found) but "
                    f"verifiability='unverifiable' -- if you can point at a location, you already looked"
                )

            # Round 39 (dipankarsarkar): locator_precision is not None asserts
            # a specific position was found, but nothing previously required
            # the record to still carry evidence of *where*. Demonstrated live:
            # deleting source_locator from 30 located records one at a time
            # and re-running this file's own checker caught exactly 1 of them
            # (PALISADE, only because derive_source_structured's boolean
            # happens to depend on it) -- the other 29, including APOLLO-2024-
            # oversight-subversion, kept locator_precision="row" / ceiling=
            # "cell" / exhaustive=False / verifiability="mechanised" with the
            # 55-character locator that justified all four silently gone.
            # MONARCH is the sharper case: it has never had a source_locator
            # (absent as a key, not null), and was promoted to "row" in round
            # 35 on the strength of a comment permalink appended to its
            # citation as a "#issuecomment-..." URL fragment -- the only "#"
            # among all 65 citations. _anchor_present() treats that fragment
            # as an equally valid carrier of the same claim: an anchor is
            # either a non-empty source_locator, or a non-empty fragment after
            # "#" in citation. Checked directly, not proposed: 0 violations at
            # HEAD on the real 65 records, and stripping the anchor from each
            # of the 31 located records one at a time fires this check on all
            # 31 -- unlike the three split-character rungs (round 38), this
            # rung is exercised by every located record that exists, not by
            # one accident of shape.
            if lp is not None and not _anchor_present(record):
                violations.append(
                    f"{rid}: locator_precision={lp!r} but no anchor -- source_locator is absent/empty "
                    f"and citation carries no '#' fragment either (round 39: a location claim with "
                    f"nothing pointing at it is unfalsifiable the moment the locator is edited or removed)"
                )

            # Round 22: source_structured left this invariant. It no longer needs a
            # location to exist -- structuredness is a fact about citation and
            # source_locator strings, checked above unconditionally, whether or not
            # a locator has been pinned yet.
            #
            # Round 31 (dipankarsarkar): the old rule ("all three None together, or
            # none of them") assumed locator_ceiling could never be known before
            # locator_precision was. That's false -- ceiling is a fact about the
            # SOURCE, so it can be recovered from a co-cited sibling that already
            # reached it, with this record's own precision still honestly null
            # because nobody has located this record's own claim in that source
            # yet. Only locator_ceiling is the real floor now: if it's None,
            # neither precision nor exhaustive can be anything but None either
            # (nothing about the source is known at all). If it's known,
            # exhaustive is just `precision == ceiling`, computed the same way
            # whether or not precision itself is still null (None == "section"
            # is False in Python, which is exactly the honest answer: not
            # exhaustive, because the gap hasn't been closed).
            if lc is None:
                if lp is not None or le is not None:
                    violations.append(
                        f"{rid}: locator_ceiling=None but locator_precision={lp!r} / "
                        f"locator_exhaustive={le!r} -- ceiling is the floor; neither of "
                        f"the others can be known before it is (round 31)"
                    )
                continue

            if lc not in LADDER:
                violations.append(f"{rid}: locator_ceiling={lc!r} not on the known ladder")
                continue

            if lp is not None:
                if lp not in LADDER:
                    violations.append(f"{rid}: locator_precision={lp!r} not on the known ladder")
                    continue
                if LADDER[lp] > LADDER[lc]:
                    violations.append(
                        f"{rid}: locator_precision={lp!r} is finer than locator_ceiling={lc!r} -- "
                        f"achieved precision cannot exceed what the source affords"
                    )
                # Round 18 (dipankarsarkar) added this gate; round 22 (dipankarsarkar)
                # demonstrated it was still forgeable because `ss` was hand-typed and
                # only checked for presence, not correctness -- BERKELEY-2026-peer-
                # preservation (a printed PDF table) passed as "field" once someone
                # typed source_structured=True next to it. `ss` above is no longer
                # read from the file uncritically: it was already checked against
                # derive_source_structured() and the function returned before this
                # line if they disagreed. This check now enforces a derived fact, not
                # a self-asserted one.
                if (lp == "field" or lc == "field") and ss is not True:
                    violations.append(
                        f"{rid}: locator_precision={lp!r} / locator_ceiling={lc!r} reaches 'field' but "
                        f"source_structured={ss!r} -- 'field' requires a verified structured-data source "
                        f"(round 18: this was prose, not enforced, until now)"
                    )

            expected_le = (lp is not None and lp == lc)
            if le != expected_le:
                violations.append(
                    f"{rid}: locator_exhaustive={le!r} but expected {expected_le!r} from "
                    f"locator_precision={lp!r} vs locator_ceiling={lc!r} -- locator_exhaustive "
                    f"must be derived, not hand-typed (round 16, generalized round 31 for a "
                    f"known ceiling with a still-null precision)"
                )

    # Round 31 (dipankarsarkar): locator_ceiling is defined (round 16) as a
    # fact about the SOURCE, not about this record's own investigation --
    # so any two records citing the same source must carry the same
    # ceiling. This was demonstrated by hand, not run: grouping all records
    # by cited source and comparing locator_ceiling within each group.
    # Records still at locator_ceiling=None inside a group are exempt --
    # None means "not yet inferred," not a conflicting value -- this check
    # is only about two DIFFERENT known ceilings on the same source, which
    # is what round 24's APOLLO-2024-sandbagging (row, while its two
    # siblings independently earned cell) and the OpenAI Atlas pair (None
    # on one record, section on its sibling, before this round's fix)
    # actually were.
    source_to_ids = {}
    for r in records:
        for s in extract_sources(r.get("citation")):
            source_to_ids.setdefault(s, []).append(r["id"])
    rec_by_id = {r["id"]: r for r in records}
    for source, ids in source_to_ids.items():
        if len(set(ids)) < 2:
            continue
        known_ceilings = {
            rec_by_id[i]["locator_ceiling"] for i in ids if rec_by_id[i]["locator_ceiling"] is not None
        }
        if len(known_ceilings) > 1:
            violations.append(
                f"co-cited source {source!r} has disagreeing locator_ceiling values "
                f"{sorted(known_ceilings)} across {sorted(set(ids))} -- ceiling is a fact "
                f"about the source (round 16), so co-citers of the same source cannot "
                f"legitimately disagree (round 31)"
            )

    # Round 30 (dipankarsarkar): every anchor rule tried on the real 64 records
    # (unanchored, round-22 ";|--", round-26 ";|,|--") derives the same 1/64
    # and agrees 64/64 -- the seed's own data cannot fail on the bug this
    # anchor exists to prevent, because exactly one located record has an
    # extension anywhere in source_locator at all, and it sits in the head
    # under every anchor tried. These four fixtures are what makes a
    # regression here actually fail loudly instead of passing silently.
    with open(ANCHOR_FIXTURES, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            fixture = json.loads(line)
            fid = fixture.get("id", f"<fixture line {lineno}>")
            got_head = _anchor_head(fixture.get("source_locator"))
            if "expected_head" in fixture and got_head != fixture["expected_head"]:
                violations.append(
                    f"{fid}: anchor head is {got_head!r}, fixture expects {fixture['expected_head']!r} "
                    f"-- the anchor's split point moved, not just its downstream boolean (round 37) "
                    f"({fixture.get('purpose', 'no purpose given')})"
                )
            got = derive_source_structured(fixture.get("citation"), fixture.get("source_locator"))
            expected = fixture["expected_source_structured"]
            if got != expected:
                violations.append(
                    f"{fid}: derive_source_structured() returned {got!r}, fixture expects {expected!r} "
                    f"({fixture.get('purpose', 'no purpose given')})"
                )

    if violations:
        print(f"FAIL: {len(violations)} invariant violation(s) in {DATASET.relative_to(REPO_ROOT)}")
        for v in violations:
            print(f"  - {v}")
        return 1

    n = len(records)
    verif_counts = Counter(r.get("verifiability") for r in records)
    # Round 33 (dipankarsarkar): locator_precision and locator_ceiling get their
    # own denominators, not one shared "has_locator" scope. Round 31 decoupled
    # them on purpose -- ceiling can be known (via a co-cited sibling) while
    # precision is still null, which is exactly what OPENAI-2025-atlas-
    # resignation-email-redteam is. Scoping ceiling/exhaustive to
    # locator_precision-is-not-None silently dropped that one record from both
    # counts, undercounting the very case the round's own fix produced.
    has_locator = [r for r in records if r["locator_precision"] is not None]
    has_ceiling = [r for r in records if r["locator_ceiling"] is not None]
    locp_counts = Counter(r["locator_precision"] for r in has_locator)
    ceiling_counts = Counter(r["locator_ceiling"] for r in has_ceiling)
    exhaustive_scoped = Counter(r["locator_exhaustive"] for r in has_ceiling)

    print(f"OK: verifiability<->locator_precision<->locator_ceiling<->locator_exhaustive invariants hold "
          f"across all records in {DATASET.relative_to(REPO_ROOT)}")
    print()
    print(f"n = {n}")
    print(f"verifiability:      " + ", ".join(f"{k}={v}" for k, v in sorted(verif_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_precision:  " + ", ".join(f"{k}={v}" for k, v in sorted(locp_counts.items(), key=lambda kv: str(kv[0]))) +
          f"  (of {len(has_locator)} records with a locator; {n - len(has_locator)} explicitly null)")
    print(f"locator_ceiling (scoped to the {len(has_ceiling)} with a known ceiling): " +
          ", ".join(f"{k}={v}" for k, v in sorted(ceiling_counts.items(), key=lambda kv: str(kv[0]))))
    print(f"locator_exhaustive (scoped to the {len(has_ceiling)}, derived not typed): " +
          ", ".join(f"{k}={v}" for k, v in sorted(exhaustive_scoped.items(), key=lambda kv: str(kv[0]))))
    if len(has_ceiling) > len(has_locator):
        print(f"  NOTE: {len(has_ceiling) - len(has_locator)} record(s) have a known locator_ceiling but "
              f"locator_precision still null -- ceiling was recovered from a co-cited sibling (round 31) "
              f"before anyone located this record's own claim in the source.")
    if len(exhaustive_scoped) <= 1 and has_ceiling:
        print(f"  NOTE: locator_exhaustive is a single value within its scope right now. Not a bug by "
              f"itself under round 16's model -- it's arithmetic on locator_precision/locator_ceiling, "
              f"both independently set, so a collapse here means every ceiling-known record's ceiling has "
              f"been found to equal its precision so far, not that the field is secretly redundant.")
    mech = verif_counts.get("mechanised", 0)
    print(f"mechanised: {mech}/{n} = {mech/n*100:.1f}%")

    # Round 32 (dipankarsarkar): a double-quoted span of 40+ characters in
    # summary or source_locator is what "someone opened the source and it
    # matched" looks like written into the record itself, offline, falsifiable
    # by any reader with ctrl-F -- unlike "human-checked" on its own, which the
    # round-28 banana case showed the checker could not tell from an unverified
    # guess. This is informational, not a gate: not carrying one doesn't mean
    # a record wasn't actually checked, only that the evidence wasn't quoted
    # into it. Failing every record without a span would be wrong today, the
    # same way promoting HTTP 200 to a locator rung would have been for a
    # different reason. Tracked here so the count is visible every run instead
    # of rediscovered by hand each round.
    #
    # Round 35: scoped to ALL records, not just unlocated ones. MONARCH's span
    # is what got it promoted to locator_precision="row" this round (see
    # docstring), so it is now both located AND span-carrying -- the first
    # record in this file's history to be both. Scoping the count to unlocated
    # only, as round 32 did, would silently make MONARCH disappear from this
    # print the moment it was fixed, which is backwards: the span didn't stop
    # existing, the record just also gained a locator alongside it.
    span_re = re.compile(r'"([^"]{40,})"')
    span_records = [
        r for r in records
        if span_re.search(r.get("summary") or "") or span_re.search(r.get("source_locator") or "")
    ]
    span_located = sum(1 for r in span_records if r["locator_precision"] is not None)
    print(f"records carrying a 40+-char quoted span (informational, not a gate): "
          f"{len(span_records)}/{n} ({span_located} of those also located)")

    # Round 38 (dipankarsarkar): a computed bound, not an assertion -- see
    # module docstring. Informational, not a gate: an inert rung is not a
    # bug in the anchor, it is an honest statement that no real record has
    # tested it yet.
    exercised = _exercised_chars(records)
    rungs_seen = sorted(c for c in _RUNG_CHARS if c in exercised)
    rungs_inert = sorted(c for c in _RUNG_CHARS if c not in exercised)
    repo_host_n = sum(1 for r in records if _REPO_HOST_RE.search(r.get("citation") or ""))
    located_repo_host_n = sum(
        1 for r in records
        if _REPO_HOST_RE.search(r.get("citation") or "") and r.get("source_locator")
    )
    print(f"anchor rungs the real corpus exercises: {rungs_seen if rungs_seen else '(none)'}")
    print(f"anchor rungs inert on all {n} real records: {rungs_inert}")
    print(f"  (repo-host-cited records: {repo_host_n}; of those with a source_locator: "
          f"{located_repo_host_n} -- only a record in that {located_repo_host_n}-record set "
          f"can move the count above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
