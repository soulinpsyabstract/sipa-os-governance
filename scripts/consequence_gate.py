#!/usr/bin/env python3
"""consequence_gate — CLI wrapper that actually connects CONSEQUENCE_EXECUTOR.py
to a real command instead of leaving it as an unused library.

This is the honest answer to "wire everything up": no live Syntaxit daemon
runs in STORED-PLAN mode (П3's inventory), so there was nowhere automatic
to plug this in. What DOES exist right now is a human (or another Claude
session) about to run a risky shell command by hand -- this gives that
moment a real disclose -> pause -> re-check -> execute path instead of
running blind.

Usage:
    consequence_gate.py "rm -rf /home/sipa/apps/old-project" \\
        --git-repo /home/sipa/apps/old-project

    consequence_gate.py "git filter-repo --force --path secret.txt" \\
        --git-repo /home/sipa/PROJECT/PAYTON_HUBS

Flow:
    1. disclose(command, scope) -- classifies severity, estimates
       probability, snapshots current state.
    2. Prints severity/probability/scope to the human. For IRREVERSIBLE,
       requires typing the literal word "yes" (not just Enter/y) --
       matches the weight of what's being confirmed.
    3. On confirm: re-snapshots, compares. Drift since step 1 -> refuses
       to run, tells you to re-run this tool fresh (do not blindly retry).
       No drift -> actually runs the command via subprocess.
    4. Every outcome (executed or blocked) is logged to
       consequence_prediction_feedback.jsonl via CONSEQUENCE_EXECUTOR.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from CONSEQUENCE_EXECUTOR import disclose, execute, StalePlanError


def run_real_command(plan) -> dict:
    result = subprocess.run(plan.command, shell=True, capture_output=True, text=True)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", help="the shell command to run, as a single string")
    ap.add_argument("--git-repo", action="append", default=[], dest="git_repos",
                     help="git repo this command touches (repeatable)")
    ap.add_argument("--path", action="append", default=[], dest="paths",
                     help="specific file/dir this command touches (repeatable)")
    ap.add_argument("--network-target", action="append", default=[], dest="network_targets",
                     help="remote IP this command's transport depends on (repeatable)")
    ap.add_argument("--yes", action="store_true",
                     help="skip the interactive confirmation (for scripted/non-interactive use -- "
                          "use sparingly, the pause is the point for IRREVERSIBLE commands)")
    args = ap.parse_args()

    scope = {"git_repos": args.git_repos, "paths": args.paths, "network_targets": args.network_targets}
    if not any(scope.values()):
        print("[consequence_gate] WARNING: no --git-repo/--path/--network-target given -- "
              "drift re-check has nothing scoped to compare, it will always report 'no drift'. "
              "This gate is only as good as the scope you tell it about.", file=sys.stderr)

    plan = disclose(args.command, scope)

    print(f"\n[consequence_gate] command : {plan.command}")
    print(f"[consequence_gate] severity: {plan.severity['category']} ({plan.severity['rationale']})")
    print(f"[consequence_gate] est. probability of bad outcome: {plan.probability:.2f} "
          f"(seed-data frequency estimate, not a calibrated model)")
    print(f"[consequence_gate] scope   : {scope}")

    if not args.yes:
        if plan.severity["category"] == "IRREVERSIBLE":
            resp = input('\n[consequence_gate] IRREVERSIBLE. Type "yes" (not just Enter) to proceed: ')
            if resp.strip() != "yes":
                print("[consequence_gate] Aborted, nothing ran.")
                return 1
        else:
            resp = input("\n[consequence_gate] Proceed? [y/N]: ")
            if resp.strip().lower() != "y":
                print("[consequence_gate] Aborted, nothing ran.")
                return 1

    try:
        result = execute(plan, real_executor=run_real_command)
    except StalePlanError as e:
        print(f"\n[consequence_gate] BLOCKED — state changed since disclosure: {e}")
        print("[consequence_gate] Re-run this tool fresh. Do not retry blindly.")
        return 2

    out = result["output"]
    if out["stdout"]:
        print(out["stdout"], end="")
    if out["stderr"]:
        print(out["stderr"], end="", file=sys.stderr)
    print(f"\n[consequence_gate] EXECUTED, exit code {out['returncode']}")
    return out["returncode"]


if __name__ == "__main__":
    sys.exit(main())
