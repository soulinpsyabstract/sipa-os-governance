#!/usr/bin/env python3
"""check_mirror_integrity -- answers dipankarsarkar's round-18 question
directly: "What would catch a mirror whose content and seal disagree, if
nobody happened to be auditing it that hour?"

Every existing check in this repo (check_locator_precision.py,
check_citations.py, check_dataset_citations.py) reads the LOCAL GIT TREE.
That's a real, structural blind spot: hf_mirror_push.py is airtight about
what IT pushes (single atomic commit, refuses a dirty tree, archives one
git sha), but has no way to know what anything else pushes to the same
target. A hand `hf upload <file>` push -- exactly the failure class the
script was built to prevent -- can still land directly on the mirror,
bypassing the script entirely, and nothing that only reads local git will
ever see it.

Case in point, found and independently reproduced round 18 (2026-09-21):
a manual 6-commit burst on 2026-09-04T16:16:40-46Z left the live public
mirror serving misbehavior_incidents_seed_v1.jsonl's Round-17 bytes
(91942, sha256 53ce987c...) sealed under Round-16's old .sha256
(3211085a...) for two commits, roughly three seconds, and left
MIRROR_PROVENANCE.md naming the wrong upstream commit for close to an
hour -- until the next regular script-driven push overwrote it. Nobody
was auditing during that hour. It self-healed by luck, not by any check
noticing.

This script is that check. It does not read local git at all -- it reads
ONLY the live mirror, exactly as a stranger downloading the dataset right
now would see it, and verifies every file against its own .sha256 sidecar
if one exists next to it on the mirror. A dirty window like the one above
would show up here as a MISMATCH the moment this script runs during it --
not resolved by luck, resolved by a check that actually looks at the
thing being certified instead of the thing that's supposed to produce it.

Usage:
    python3 scripts/check_mirror_integrity.py
    python3 scripts/check_mirror_integrity.py --revision <sha>   # audit a
        specific past HF commit instead of the current HEAD, e.g. to
        re-verify a historical incident the way this docstring does.

Requires HF_TOKEN in the environment (sourced from .sipa_env by the
caller, same convention as hf_mirror_push.py). No AI calls.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request

HF_REPO_ID = "SoulInPsyAbstract/sipa-os-governance"
HF_API_BASE = f"https://huggingface.co/api/datasets/{HF_REPO_ID}"
HF_RAW_BASE = f"https://huggingface.co/datasets/{HF_REPO_ID}/raw"
# `raw/` returns a Git-LFS pointer file (~130 bytes of text: oid + size), not
# the actual bytes, for anything LFS-tracked -- confirmed live, round 18: a
# small .zip whose raw/ content hashed to 1c667ecd... (the pointer) while its
# real content, fetched via resolve/ (which follows the LFS pointer), hashed
# to 60e3f23b..., matching the seal exactly. `resolve/` is correct for both
# LFS and non-LFS files; `raw/` is only safe for the tiny non-LFS .sha256
# sidecars themselves, never for the content being verified.
HF_RESOLVE_BASE = f"https://huggingface.co/datasets/{HF_REPO_ID}/resolve"

# Files whose seal lives beside the archive but is the archive verifying
# ITSELF, not the mirror's copy of it -- and files this script has no
# business checking (directories, the provenance stamp, which documents
# itself as deliberately unsealed -- see MIRROR_PROVENANCE.md's own text).
_SKIP_SUFFIXES = (".sha256", ".TAG")
_SKIP_EXACT = {"MIRROR_PROVENANCE.md", ".gitattributes"}


def _http_get(url: str, token: str, timeout: int = 30, retries: int = 3) -> bytes:
    body, _headers = _http_get_with_headers(url, token, timeout=timeout, retries=retries)
    return body


def _http_get_with_headers(url: str, token: str, timeout: int = 30, retries: int = 3):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_err}")


def _parse_next_link(link_header: str | None) -> str | None:
    """Parse a `Link: <url>; rel="next", <url2>; rel="prev"` header (RFC 5988)
    and return the rel="next" URL, or None if there isn't one.

    dipankarsarkar, round 19 (2026-09-21): the tree/ endpoint DOES paginate
    at 1000 entries -- confirmed live against this exact repo (441 total
    seals, page 1 stops at 342 with a Link header present, page 2 holds the
    other 99). The previous version of this function set cursor_url = None
    unconditionally after one call and never looked at the Link header at
    all, so the docstring's own stated intent ("fail loud rather than
    silently check a partial mirror") never had a chance to fire -- there
    was no code path that could detect pagination in the first place. Fixed
    by actually reading the header instead of asserting its absence.
    """
    if not link_header:
        return None
    for part in link_header.split(","):
        segments = part.split(";")
        if len(segments) < 2:
            continue
        url_part = segments[0].strip()
        if not (url_part.startswith("<") and url_part.endswith(">")):
            continue
        rel_is_next = any(seg.strip().replace(" ", "") in ('rel="next"', "rel=next") for seg in segments[1:])
        if rel_is_next:
            return url_part[1:-1]
    return None


def _list_tree(token: str, revision: str) -> dict[str, int]:
    """Every file path in the mirror at `revision`, recursively, mapped to its
    known size in bytes. Follows Link: rel="next" pagination -- see
    _parse_next_link's docstring for why this used to silently stop after
    page 1.

    dipankarsarkar, round 23 (2026-09-23): the tree listing already carries
    each entry's `size`, but this function used to keep only `path` and drop
    it on the way in -- so `check()` had no independent byte count to verify
    a fetched body against, only the hash. A client that fetches the WRONG
    bytes (a 307 redirect page instead of the real file, an LFS pointer
    instead of the resolved blob -- exactly round 18's bug class) can still
    produce "a right hash of the wrong bytes" if the reference hash was
    computed the same buggy way. Size is now threaded through so `check()`
    can assert `len(body) == size` before trusting any hash match at all.
    """
    url = f"{HF_API_BASE}/tree/{revision}?recursive=true"
    import json

    sizes: dict[str, int] = {}
    cursor_url: str | None = url
    pages = 0
    while cursor_url:
        raw, headers = _http_get_with_headers(cursor_url, token)
        entries = json.loads(raw)
        for entry in entries:
            if entry.get("type") == "file":
                sizes[entry["path"]] = entry.get("size")
        pages += 1
        cursor_url = _parse_next_link(headers.get("Link"))
    if pages > 1:
        print(f"[check_mirror_integrity] tree listing paginated: {pages} pages, {len(sizes)} total paths", flush=True)
    return sizes


def check(revision: str, token: str) -> int:
    sizes = _list_tree(token, revision)
    paths = list(sizes.keys())
    path_set = set(paths)
    # Fallback for legacy layouts where a seal doesn't sit next to its target
    # -- confirmed live, round 18: FIRST_ERA archives keep every .sha256 in
    # a sibling SHA256/ folder while the sealed file lives in a sibling
    # LOGS/ or MANIFEST/ folder, same basename. Rather than hardcode those
    # two folder names (the next legacy convention would just be a third),
    # index every path by its basename once and fall back to "exactly one
    # other file anywhere in the tree shares this basename" before calling
    # a seal orphaned.
    by_basename: dict[str, list[str]] = {}
    for p in paths:
        by_basename.setdefault(p.rsplit("/", 1)[-1], []).append(p)

    sealed = [p for p in paths if p.endswith(".sha256")]

    checked = 0
    mismatches: list[tuple[str, str, str]] = []
    size_mismatches: list[tuple[str, int, int]] = []
    missing_target: list[str] = []
    resolved_elsewhere: list[tuple[str, str]] = []

    for seal_path in sealed:
        same_dir_target = seal_path[: -len(".sha256")]
        if same_dir_target in _SKIP_EXACT or same_dir_target.endswith(_SKIP_SUFFIXES):
            continue

        target_path: str | None = None
        if same_dir_target in path_set:
            target_path = same_dir_target
        else:
            basename = same_dir_target.rsplit("/", 1)[-1]
            candidates = [p for p in by_basename.get(basename, []) if not p.endswith(".sha256")]
            if len(candidates) == 1:
                target_path = candidates[0]
                resolved_elsewhere.append((seal_path, target_path))
            else:
                missing_target.append(seal_path)
                continue

        content = _http_get(f"{HF_RESOLVE_BASE}/{revision}/{target_path}", token)
        # dipankarsarkar, round 23: verify byte count against the tree
        # listing's own `size` BEFORE trusting any hash match. A client that
        # fetched the wrong bytes (a 307 redirect page, an LFS pointer) can
        # still produce a hash that matches a reference computed the same
        # buggy way -- "a right hash of the wrong bytes" fails on byte count
        # alone even when it passes on hash alone, so check count first and
        # independently of the hash, not as a corroborating detail.
        expected_size = sizes.get(target_path)
        if expected_size is not None and len(content) != expected_size:
            size_mismatches.append((target_path, len(content), expected_size))
            continue
        actual = hashlib.sha256(content).hexdigest()
        sealed_raw = _http_get(f"{HF_RAW_BASE}/{revision}/{seal_path}", token)
        # .sha256 sidecar format is "<hex>  <filename>\n" (sha256sum's own
        # output format) or bare hex -- accept either, take the first
        # whitespace-delimited token.
        sealed_hash = sealed_raw.decode("utf-8", errors="replace").split()[0].strip()

        checked += 1
        if actual != sealed_hash:
            mismatches.append((target_path, actual, sealed_hash))

    print(f"[check_mirror_integrity] revision={revision}")
    print(f"[check_mirror_integrity] files with a .sha256 sidecar: {len(sealed)}")
    print(f"[check_mirror_integrity] verified against live content: {checked}")

    if resolved_elsewhere:
        print(f"[check_mirror_integrity] resolved via basename fallback (seal not in same dir as target): {len(resolved_elsewhere)}")
        for seal_path, target_path in resolved_elsewhere:
            print(f"  - {seal_path} -> {target_path}")

    if missing_target:
        print(f"[check_mirror_integrity] SEAL WITH NO TARGET FILE: {len(missing_target)}")
        for p in missing_target:
            print(f"  - {p}")

    if size_mismatches:
        print(f"[check_mirror_integrity] SIZE MISMATCH: {len(size_mismatches)} file(s) where the fetched body's byte count does not match the tree listing's own size -- fetched the wrong bytes (redirect page, LFS pointer, etc.), checked before any hash comparison")
        for path, got, expected in size_mismatches:
            print(f"  - {path}")
            print(f"      fetched body bytes: {got}")
            print(f"      tree listing size:  {expected}")

    if mismatches:
        print(f"[check_mirror_integrity] MISMATCH: {len(mismatches)} file(s) where the live mirror's content does not match its own sealed hash")
        for path, actual, sealed_hash in mismatches:
            print(f"  - {path}")
            print(f"      live content sha256:   {actual}")
            print(f"      sealed .sha256 claims:  {sealed_hash}")
        return 1

    if missing_target or size_mismatches:
        return 1

    print("[check_mirror_integrity] OK: every sealed file on the live mirror matches its own .sha256")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revision", default="main", help="HF revision/commit to audit (default: main, i.e. right now)")
    args = ap.parse_args()

    token = None
    import os

    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            with open(os.path.expanduser("~/.sipa_env")) as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"')
        except FileNotFoundError:
            pass
    if not token:
        print("[check_mirror_integrity] REFUSED: no HF_TOKEN in environment or ~/.sipa_env", file=sys.stderr)
        sys.exit(2)

    sys.exit(check(args.revision, token))


if __name__ == "__main__":
    main()
