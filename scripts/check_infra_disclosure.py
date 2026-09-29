#!/usr/bin/env python3
"""check_infra_disclosure.py -- automated architecture-disclosure gate.

2026-09-29, architect's own finding, live in chat: this repo's forensic-
transparency principle ("PUBLIC package (demo/preview) != OPERATOR artifacts
(private/canonical)", HUB_CORE_CANON/CLAUDE.md IP & LEGAL PROTECTION section)
has always been enforced by memory and manual judgment at commit time, same
as every other repo under soulinpsyabstract/* on GitHub. check_citations.py
and check_dataset_citations.py exist because "I checked" turned out not to be
a reliable substitute for a script that checks the same thing every time --
this is that same fix applied to a different class of leak: not a secret
VALUE (detect-secrets, git-secrets, and this session's own detect-secrets
pass already cover that), but architecture TOPOLOGY -- ZeroTier overlay IPs,
the SSH port used for the two phone nodes, named Cloudflare account tokens,
and absolute paths that reveal the private canon's directory layout. None of
that is a credential a rotation fixes; all of it is reconnaissance a
bad-faith reader (human or agentic, see this session's GPT-6.1 Sol
discussion) gets for free from a public repo's own source, without touching
the network layer ZeroTier/SSH hardening actually protects.

What it does: walks every tracked file under the given root (skips .git,
binary extensions, and *.TAG/*.sha256 sidecars -- those are hash content by
construction, not prose that could disclose anything), and flags any line
matching a known-sensitive infrastructure pattern:

  ZEROTIER_IP    -- the 172.27.0.0/16 overlay range used by every SIPA OS
                    node (SERVER/T15/X7/X5/LAPTOP). A real internal address,
                    not a placeholder -- CLAUDE.md's own NETWORK CANON table
                    is exactly this range, exactly why it must never leave
                    that one private file.
  PHONE_SSH_PORT -- literal 8022, the non-default SSH port both phone nodes
                    (T15, X7) listen on. Meaningful only in combination with
                    an IP, but the port alone is still a fingerprint an
                    attacker can grep GitHub for across every SIPA OS repo.
  CF_TOKEN_NAME  -- the human-readable Cloudflare API token names from
                    CLAUDE.md's own key reference (cold-wood-44da,
                    tight-silence-85f1, silent-firefly-a608). The token
                    VALUES are secrets (detect-secrets' job); the NAMES are
                    architecture metadata that let a reader match a leaked
                    value, found anywhere else, back to its actual scope.
  SERVER_LAN_IP  -- the SERVER node's local-network address (192.168.1.122)
                    and the LAPTOP node's (192.168.1.3), from the same
                    NETWORK CANON table.
  CANON_PATH     -- absolute paths into the private canon tree itself
                    (/home/sipa/PROJECT/PAYTON_HUBS, /home/sipa/.sipa_env,
                    /home/sipa/.sipa_secrets*) -- confirms to a reader that
                    this exact directory layout exists on a reachable host,
                    independent of whether any secret value is nearby.

Deliberately narrow: this is not a general secrets-and-PII linter (that is
detect-secrets' job, already run manually this session, worth wiring in
separately if she wants it as a standing hook). This only covers the
specific, named, already-catalogued architecture facts from CLAUDE.md's own
NETWORK CANON and key-reference tables -- the exact set the architect
pointed at live. Extending the pattern set is a real decision each time
(same discipline as citation_baseline.txt), not a place to paste in
speculative regexes.

Baseline: scripts/infra_disclosure_baseline.txt, same (file, line-content)
pair-per-line format as the citation baselines. A match here is a real,
reviewed exception (e.g. this script's own docstring, which has to name the
patterns it looks for) -- never add a line just to silence the hook.

Exit code is nonzero iff any non-baselined match exists, so this runs as a
pre-commit step alongside the other four checks -- same git-tree-not-disk
discipline as check_seals.py / check_jsonl_canonical.py (operates on
sys.argv[1] when given one, so the pre-commit hook can point it at the
git-archive extraction instead of the working tree).

Usage: python3 scripts/check_infra_disclosure.py [root_dir] [--json]
"""
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git"}
SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".webp",
}
SKIP_SUFFIXES = (".TAG", ".sha256")

PATTERNS = [
    ("ZEROTIER_IP", re.compile(r"\b172\.27\.\d{1,3}\.\d{1,3}\b")),
    ("PHONE_SSH_PORT", re.compile(r"\b8022\b")),
    ("CF_TOKEN_NAME", re.compile(r"\b(cold-wood-44da|tight-silence-85f1|silent-firefly-a608)\b")),
    ("SERVER_LAN_IP", re.compile(r"\b192\.168\.1\.(122|3)\b")),
    ("CANON_PATH", re.compile(r"/home/sipa/(PROJECT/PAYTON_HUBS|\.sipa_env|\.sipa_secrets)\b")),
]

BASELINE_PATH = os.path.join(REPO_ROOT, "scripts", "infra_disclosure_baseline.txt")


def load_baseline() -> set:
    pairs = set()
    if not os.path.isfile(BASELINE_PATH):
        return pairs
    with open(BASELINE_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                pairs.add(tuple(line.split("\t", 1)))
    return pairs


def is_binary_path(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in SKIP_EXTS


def iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(SKIP_SUFFIXES):
                continue
            full = os.path.join(dirpath, name)
            if is_binary_path(full):
                continue
            yield full


def scan(root: str):
    baseline = load_baseline()
    findings = []  # (relpath, line_no, pattern_name, line_content)
    for path in iter_files(root):
        rel = os.path.relpath(path, root)
        if rel.startswith("scripts/check_infra_disclosure.py") or rel.endswith(
            "infra_disclosure_baseline.txt"
        ):
            # This script's own docstring and its baseline file necessarily
            # name every pattern -- not a leak, would only ever self-flag.
            continue
        try:
            with open(path, encoding="utf-8", errors="strict") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines, start=1):
            for pname, pat in PATTERNS:
                if pat.search(line):
                    key = (rel, line.strip())
                    if key in baseline:
                        continue
                    findings.append((rel, i, pname, line.strip()))
    return findings


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    root = args[0] if args else REPO_ROOT

    findings = scan(root)

    if as_json:
        print(json.dumps(
            [{"file": f, "line": n, "pattern": p, "content": c} for f, n, p, c in findings],
            ensure_ascii=False, indent=2,
        ))
    else:
        if not findings:
            print("[check_infra_disclosure] OK: no non-baselined infrastructure-topology matches")
        else:
            print(f"[check_infra_disclosure] FOUND {len(findings)} non-baselined match(es):")
            for f, n, p, c in findings:
                print(f"  {f}:{n} [{p}] {c}")
            print(
                "\nIf any of these are genuine, deliberate exceptions, add "
                "them to scripts/infra_disclosure_baseline.txt (file<TAB>line "
                "content, one per line) -- never to silence the hook without "
                "review."
            )

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
