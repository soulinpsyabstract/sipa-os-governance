#!/usr/bin/env python3
"""check_seals.py -- answers dipankarsarkar's round-19 question directly:
"What is supposed to check a seal that nothing cites?"

check_citations.py walks FROM documents (EXP-*.md / FINDING__*.md / README*.md)
TO the files they cite in backticks, and flags STALE/UNSEALED/ABSENT along
that path. That's citation-driven: a file with a .sha256 sidecar that no
document happens to cite by name is completely outside its scan, no matter
how stale its seal gets. scripts/citation_baseline.txt,
scripts/dataset_citation_baseline.txt, and scripts/install-hooks.sh are
exactly that case -- support scripts nothing cites in backticks, each edited
after sealing without a reseal, all three invisible to check_citations.py's
exit code (round 19, found only because check_mirror_integrity.py's
pagination bug got fixed and it could finally see page 2 of the live
mirror's tree, where these three seals' targets happened to also live).

This script is the other direction: walk EVERY *.sha256 file in the tree,
regardless of whether anything cites its target, and verify it against the
target's current content. Citation-independent by construction -- a seal
either matches its file or it doesn't, and this script doesn't care whether
a doc ever mentions the file's name.

Usage:
    python3 scripts/check_seals.py [ROOT]
        ROOT defaults to the repo root; pass a git-archive extraction (same
        pattern check_citations.py's pre-commit wiring uses) to check the
        tree that's about to be committed rather than whatever's on disk.

Exit code is nonzero iff any STALE or ORPHANED seal is found.
"""
from __future__ import annotations

import hashlib
import os
import sys

_SKIP_EXACT = {"MIRROR_PROVENANCE.md"}


def find_seals(root: str) -> list[str]:
    seals = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fn in filenames:
            if fn.endswith(".sha256"):
                seals.append(os.path.join(dirpath, fn))
    return seals


def read_sealed_hash(seal_path: str) -> str:
    with open(seal_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    # sha256sum output format "<hex>  <filename>\n", or bare hex on its own.
    return raw.split()[0].strip() if raw.split() else ""


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(root: str) -> int:
    root = os.path.abspath(root)
    seals = find_seals(root)

    # Legacy FIRST_ERA layout keeps seals in a sibling SHA256/ folder while
    # the target lives in a sibling LOGS/ or MANIFEST/ folder, same basename
    # -- same fallback check_mirror_integrity.py uses for the live mirror
    # (round 18). Without this, 9 known-fine legacy seals report as
    # ORPHANED on every single run/commit forever.
    all_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fn in filenames:
            all_files.append(os.path.join(dirpath, fn))
    by_basename: dict[str, list[str]] = {}
    for p in all_files:
        if not p.endswith(".sha256"):
            by_basename.setdefault(os.path.basename(p), []).append(p)

    checked = 0
    stale: list[tuple[str, str, str]] = []
    orphaned: list[str] = []
    resolved_elsewhere: list[tuple[str, str]] = []

    for seal_path in seals:
        same_dir_target = seal_path[: -len(".sha256")]
        target_name = os.path.basename(same_dir_target)
        if target_name in _SKIP_EXACT:
            continue

        if os.path.isfile(same_dir_target):
            target_path = same_dir_target
        else:
            candidates = by_basename.get(target_name, [])
            if len(candidates) == 1:
                target_path = candidates[0]
                resolved_elsewhere.append((os.path.relpath(seal_path, root), os.path.relpath(target_path, root)))
            else:
                orphaned.append(os.path.relpath(seal_path, root))
                continue

        sealed_hash = read_sealed_hash(seal_path)
        actual_hash = sha256_of(target_path)
        checked += 1
        if actual_hash != sealed_hash:
            stale.append((os.path.relpath(target_path, root), actual_hash, sealed_hash))

    print(f"[check_seals] seals found: {len(seals)}")
    print(f"[check_seals] verified against current content: {checked}")

    if resolved_elsewhere:
        print(f"[check_seals] resolved via basename fallback (seal not in same dir as target): {len(resolved_elsewhere)}")
        for seal_path, target_path in resolved_elsewhere:
            print(f"  - {seal_path} -> {target_path}")

    if orphaned:
        print(f"[check_seals] ORPHANED (seal exists, target file missing): {len(orphaned)}")
        for p in orphaned:
            print(f"  - {p}")

    if stale:
        print(f"[check_seals] STALE (target content no longer matches its own seal): {len(stale)}")
        for path, actual, sealed_hash in stale:
            print(f"  - {path}")
            print(f"      current sha256: {actual}")
            print(f"      sealed .sha256: {sealed_hash}")

    if stale or orphaned:
        return 1

    print("[check_seals] OK: every .sha256 in the tree matches its target's current content")
    return 0


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(check(root))
