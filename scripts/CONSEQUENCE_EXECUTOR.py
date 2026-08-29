#!/usr/bin/env python3
"""STORED-PLAN Executor — the missing piece named in
HUB_LEGAL_FORENSIC/SYNTAX_AUDIT/PLAN__CONSEQUENCE_PREDICTION_LAYER__2026-08-11.md,
П1/П3 ("вывод из инвентаризации"): no existing Syntaxit component runs in
STORED-PLAN mode, so CONSEQUENCE_GATE_RECHECK.py had nowhere to be called
from. This is that caller, built fresh (not retrofitted) with re-check
mandatory on the way in, per П3's conclusion.

Flow (STORED-PLAN only -- per П3, IMMEDIATE flows don't need this):
    plan = disclose(action)            # snapshot taken now, shown to human
    ... time passes, human approves ...
    result = execute(plan, real_fn)    # snapshot taken again, compared;
                                        # drift -> BLOCKED, re-disclose;
                                        # no drift -> real_fn(action) runs

Every call to execute() logs one append-only feedback event to
consequence_prediction_feedback.jsonl in the exact schema П5 specified,
at the file path П5 reserved -- this is the first thing to write there.
No AI calls anywhere in this module, same principle as its two
dependencies (CONSEQUENCE_GATE_RECHECK.py, ACTION_SEVERITY_CLASSIFIER.py).
"""
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent))
from ACTION_SEVERITY_CLASSIFIER import classify_command
from CONSEQUENCE_GATE_RECHECK import snapshot, compare
from FREQUENCY_PROBABILITY_ESTIMATOR import seeded_frequency_probability_fn

FEEDBACK_LOG = Path(
    "/home/sipa/PROJECT/PAYTON_HUBS/HUB_LEGAL_FORENSIC/SYNTAX_AUDIT/"
    "consequence_prediction_feedback.jsonl"
)


RISK_PROBABILITY_THRESHOLD = 0.5


def risk_action(severity_category: str, probability: float) -> str:
    """Combine severity + probability into one explicit action instead of
    reporting them as two separate numbers a human reconciles by eye
    (architect, 2026-08-29: "не только вероятность нужна, а оценка риска" --
    probability alone was never the right output, risk was).

    Severity dominates for IRREVERSIBLE: no probability, however low, should
    talk anyone into skipping confirmation on something that can't be
    undone -- averaging severity against probability is exactly the mistake
    this refuses to make. REVERSIBLE_COSTLY always asks too, because the
    cost of being wrong is real even when technically reversible.
    REVERSIBLE_CHEAP is the only category where a low predicted probability
    is allowed to skip the prompt and just log -- that's the one place
    probability should actually change the outcome.
    """
    if severity_category == "IRREVERSIBLE":
        return "HARD_STOP"
    if severity_category == "REVERSIBLE_COSTLY":
        return "CONFIRM"
    if probability >= RISK_PROBABILITY_THRESHOLD:
        return "CONFIRM"
    return "LOG_ONLY"


class StalePlanError(Exception):
    """Raised when execute() is called but the pre-execution re-check found
    drift -- the state the plan was disclosed against no longer holds.
    Per П3: never silently run a stale plan, always re-disclose instead."""
    pass


@dataclass
class StoredPlan:
    command: str
    action_scope: dict = field(default_factory=dict)  # {"git_repos": [...], "paths": [...], "network_targets": [...]}
    disclosed_at: float = field(default_factory=time.time)
    snapshot_before: dict = field(default_factory=dict)
    severity: dict = field(default_factory=dict)
    probability: float = 0.5


def disclose(command: str, action_scope: dict) -> StoredPlan:
    """Call this when the plan is shown to the human for approval.
    action_scope names exactly what the plan touches -- git_repos/paths/
    network_targets, same shape CONSEQUENCE_GATE_RECHECK.snapshot() expects.
    This is NOT a full-system dump; scope it to what the command actually names."""
    severity = classify_command(command)
    prob = seeded_frequency_probability_fn(command, depth=0)
    return StoredPlan(
        command=command,
        action_scope=action_scope,
        disclosed_at=time.time(),
        snapshot_before=snapshot(action_scope),
        severity=severity,
        probability=prob,
    )


def _log_feedback(plan: StoredPlan, drift: list[str], status: str) -> None:
    """Append-only per Core Law #5 -- never rewrite, only append. Schema
    exactly as specified in П5 of the plan doc."""
    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "action": plan.command,
        "predicted_severity": plan.severity["category"],
        "predicted_probability": round(plan.probability, 3),
        "drift_detected": bool(drift),
        "drift_details": drift,
        "source": "CONSEQUENCE_GATE_RECHECK",
        "status": status,
    }
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def execute(plan: StoredPlan, real_executor: Callable[[StoredPlan], Any]) -> dict:
    """Call this right before actually running the approved plan.
    Re-snapshots, compares against the disclosure-time snapshot.

    - drift found -> does NOT call real_executor. Logs the block, raises
      StalePlanError. Caller must re-disclose, not retry blindly.
    - no drift -> calls real_executor(plan), logs EXECUTED, returns its
      output wrapped with the audit fields.
    """
    snapshot_after = snapshot(plan.action_scope)
    drift = compare(plan.snapshot_before, snapshot_after)

    if drift:
        _log_feedback(plan, drift, status="BLOCKED_STALE_PLAN")
        raise StalePlanError(
            f"Plan for {plan.command!r} disclosed at {plan.disclosed_at} is stale: "
            f"{'; '.join(drift)}. Re-disclose before executing, do not retry blindly."
        )

    output = real_executor(plan)
    _log_feedback(plan, drift, status="EXECUTED")
    return {
        "command": plan.command,
        "severity": plan.severity["category"],
        "probability": plan.probability,
        "status": "EXECUTED",
        "output": output,
    }


if __name__ == "__main__":
    print("=== TEST 0: risk_action matrix ===")
    assert risk_action("IRREVERSIBLE", 0.01) == "HARD_STOP", "severity must dominate even at near-zero probability"
    assert risk_action("IRREVERSIBLE", 0.99) == "HARD_STOP"
    assert risk_action("REVERSIBLE_COSTLY", 0.01) == "CONFIRM", "costly-to-reverse always confirms regardless of probability"
    assert risk_action("REVERSIBLE_COSTLY", 0.99) == "CONFIRM"
    assert risk_action("REVERSIBLE_CHEAP", 0.99) == "CONFIRM", "high probability still confirms even when cheap to reverse"
    assert risk_action("REVERSIBLE_CHEAP", 0.01) == "LOG_ONLY", "only cell that reaches LOG_ONLY: cheap + unlikely"
    print("PASS: severity dominates IRREVERSIBLE/REVERSIBLE_COSTLY regardless of probability; "
          "only REVERSIBLE_CHEAP + low probability reaches LOG_ONLY")

    # Self-test: VIO-006-shaped scenario, both branches.
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q"], cwd=tmp)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp)
        subprocess.run(["git", "config", "user.name", "t"], cwd=tmp)
        (Path(tmp) / "README.md").write_text("x")
        subprocess.run(["git", "add", "README.md"], cwd=tmp)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp)

        scope = {"git_repos": [tmp]}

        print("=== TEST 1: no drift -> executes ===")
        plan = disclose("git status", scope)
        result = execute(plan, real_executor=lambda p: "ran clean")
        assert result["status"] == "EXECUTED"
        print("PASS:", result)

        print("\n=== TEST 2: drift (untracked file appears) -> blocked, real_executor never called ===")
        plan2 = disclose("rm -rf .", scope)
        (Path(tmp) / "untracked.txt").write_text("surprise")  # state changes after disclosure
        called = []
        try:
            execute(plan2, real_executor=lambda p: called.append(1))
            print("FAIL: should have raised StalePlanError")
        except StalePlanError as e:
            assert not called, "real_executor must NOT run when plan is stale"
            print("PASS (blocked, real_executor never invoked):", e)

        print("\n=== TEST 3: feedback log is append-only and has both events ===")
        lines = FEEDBACK_LOG.read_text().splitlines()
        assert len(lines) >= 2
        last_two = [json.loads(l) for l in lines[-2:]]
        assert last_two[0]["status"] == "EXECUTED"
        assert last_two[1]["status"] == "BLOCKED_STALE_PLAN"
        assert last_two[1]["predicted_severity"] == "IRREVERSIBLE"
        print(f"PASS: {FEEDBACK_LOG} has {len(lines)} total events, last two match expected sequence")

    print("\nALL SELF-TESTS PASSED")
