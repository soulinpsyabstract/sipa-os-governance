#!/usr/bin/env python3
"""Deterministic obratimo/neobratimo (reversibility) classifier — no AI calls.

Per HUB_LEGAL_FORENSIC/SYNTAX_AUDIT/PLAN__CONSEQUENCE_PREDICTION_LAYER__2026-08-11.md, П2:
without a programmatic severity classifier there's nothing to drive branch-pruning (П4)
or to decide which steps get visually flagged in disclosure. Same "no AI in the judgment
path" principle as CONSEQUENCE_GATE_RECHECK.py (П1) — a classifier an LLM can talk its way
around is not a safety mechanism.

Three categories, derived directly from the three real incidents in CLAUDE.md's
AI_VIOLATIONS_LOG rather than invented in the abstract:
  IRREVERSIBLE        — VIO-001 (killed the live tunnel), VIO-006 (rm -rf untracked files)
  REVERSIBLE_COSTLY   — VIO-007 (git filter-repo — recoverable via reflog/backup, but
                         expensive and easy to get wrong under time pressure)
  REVERSIBLE_CHEAP     — editing a draft, a local uncommitted change with a clean git repo

Unknown/unmatched commands default to REVERSIBLE_COSTLY, not REVERSIBLE_CHEAP —
fail toward caution, not toward silence.
"""
import re

IRREVERSIBLE = "IRREVERSIBLE"
REVERSIBLE_COSTLY = "REVERSIBLE_COSTLY"
REVERSIBLE_CHEAP = "REVERSIBLE_CHEAP"

# (pattern, category, rationale) — checked in order, first match wins
RULES: list[tuple[str, str, str]] = [
    (r"\brm\s+.*-[a-z]*r[a-z]*f|\brm\s+.*-[a-z]*f[a-z]*r", IRREVERSIBLE,
     "recursive force delete — matches VIO-006 pattern (untracked files have no git backup)"),
    (r"\bgit\s+clean\s+.*-[a-z]*f[a-z]*d|\bgit\s+clean\s+.*-[a-z]*d[a-z]*f", IRREVERSIBLE,
     "git clean -fd removes untracked files/dirs permanently, same class as VIO-006"),
    (r"\bip\s+(link|tunnel)\s+.*\bdel\b|\bip\s+link\s+set\s+\S+\s+down", IRREVERSIBLE,
     "network interface/tunnel teardown — matches VIO-001 pattern (may sever the active session)"),
    (r"zerotier-cli\s+leave|systemctl\s+(stop|disable)\s+.*zerotier", IRREVERSIBLE,
     "ZeroTier teardown — direct VIO-001 case, RED LINE in CLAUDE.md"),
    (r"\bgit\s+filter-repo\b|\bgit\s+filter-branch\b", REVERSIBLE_COSTLY,
     "history rewrite — matches VIO-007 pattern; recoverable via reflog/backup but resets working tree"),
    (r"\bgit\s+reset\s+.*--hard\b", REVERSIBLE_COSTLY,
     "hard reset discards uncommitted tracked changes — recoverable only if committed elsewhere"),
    (r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b", REVERSIBLE_COSTLY,
     "force push rewrites remote history — recoverable from local reflog, not from remote alone"),
    (r"\bgit\s+rebase\b", REVERSIBLE_COSTLY,
     "rebase rewrites commit history — recoverable via reflog but easy to lose track of"),
    (r"\bdrop\s+table\b|\btruncate\s+table\b", IRREVERSIBLE,
     "SQL destructive DDL/DML without a stated backup"),
]

SAFE_HINTS = [
    r"^git\s+add\b", r"^git\s+commit\b", r"^git\s+status\b", r"^git\s+diff\b",
    r"^cat\b", r"^ls\b", r"^echo\b", r"^cp\b(?!.*-r.*-f)",
]


def classify_command(cmd: str, context: dict | None = None) -> dict:
    """cmd = the literal shell command (or equivalent action description) under review.
    context = optional dict from CONSEQUENCE_GATE_RECHECK.snapshot(), e.g. to check
    whether the target path actually has untracked files before calling something IRREVERSIBLE."""
    cmd = cmd.strip()

    for pattern, category, rationale in RULES:
        if re.search(pattern, cmd, re.IGNORECASE):
            result = {"command": cmd, "category": category, "rationale": rationale}
            if context and category == IRREVERSIBLE:
                untracked = sum(g.get("untracked_count", 0) for g in context.get("git", []))
                if untracked:
                    result["context_note"] = f"{untracked} untracked files in scope — confirms real exposure"
            return result

    for pattern in SAFE_HINTS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return {"command": cmd, "category": REVERSIBLE_CHEAP,
                     "rationale": "matches known-safe pattern (read-only or git-tracked staging)"}

    return {"command": cmd, "category": REVERSIBLE_COSTLY,
            "rationale": "no matching rule — defaulting to caution, not to silence"}


if __name__ == "__main__":
    tests = [
        ("rm -rf /home/sipa/apps/sipa-ai-app-lovable", IRREVERSIBLE, "VIO-006"),
        ("git filter-repo --force --path CLAUDE.md", REVERSIBLE_COSTLY, "VIO-007"),
        ("zerotier-cli leave 1d71939404e4dfce", IRREVERSIBLE, "VIO-001"),
        ("git commit -am 'draft update'", REVERSIBLE_CHEAP, "safe baseline"),
        ("some totally novel command nobody wrote a rule for", REVERSIBLE_COSTLY, "unknown default"),
    ]
    print("VIO-log validation:")
    all_pass = True
    for cmd, expected, label in tests:
        r = classify_command(cmd)
        ok = r["category"] == expected
        all_pass &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {cmd!r} -> {r['category']} ({r['rationale']})")
    print("ALL PASS" if all_pass else "SOME FAILED")
