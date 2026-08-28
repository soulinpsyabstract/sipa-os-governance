#!/usr/bin/env python3
"""Real pytest coverage for CONSEQUENCE_EXECUTOR.py -- against the actual
modules (ACTION_SEVERITY_CLASSIFIER, CONSEQUENCE_GATE_RECHECK,
FREQUENCY_PROBABILITY_ESTIMATOR), not the Gemini reinvention this replaces.

Run: cd /home/sipa/bin && pytest test_CONSEQUENCE_EXECUTOR.py -v
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from CONSEQUENCE_EXECUTOR import disclose, execute, StalePlanError, FEEDBACK_LOG


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "README.md").write_text("x")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def _feedback_tail(n=1):
    lines = FEEDBACK_LOG.read_text().splitlines()
    return [json.loads(l) for l in lines[-n:]]


def test_no_drift_executes(git_repo):
    plan = disclose("git status", {"git_repos": [str(git_repo)]})
    result = execute(plan, real_executor=lambda p: "ok")
    assert result["status"] == "EXECUTED"
    assert result["output"] == "ok"


def test_untracked_file_appearing_between_disclose_and_execute_blocks(git_repo):
    plan = disclose("rm -rf .", {"git_repos": [str(git_repo)]})
    (git_repo / "surprise.txt").write_text("appeared after disclosure")
    with pytest.raises(StalePlanError):
        execute(plan, real_executor=lambda p: pytest.fail("real_executor must not run"))


def test_real_executor_never_called_when_stale(git_repo):
    plan = disclose("rm -rf .", {"git_repos": [str(git_repo)]})
    (git_repo / "surprise.txt").write_text("x")
    called = []
    try:
        execute(plan, real_executor=lambda p: called.append(True))
    except StalePlanError:
        pass
    assert called == [], "real_executor ran despite detected drift -- the whole point of the gate"


def test_head_change_between_disclose_and_execute_blocks(git_repo):
    plan = disclose("git filter-repo --force", {"git_repos": [str(git_repo)]})
    (git_repo / "another.txt").write_text("x")
    subprocess.run(["git", "add", "another.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=git_repo, check=True)
    with pytest.raises(StalePlanError):
        execute(plan, real_executor=lambda p: None)


def test_modified_tracked_file_between_disclose_and_execute_blocks(git_repo):
    plan = disclose("git reset --hard", {"git_repos": [str(git_repo)]})
    (git_repo / "README.md").write_text("changed after disclosure")
    with pytest.raises(StalePlanError):
        execute(plan, real_executor=lambda p: None)


def test_feedback_log_is_append_only_never_shrinks(git_repo):
    before = len(FEEDBACK_LOG.read_text().splitlines()) if FEEDBACK_LOG.exists() else 0
    plan = disclose("git status", {"git_repos": [str(git_repo)]})
    execute(plan, real_executor=lambda p: "ok")
    after = len(FEEDBACK_LOG.read_text().splitlines())
    assert after == before + 1, "each execute() call must append exactly one line, never rewrite the file"


def test_feedback_event_schema_matches_plan_p5(git_repo):
    plan = disclose("git status", {"git_repos": [str(git_repo)]})
    execute(plan, real_executor=lambda p: "ok")
    event = _feedback_tail(1)[0]
    required_keys = {"ts", "action", "predicted_severity", "predicted_probability",
                      "drift_detected", "drift_details", "source"}
    assert required_keys.issubset(event.keys()), f"missing keys: {required_keys - event.keys()}"
    assert event["source"] == "CONSEQUENCE_GATE_RECHECK"


def test_blocked_event_logs_irreversible_severity_for_vio006_shaped_command(git_repo):
    plan = disclose("rm -rf .", {"git_repos": [str(git_repo)]})
    (git_repo / "x.txt").write_text("x")
    with pytest.raises(StalePlanError):
        execute(plan, real_executor=lambda p: None)
    event = _feedback_tail(1)[0]
    assert event["predicted_severity"] == "IRREVERSIBLE"
    assert event["status"] == "BLOCKED_STALE_PLAN"


def test_executed_event_carries_correct_severity_for_safe_command(git_repo):
    plan = disclose("git commit -am 'draft'", {"git_repos": [str(git_repo)]})
    execute(plan, real_executor=lambda p: "committed")
    event = _feedback_tail(1)[0]
    assert event["predicted_severity"] == "REVERSIBLE_CHEAP"
    assert event["status"] == "EXECUTED"


def test_no_drift_when_repo_genuinely_unchanged(git_repo):
    plan = disclose("git log", {"git_repos": [str(git_repo)]})
    result = execute(plan, real_executor=lambda p: "logged")
    assert result["status"] == "EXECUTED"
    event = _feedback_tail(1)[0]
    assert event["drift_detected"] is False
    assert event["drift_details"] == []
