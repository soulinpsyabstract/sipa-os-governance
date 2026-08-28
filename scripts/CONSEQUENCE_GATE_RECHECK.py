#!/usr/bin/env python3
"""Deterministic pre-execution re-check — no AI calls anywhere in this module.

Per HUB_LEGAL_FORENSIC/SYNTAX_AUDIT/PLAN__CONSEQUENCE_PREDICTION_LAYER__2026-08-11.md, П1:
the component that re-verifies a predicted consequence-graph right before execution
must not itself be an LLM call, or it inherits the same fabrication risk it's meant
to catch. This module only reads real system state (git, filesystem, network route)
and diffs two snapshots — no interpretation, no judgment calls.

Usage pattern (STORED-PLAN flows only, per П3):
    before = snapshot(action)          # taken when the plan is disclosed to the human
    ... time passes, human approves ...
    after = snapshot(action)           # taken right before Executor runs it
    drift = compare(before, after)
    if drift:
        # do not execute — re-disclose, do not silently proceed on a stale plan
        ...
"""
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception as e:
        return f"__ERROR__:{e}"


def snapshot_git(repo_path: str) -> dict:
    status = _run(["git", "status", "--short"], cwd=repo_path)
    untracked = [line[3:] for line in status.splitlines() if line.startswith("??")]
    modified = [line[3:] for line in status.splitlines() if line[:2].strip() in ("M", "MM", "AM")]
    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_path)
    return {
        "repo": repo_path,
        "head": head,
        "untracked_count": len(untracked),
        "untracked_sample": untracked[:20],
        "modified": modified,
    }


def snapshot_path(path: str) -> dict:
    p = Path(path)
    exists = p.exists()
    return {
        "path": str(p),
        "exists": exists,
        "is_dir": p.is_dir() if exists else None,
        "mtime": p.stat().st_mtime if exists else None,
    }


def snapshot_network_route(remote_ip: str) -> dict:
    route = _run(["ip", "route", "get", remote_ip])
    return {"remote_ip": remote_ip, "route": route}


def snapshot(action: dict) -> dict:
    """action = {"git_repos": [...], "paths": [...], "network_targets": [...]}
    Only include what the proposed action actually touches — this is not a
    full-system dump, it's scoped to the specific objects named in the plan."""
    return {
        "git": [snapshot_git(r) for r in action.get("git_repos", [])],
        "paths": [snapshot_path(p) for p in action.get("paths", [])],
        "network": [snapshot_network_route(ip) for ip in action.get("network_targets", [])],
    }


def compare(before: dict, after: dict) -> list[str]:
    """Returns human-readable drift warnings. Empty list = state unchanged, safe to proceed.
    Any non-empty result means: do not execute the stale plan, re-disclose instead."""
    warnings = []

    for b, a in zip(before.get("git", []), after.get("git", [])):
        if b["head"] != a["head"]:
            warnings.append(f"DRIFT git {b['repo']}: HEAD {b['head'][:8]} -> {a['head'][:8]}")
        if b["untracked_count"] != a["untracked_count"]:
            warnings.append(
                f"DRIFT git {b['repo']}: untracked count {b['untracked_count']} -> {a['untracked_count']}"
            )
        if b["modified"] != a["modified"]:
            warnings.append(f"DRIFT git {b['repo']}: modified-file set changed")

    for b, a in zip(before.get("paths", []), after.get("paths", [])):
        if b["exists"] != a["exists"]:
            warnings.append(f"DRIFT path {b['path']}: exists {b['exists']} -> {a['exists']}")
        elif b["exists"] and b["mtime"] != a["mtime"]:
            warnings.append(f"DRIFT path {b['path']}: modified since snapshot")

    for b, a in zip(before.get("network", []), after.get("network", [])):
        if b["route"] != a["route"]:
            warnings.append(f"DRIFT network {b['remote_ip']}: route changed")

    return warnings


if __name__ == "__main__":
    import sys

    repo = sys.argv[1] if len(sys.argv) > 1 else "/home/sipa/PROJECT/PAYTON_HUBS"
    action = {"git_repos": [repo]}
    s1 = snapshot(action)
    s2 = snapshot(action)
    drift = compare(s1, s2)
    print(f"snapshot 1: {s1}")
    print(f"snapshot 2: {s2}")
    print(f"drift: {drift if drift else 'none (identical snapshots, self-test pass)'}")
