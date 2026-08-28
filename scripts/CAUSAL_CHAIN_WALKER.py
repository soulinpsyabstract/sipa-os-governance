#!/usr/bin/env python3
"""Causal-chain branch pruning — П4.

Per PLAN__CONSEQUENCE_PREDICTION_LAYER__2026-08-11.md: a full 10-step enumeration
across multiple candidate actions (A/B/C) grows exponentially and becomes both
computationally expensive and unreadable for human disclosure. This module is the
deterministic tree-walk + pruning mechanism SIPA can build without waiting on
Rabbit's probability engine — branches scoring probability x severity below a
threshold get collapsed into a single summary node instead of expanded further.

Where a real probability is needed, this calls a pluggable `probability_fn`.
`stub_probability_fn` below is the ORIGINAL PLACEHOLDER (flat 0.5) — kept for
tests that want a deliberately uninformative baseline. The default used by
walk_and_prune() is now `seeded_frequency_probability_fn` from
FREQUENCY_PROBABILITY_ESTIMATOR.py, ported 2026-08-12 from the live
Consequence Engine Base44 app (calc-the-consequence.base44.app, built for
the platform's "One Prompt Challenge") — verified byte-faithful against the
live app's own displayed math during Playwright testing. This is still a
seed-data estimator, not a live-calibrated one (no real feedback log has
enough variance yet — see check_data_diversity() in that module), and it is
NOT Rabbit's engine; the seam for Rabbit's engine per
project_adam_shibli_rabbit_partnership.md (SIPA = graph + severity, Rabbit =
probability) is unchanged — any probability_fn can still be swapped in.
Presenting either function as more than what it is would repeat the
overclaim risk flagged under П6.
"""
import json
from dataclasses import dataclass, field
from typing import Callable

from ACTION_SEVERITY_CLASSIFIER import classify_command, IRREVERSIBLE, REVERSIBLE_COSTLY, REVERSIBLE_CHEAP
from FREQUENCY_PROBABILITY_ESTIMATOR import seeded_frequency_probability_fn

SEVERITY_WEIGHT = {IRREVERSIBLE: 1.0, REVERSIBLE_COSTLY: 0.5, REVERSIBLE_CHEAP: 0.1}


@dataclass
class ChainNode:
    action: str
    children: list["ChainNode"] = field(default_factory=list)


def stub_probability_fn(action: str, depth: int) -> float:
    """PLACEHOLDER — not a real prediction, returns a flat 0.5 for everything.
    Kept for tests that want a deliberately uninformative baseline; no longer
    the default (see seeded_frequency_probability_fn, imported above)."""
    return 0.5


def score(action: str, probability_fn: Callable[[str, int], float], depth: int) -> float:
    severity = classify_command(action)["category"]
    weight = SEVERITY_WEIGHT[severity]
    prob = probability_fn(action, depth)
    return prob * weight


def walk_and_prune(root: ChainNode, probability_fn: Callable[[str, int], float] = seeded_frequency_probability_fn,
                    threshold: float = 0.3, max_depth: int = 10, depth: int = 0) -> dict:
    """Returns a pruned tree as nested dicts. depth counts down from the root;
    max_depth=10 matches the operator's "up to 10 steps" framing."""
    node_score = score(root.action, probability_fn, depth)
    result = {
        "action": root.action,
        "score": round(node_score, 3),
        "severity": classify_command(root.action)["category"],
    }

    if depth >= max_depth or not root.children:
        result["children"] = []
        return result

    kept, collapsed = [], 0
    for child in root.children:
        child_score = score(child.action, probability_fn, depth + 1)
        if child_score >= threshold:
            kept.append(walk_and_prune(child, probability_fn, threshold, max_depth, depth + 1))
        else:
            collapsed += 1

    result["children"] = kept
    if collapsed:
        result["collapsed_low_risk_branches"] = collapsed
    return result


if __name__ == "__main__":
    # VIO-006-shaped example: rm -rf branches into a real-loss outcome vs a recoverable one
    tree = ChainNode("rm -rf /home/sipa/apps/target-dir", children=[
        ChainNode("1798 untracked files permanently lost", children=[]),
        ChainNode("git history intact on remote (recoverable)", children=[]),
    ])

    def biased_stub(action, depth):
        # crude test-only probability: outcomes described as "lost" score high, others low
        return 0.9 if "lost" in action else 0.1

    pruned = walk_and_prune(tree, probability_fn=biased_stub, threshold=0.3)
    print(json.dumps(pruned, indent=2, ensure_ascii=False))

    kept_actions = [c["action"] for c in pruned["children"]]
    assert "1798 untracked files permanently lost" in kept_actions, "high-risk branch must survive pruning"
    assert "git history intact on remote (recoverable)" not in kept_actions, "low-risk branch must be pruned"
    assert pruned.get("collapsed_low_risk_branches") == 1
    print("\nPASS: high-severity branch kept, low-risk branch collapsed as expected")
