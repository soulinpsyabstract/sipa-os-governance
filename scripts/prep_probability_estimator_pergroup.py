#!/usr/bin/env python3
"""prep_probability_estimator_pergroup.py -- SFT data prep for the
probability-estimator tune (EXP-046), the first fine-tune attempt at the
P(harmful Y|X,C) half of the project's own Risk(X|C) = P x Impact
architecture (see project_consequence_prediction_architecture.md, memory).
`FREQUENCY_PROBABILITY_ESTIMATOR.py` has existed as a formula/spec, never as
a trained model -- this fills that gap using the two dataset layers already
generated 2026-09-21 (causal_chain_*.jsonl structural chains, probability_*.jsonl
their probability annotations) via Hermes-4-405B, joined by chain_ref.

Specialist-per-group-then-merge convention (EXP-031's own pattern), NOT a
single generalist model like EXP-037/045 -- this dataset has real per-group
volume (200/group across 3 groups: vulnerability, deletion,
sensitive_publication), the same scale EXP-031 used to justify per-group
over generalist.

Input:  DATASETS_CAUSAL_RISK_PIPELINE/causal_chain_<group>.jsonl (id, chain)
        DATASETS_CAUSAL_RISK_PIPELINE/probability_<group>.jsonl (chain_ref,
        probability_estimate, probability_reasoning) -- joined by id==chain_ref.
Output: per_group/<group>_train.jsonl (180), per_group/<group>_eval.jsonl (20,
        every 10th record, never touched by training) -- matches EXP-031's
        176-180/20 split ratio.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "AI_EXPERIMENTS" / "DATASETS_CAUSAL_RISK_PIPELINE"
OUT_DIR = REPO_ROOT / "AI_EXPERIMENTS" / "per_group"
OUT_DIR.mkdir(exist_ok=True)

GROUPS = ["vulnerability", "deletion", "sensitive_publication"]

SYSTEM = (
    "You are a probability estimator for a security-risk pipeline. You will be shown an "
    "initiating action and a causal chain of steps (X -> Y -> Z) leading to a terminal "
    "outcome. Estimate the probability (0.0 to 1.0) that THIS SPECIFIC chain actually "
    "completes to the stated terminal outcome, and give a one-sentence reasoning. Respond "
    "with ONLY a JSON object, no other text: "
    '{"probability_estimate": <float 0.0-1.0>, "probability_reasoning": "<one sentence>"}'
)


def format_chain(action_x: str, chain: list, terminal_outcome: str) -> str:
    steps = "\n".join(f"{c['step']}. ({c['node']}) {c['description']}" for c in chain)
    return f"Initiating action: {action_x}\n\nChain:\n{steps}\n\nTerminal outcome: {terminal_outcome}"


def to_messages(rec: dict, idx: int, group: str) -> dict:
    user_text = format_chain(rec["action_x"], rec["chain"], rec["terminal_outcome"])
    assistant_json = json.dumps({
        "probability_estimate": rec["probability_estimate"],
        "probability_reasoning": rec["probability_reasoning"],
    })
    return {
        "id": rec["chain_ref"],
        "group": group,
        "probability_estimate": rec["probability_estimate"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_json},
        ],
    }


def main():
    for group in GROUPS:
        chains = {c["id"]: c for c in (json.loads(l) for l in open(DATA_DIR / f"causal_chain_{group}.jsonl"))}
        probs = [json.loads(l) for l in open(DATA_DIR / f"probability_{group}.jsonl")]

        joined = []
        for p in probs:
            chain_rec = chains.get(p["chain_ref"])
            if chain_rec is None:
                print(f"  WARNING: {p['chain_ref']} has no matching causal_chain record, skipping")
                continue
            joined.append({**p, "chain": chain_rec["chain"]})

        eval_recs = joined[9::10]
        train_recs = [r for r in joined if r not in eval_recs]

        train_out = OUT_DIR / f"{group}_train.jsonl"
        eval_out = OUT_DIR / f"{group}_eval.jsonl"
        with open(train_out, "w", encoding="utf-8") as f:
            for i, r in enumerate(train_recs):
                f.write(json.dumps(to_messages(r, i, group), ensure_ascii=False) + "\n")
        with open(eval_out, "w", encoding="utf-8") as f:
            for i, r in enumerate(eval_recs):
                f.write(json.dumps(to_messages(r, i, group), ensure_ascii=False) + "\n")

        print(f"[{group}] train={len(train_recs)} eval={len(eval_recs)} -> {train_out.name}, {eval_out.name}")


if __name__ == "__main__":
    main()
