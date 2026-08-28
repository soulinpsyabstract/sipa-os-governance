#!/usr/bin/env python3
"""Frequency-based probability estimator — self-built fallback for
CAUSAL_CHAIN_WALKER.probability_fn, per operator's "то что можем сами делаем" (2026-08-11).

No AI calls — computes P(bad_outcome | action_pattern) empirically from an append-only
feedback log (same shape as binary-gate-dryrun-verdicts.jsonl / the future
consequence_prediction_feedback.jsonl from П5 of PLAN__CONSEQUENCE_PREDICTION_LAYER).
This is the SIPA-buildable half of probability estimation if the Rabbit partnership
doesn't happen — see project_adam_shibli_rabbit_partnership.md fallback discussion.

HONEST FINDING (2026-08-11, live check): binary-gate-dryrun-verdicts.jsonl (2286+
events) is NOT usable as a calibration source as-is. 2286/2289 entries are "fail"
with the identical reason "No proof indicators found. Cannot verify truth." — a
99.87% constant outcome. A frequency estimator trained on a near-constant signal
produces no discrimination between action patterns. This looks like a separate
miscalibration in binary-gate's own validator.py (too strict on ordinary
conversational answers lacking a "source:" marker), not evidence that 99.87% of
real agent actions are actually bad. check_data_diversity() below exists specifically
to catch this class of problem before trusting any frequency table built from it —
flagging it rather than pretending the dataset is calibration-ready.
"""
import json
from collections import defaultdict
from pathlib import Path

# Seed frequency table — ported verbatim (same action types, same
# occurrences/total counts) from the live Consequence Engine Base44 app
# (calc-the-consequence.base44.app, built 2026-08-12 for the platform's
# "One Prompt Challenge"). This is real seed data, not a live-calibrated
# feedback log — it exists so action-type probability has an honest,
# non-arbitrary starting point before binary-gate-dryrun-verdicts.jsonl
# (or any other real log) has enough variance to calibrate from directly
# (see check_data_diversity() above — that source is currently unusable).
SEED_ACTION_OUTCOMES = [
    {"actionType": "delete", "outcome": "data loss", "occurrences": 8, "total": 10, "negative": True},
    {"actionType": "delete", "outcome": "no effect (backup existed)", "occurrences": 2, "total": 10, "negative": False},
    {"actionType": "drop", "outcome": "schema lost", "occurrences": 7, "total": 9, "negative": True},
    {"actionType": "drop", "outcome": "recovered from snapshot", "occurrences": 2, "total": 9, "negative": False},
    {"actionType": "force push", "outcome": "teammate lost commits", "occurrences": 6, "total": 11, "negative": True},
    {"actionType": "force push", "outcome": "clean rewrite, no harm", "occurrences": 5, "total": 11, "negative": False},
    {"actionType": "rm -rf", "outcome": "wrong directory deleted", "occurrences": 5, "total": 6, "negative": True},
    {"actionType": "rm -rf", "outcome": "intended target only", "occurrences": 1, "total": 6, "negative": False},
    {"actionType": "deploy", "outcome": "production incident", "occurrences": 9, "total": 24, "negative": True},
    {"actionType": "deploy", "outcome": "smooth rollout", "occurrences": 15, "total": 24, "negative": False},
    {"actionType": "send", "outcome": "sent to wrong recipients", "occurrences": 4, "total": 18, "negative": True},
    {"actionType": "send", "outcome": "delivered as intended", "occurrences": 14, "total": 18, "negative": False},
    {"actionType": "publish", "outcome": "public error noticed", "occurrences": 3, "total": 16, "negative": True},
    {"actionType": "publish", "outcome": "fine", "occurrences": 13, "total": 16, "negative": False},
    {"actionType": "merge", "outcome": "broken main branch", "occurrences": 7, "total": 20, "negative": True},
    {"actionType": "merge", "outcome": "clean integration", "occurrences": 13, "total": 20, "negative": False},
    {"actionType": "email", "outcome": "reply-all storm", "occurrences": 2, "total": 12, "negative": True},
    {"actionType": "email", "outcome": "normal thread", "occurrences": 10, "total": 12, "negative": False},
    {"actionType": "test", "outcome": "flaky false alarm", "occurrences": 3, "total": 14, "negative": True},
    {"actionType": "test", "outcome": "caught bug early", "occurrences": 11, "total": 14, "negative": False},
    {"actionType": "preview", "outcome": "no impact", "occurrences": 0, "total": 8, "negative": False},
    {"actionType": "save draft", "outcome": "no impact", "occurrences": 0, "total": 9, "negative": False},
]

# Same order-sensitive keyword list as the live app's SN array — order
# matters because the first substring match wins (e.g. "force push"
# would otherwise also match a hypothetical bare "push" entry first).
ACTION_TYPE_KEYWORDS = [
    "delete", "drop", "rm -rf", "force push", "destroy", "wipe", "purge",
    "truncate", "overwrite", "format", "deploy", "publish", "send", "email",
    "merge", "push", "commit", "test", "preview", "save draft", "draft", "edit",
]


def estimate_action_type_probability(action: str, seed: list[dict] = SEED_ACTION_OUTCOMES,
                                      min_total: int = 5) -> dict:
    """Ports Ov() from the Consequence Engine verbatim: filter seed entries whose
    actionType is a substring of the (lowercased) action text, sum
    occurrences/total across all matches, return the negative-outcome ratio.
    sufficient=False (and probability=None) below min_total observations —
    mirrors the live app's own "insufficient data" guard."""
    lowered = (action or "").lower()
    entries = [e for e in seed if e["actionType"] in lowered]
    total = sum(e["total"] for e in entries)
    negative = sum(e["occurrences"] for e in entries if e["negative"])
    sufficient = total >= min_total
    return {
        "sufficient": sufficient,
        "probability": (negative / total) if sufficient and total else None,
        "matched_entries": [e["actionType"] for e in entries],
        "negative_occ": negative,
        "total_occ": total,
    }


def load_feedback_events(path: str) -> list[dict]:
    events = []
    p = Path(path)
    if not p.exists():
        return events
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def check_data_diversity(events: list[dict], outcome_key: str) -> dict:
    """Before trusting frequency counts, check whether the outcome signal actually
    varies. A near-constant outcome means the source reflects a different problem
    (e.g. an over-strict upstream validator) rather than real variance in risk."""
    counts = defaultdict(int)
    for e in events:
        counts[e.get(outcome_key)] += 1
    total = sum(counts.values())
    if total == 0:
        return {"usable": False, "total": 0, "reason": "no data"}
    dominant_frac = max(counts.values()) / total
    if total < 20:
        return {"usable": False, "total": total, "distribution": dict(counts),
                "reason": "fewer than 20 events — too little data"}
    usable = dominant_frac < 0.95
    return {
        "usable": usable,
        "total": total,
        "distribution": dict(counts),
        "dominant_fraction": round(dominant_frac, 4),
        "reason": None if usable else
                  f"outcome is {dominant_frac:.1%} single value — not enough variance to calibrate on",
    }


def build_frequency_table(events: list[dict], pattern_key: str, outcome_key: str, bad_value) -> dict:
    """Returns {pattern: P(outcome == bad_value)} from accumulated events."""
    totals = defaultdict(int)
    bad = defaultdict(int)
    for e in events:
        pattern = e.get(pattern_key)
        if pattern is None:
            continue
        totals[pattern] += 1
        if e.get(outcome_key) == bad_value:
            bad[pattern] += 1
    return {p: bad[p] / totals[p] for p in totals}


def make_probability_fn(events: list[dict], pattern_key: str = "from",
                         outcome_key: str = "verdict", bad_value: str = "fail",
                         fallback: float = 0.5):
    """Returns a probability_fn compatible with CAUSAL_CHAIN_WALKER.walk_and_prune().
    fallback is returned for any pattern never seen in the training events —
    unknown defaults to uncertain (0.5), not to false confidence in either direction."""
    table = build_frequency_table(events, pattern_key, outcome_key, bad_value)

    def probability_fn(action: str, depth: int) -> float:
        return table.get(action, fallback)

    return probability_fn


def seeded_frequency_probability_fn(action: str, depth: int, fallback: float = 0.5) -> float:
    """A ready-to-use probability_fn for CAUSAL_CHAIN_WALKER.walk_and_prune(),
    backed by estimate_action_type_probability() (the ported Consequence
    Engine seed table) instead of a flat placeholder. Falls back to 0.5
    (uncertain) for unmatched action types or insufficient data — never to
    false confidence. depth is accepted for signature compatibility but
    unused, matching stub_probability_fn's own behavior."""
    result = estimate_action_type_probability(action)
    if not result["sufficient"] or result["probability"] is None:
        return fallback
    return result["probability"]


if __name__ == "__main__":
    events = load_feedback_events("/home/sipa/SYNTAX_CHANNEL/logs/binary-gate-dryrun-verdicts.jsonl")
    diversity = check_data_diversity(events, "verdict")
    print(f"Data diversity check on binary-gate-dryrun-verdicts.jsonl ({len(events)} events):")
    print(json.dumps(diversity, indent=2))

    if not diversity["usable"]:
        print(f"\nNOT calibrating from this source: {diversity['reason']}")
        print("Validating the estimator code itself against synthetic VIO-shaped data instead:\n")

    synthetic = (
        [{"pattern": "rm -rf untracked-dir", "outcome": "bad"} for _ in range(9)]
        + [{"pattern": "rm -rf untracked-dir", "outcome": "ok"} for _ in range(1)]
        + [{"pattern": "git commit", "outcome": "ok"} for _ in range(10)]
    )
    prob_fn = make_probability_fn(synthetic, pattern_key="pattern", outcome_key="outcome", bad_value="bad")
    p_destructive = prob_fn("rm -rf untracked-dir", 0)
    p_safe = prob_fn("git commit", 0)
    p_unseen = prob_fn("some never-seen command", 0)
    print(f"P(bad | 'rm -rf untracked-dir') = {p_destructive}  (expect ~0.9)")
    print(f"P(bad | 'git commit') = {p_safe}  (expect 0.0)")
    print(f"P(bad | unseen pattern) = {p_unseen}  (expect fallback 0.5)")
    assert abs(p_destructive - 0.9) < 1e-9
    assert p_safe == 0.0
    assert p_unseen == 0.5
    print("\nPASS: estimator correctly discriminates when the underlying data has real variance")

    print("\nSeed-table estimator (ported from Consequence Engine, real numbers not synthetic):")
    for probe in ["delete this production database", "save a draft of the email", "some never-seen command"]:
        r = estimate_action_type_probability(probe)
        print(f"  {probe!r} -> {r}")
    # NOTE: both the "negative" and "non-negative" rows for a given actionType
    # carry the SAME total count (that's how the seed data — and the live
    # app's own summing logic — is shaped), so matching 2 rows sums total
    # twice. 8/20=0.4 here, not 8/10 — verified against the live app's own
    # displayed math (0.40 base probability) during Playwright testing.
    assert estimate_action_type_probability("delete this production database")["probability"] == 8 / 20
    assert estimate_action_type_probability("save a draft of the email")["probability"] == 2 / 24
    assert estimate_action_type_probability("some never-seen command")["sufficient"] is False
    assert seeded_frequency_probability_fn("delete the users table", depth=0) == 8 / 20
    assert seeded_frequency_probability_fn("some never-seen command", depth=0) == 0.5
    print("PASS: seed-table estimator matches the live Consequence Engine app's own numbers")
