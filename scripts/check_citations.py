#!/usr/bin/env python3
"""check_citations.py -- automated citation-vs-seal checker.

dipankarsarkar, round 5: "Is 'cited' something you want computed or curated?
A short pre-commit check ... would have returned 6 this morning instead of
0." This is that check, built as a real script instead of another one-off
manual sweep -- the exact asymmetry he named (TAG layer got a mechanism,
citation layer got a one-time sweep of whatever doc was in front of me).

What it does: scans every EXP-*.md / FINDING__*.md / README*.md in the repo
-- actually every one, anywhere in the tree, not just under AI_EXPERIMENTS/
and the repo root (round-6 fix: dipankarsarkar found the docstring said
"every" while doc_patterns was three anchored globs, silently skipping 5 of
46 -- among them a stale, unsealed, uncorrected duplicate of EXP-024 sitting
at the repo root while the corrected+sealed copy lived one directory over).
Pulls every backticked span that looks like a file reference (has a path
separator or a known file extension -- excludes model names, function names,
label strings, which also live in backticks in these docs and outnumber real
path citations), resolves it against the actual repo tree (bare filenames
are searched for by basename; globs are expanded; paths under the repo's
own absolute root are made relative to it), and buckets each into:

  SEALED         -- cited, resolves to a real file, .sha256 exists AND its
                    recorded hash matches the file's actual current
                    content. Fine.
  STALE          -- cited, resolves to a real file, .sha256 exists but does
                    NOT match the file's actual content -- the artifact
                    changed after sealing and nobody resealed it. Round-6
                    fix: this used to be silently reported as SEALED,
                    because the old check only asked whether the sidecar
                    existed, never opened it. Fixable by running reseal.py.
  UNSEALED       -- cited, resolves to a real file, .sha256 missing. Defect,
                    fixable by running reseal.py on it.
  ABSENT         -- cited, does not resolve to anything in the repo tree at
                    all. Worse defect -- not fixable by sealing. Needs a
                    per-case honest append-only correction (EXP-024 is the
                    template) or is a stale/renamed reference to fix in the
                    citing doc's own prose.
  EXTERNAL       -- resolves outside this repo by construction (e.g.
                    /home/zeus/... Colab runtime paths, /content/...) --
                    not a repo artifact, nothing to seal, not reported as a
                    defect.

Exit code is nonzero iff STALE, UNSEALED, or ABSENT is nonempty, so this is
usable as a pre-commit hook, not just a manual report.

Usage: python3 scripts/check_citations.py [--json]
"""
import glob
import hashlib
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Extensions that mark a backticked span as "this is probably a file
# citation" rather than a model name / function name / label string (all of
# which also appear in backticks throughout these docs, and outnumber real
# path citations by a wide margin -- EXP-010 alone backtick-quotes
# `FastLanguageModel`, `single_action_only`, `conciseness`, none of them
# files).
FILE_EXTENSIONS = (
    ".py", ".jsonl", ".json", ".md", ".log", ".sh", ".csv", ".txt",
    ".yaml", ".yml", ".TAG", ".sha256",
)

# Absolute-path prefixes that are runtime locations on a Colab/cloud
# instance or another machine, not this repo -- cited as evidence of where
# something ran, not as something this repo can seal. Anything starting
# with one of these is EXTERNAL, not ABSENT.
EXTERNAL_PREFIXES = (
    "/home/zeus/", "/content/", "/root/", "/tmp/", "/home/sipa/specialist-models/",
)

# Bare filenames that name a doc/script living in a *different* repo (the
# canon hub, or a tooling repo) -- cited here as context for how/where an
# experiment ran, not as evidence this governance repo's own seal layer
# owns. Declared explicitly rather than guessed at by heuristic, so the
# exemption is auditable: anyone can see exactly what's exempted and why,
# instead of a regex silently deciding. Add to this list only when a
# specific citation is confirmed (not assumed) to point outside this repo.
KNOWN_EXTERNAL_REFS = {
    "CLAUDE.md", "CLAUDE-BRIEF.md", "GOLD.md", "ARCHITECTURE.md",
    "SIPA_EXECUTION_PROTOCOL.md", "SIPA_AI_INTERACTION_PROTOCOL.md",
    "SIPA_COORD.md", "feedback_claude_role_mll.md",
    "ask.sh", "BIN/ask.sh", "fix-bug.sh", "update-docs.sh", "send-report.sh",
    # Third-party library internals cited as investigative/patch context
    # (which upstream file had the bug, which line was patched) -- not
    # artifacts this repo owns or could seal, confirmed by reading each
    # citation's surrounding prose before adding (EXP-007, EXP-028, EXP-030).
    "modeling_phi3.py", "hub_kernels.py", "flashinfer/comm/fd_exchange.py",
    # NVIDIA/garak (github.com/NVIDIA/garak) probe/data files cited in
    # DATASETS_VULN_6GROUPS_EXTERNAL/README.md as provenance for which
    # upstream probes the external-dataset group was sourced from -- same
    # category as modeling_phi3.py above. Round-6: only surfaced as ABSENT
    # once the scan widened to actually cover this doc (see docstring).
    "garak/probes/apikey.py", "garak/probes/packagehallucination.py",
    "garak/probes/promptinject.py", "garak/data/dan/Dan_11_0.json",
    # Cross-hub citation: the architect's PAYTON_HUBS canon (not this repo)
    # holds the full incident register this repo's FINDING doc references
    # as provenance for the backpedal-phrase-detector's origin. This repo
    # can't seal a file it doesn't contain.
    "HUB_LEGAL_FORENSIC/INCIDENTS/INCIDENT__PAYTON-ERA-FAILURE-PATTERNS__2026-08-31.md",
}

BACKTICK_RE = re.compile(r"`([^`\n]+)`")

# HF-style "org/model-name" identifiers -- exactly one slash, no file
# extension, and the tail looks like a model/dataset slug (has digits, caps,
# or hyphens the way model names do). These are the single biggest source
# of ABSENT false positives (Qwen/Qwen2.5-7B-Instruct, deepseek-ai/..., etc)
# -- they're citations of a model identity, not of a file this repo could
# ever seal.
HF_ID_RE = re.compile(r"^[\w.-]+/[\w.-]*[A-Z0-9][\w.-]*$")

# HF org/user namespaces seen citing their own model or dataset repos in
# this doc series, where the repo-name half happens to be all-lowercase
# (so HF_ID_RE's digit/caps heuristic misses it, e.g.
# SoulInPsyAbstract/specialist-cd-binary-honesty). Same rationale as
# HF_ID_RE: a model/dataset identity, not a file this repo could seal.
KNOWN_HF_ORGS = {
    "SoulInPsyAbstract", "unsloth", "NousResearch", "deepseek-ai", "Qwen",
    "meta-llama", "mistralai", "microsoft", "openai", "zai-org",
    "vectionlabs", "NVIDIA-NeMo", "nvidia",
}


def looks_like_path(span: str) -> bool:
    if not span or " " in span or span.startswith(("http://", "https://")):
        return False
    if any(c in span for c in "<>{}()'\"$"):
        return False  # template placeholders, code snippets, price strings
    if span.endswith("/"):
        return False  # directory reference, not a specific-file citation
    if span.count("/") == 1 and not span.endswith(FILE_EXTENSIONS):
        if HF_ID_RE.match(span) or span.split("/", 1)[0] in KNOWN_HF_ORGS:
            return False  # org/model-name, not a repo file
    if "/" in span:
        return True
    return any(span.endswith(ext) for ext in FILE_EXTENSIONS)


def seal_is_current(resolved_path: str) -> bool:
    """Round-6 fix: SEALED used to mean only 'a .sha256 file exists next to
    this' (os.path.exists check, never opened). dipankarsarkar demonstrated
    the gap directly -- appended a line to a cited, sealed script without
    resealing, and the checker still printed SEALED. This is the missing
    half: read the recorded hash, recompute the real one, compare. Format
    is the one daily/weekly_governance_report.sh already write (plain
    `sha256sum <basename>` redirected to the .sha256 file), so the
    recorded hash is whitespace-token 0 of line 0.
    """
    sha_path = resolved_path + ".sha256"
    try:
        with open(sha_path, encoding="utf-8", errors="replace") as f:
            first_line = f.readline().strip()
        recorded = first_line.split()[0] if first_line else ""
        if not recorded:
            return False
        h = hashlib.sha256()
        with open(resolved_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest() == recorded
    except OSError:
        # Sidecar or artifact unreadable -- treat as not-current rather
        # than silently passing it as SEALED.
        return False


def classify(span: str, repo_files_by_basename: dict) -> tuple[str, str]:
    """Returns (bucket, resolved_repr)."""
    candidate = span

    if candidate in KNOWN_EXTERNAL_REFS:
        return "EXTERNAL", candidate

    if candidate.startswith(EXTERNAL_PREFIXES):
        return "EXTERNAL", candidate

    # Absolute path rooted at this repo -- make relative.
    if candidate.startswith(REPO_ROOT + "/"):
        candidate = candidate[len(REPO_ROOT) + 1:]
    elif candidate.startswith("/"):
        # Some other absolute path not under this repo and not a recognized
        # external prefix -- treat as external (can't seal something
        # outside the repo regardless).
        return "EXTERNAL", candidate

    candidate = candidate.rstrip("/")
    if not candidate:
        return "EXTERNAL", span

    if "*" in candidate:
        if "/" in candidate:
            matches = glob.glob(os.path.join(REPO_ROOT, candidate))
            matches = [m for m in matches if os.path.isfile(m)]
        else:
            # Bare wildcard, no directory given (e.g. "*.log"). A whole-repo
            # recursive search was tried and rejected: EXP-031's own "*.log"
            # matched unrelated FIRST_ERA/ scaffold logs from a totally
            # different archive, which would have mislabeled them UNSEALED
            # under the wrong doc's citation. There's no way to infer the
            # intended directory from the span alone without guessing --
            # so this is reported as AMBIGUOUS for a human to scope, not
            # silently resolved to a directory the checker made up.
            return "AMBIGUOUS", f"{span} (bare wildcard, no directory -- cannot auto-scope)"
        if not matches:
            return "ABSENT", span
        unsealed = [m for m in matches if not os.path.exists(m + ".sha256")]
        if unsealed:
            rel = ", ".join(os.path.relpath(m, REPO_ROOT) for m in unsealed)
            return "UNSEALED", f"{span} -> {rel}"
        stale = [m for m in matches if not seal_is_current(m)]
        if stale:
            rel = ", ".join(os.path.relpath(m, REPO_ROOT) for m in stale)
            return "STALE", f"{span} -> {rel}"
        return "SEALED", span

    direct = os.path.join(REPO_ROOT, candidate)
    if os.path.isfile(direct):
        resolved = direct
    elif "/" not in candidate and candidate in repo_files_by_basename:
        hits = repo_files_by_basename[candidate]
        if len(hits) > 1:
            return "ABSENT", f"{span} (ambiguous basename, {len(hits)} matches: {', '.join(hits)})"
        resolved = os.path.join(REPO_ROOT, hits[0])
    else:
        return "ABSENT", span

    # A citation of the sidecar itself (path.sha256 / path.TAG) is citing
    # the seal as evidence that sealing happened, not an artifact that
    # itself needs a seal-of-a-seal -- its own existence on disk (already
    # confirmed above via os.path.isfile) is the SEALED verdict.
    if resolved.endswith((".sha256", ".TAG")):
        return "SEALED", span

    if not os.path.exists(resolved + ".sha256"):
        return "UNSEALED", span
    if not seal_is_current(resolved):
        # Round-6 fix: dipankarsarkar appended one line to a cited, sealed
        # script without resealing -- classify() used to report SEALED
        # regardless, because it only checked that a .sha256 existed, never
        # that it still matched. This is that check.
        return "STALE", span
    return "SEALED", span


BASELINE_PATH = os.path.join(REPO_ROOT, "scripts", "citation_baseline.txt")


def load_baseline() -> set:
    if not os.path.exists(BASELINE_PATH):
        return set()
    pairs = set()
    with open(BASELINE_PATH) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            doc, _, span = line.partition("\t")
            pairs.add((doc, span))
    return pairs


def main():
    as_json = "--json" in sys.argv
    baseline = load_baseline()

    # Repo-wide, not anchored to AI_EXPERIMENTS/ or root -- a doc named
    # EXP-*.md / FINDING__*.md / README*.md anywhere in the tree is in
    # scope. This walk also builds repo_files_by_basename in the same
    # pass, so there's one source of truth for "what files exist" instead
    # of two (glob() here, os.walk() below) that can silently disagree.
    DOC_NAME_RE = re.compile(r"^(EXP-.*\.md|FINDING__.*\.md|README.*\.md)$")
    docs = []
    repo_files_by_basename: dict[str, list[str]] = {}
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), REPO_ROOT)
            if fn.endswith((".sha256", ".TAG")):
                continue
            repo_files_by_basename.setdefault(fn, []).append(rel)
            if DOC_NAME_RE.match(fn):
                docs.append(os.path.join(dirpath, fn))
    docs.sort()

    results = {"SEALED": [], "STALE": [], "UNSEALED": [], "ABSENT": [], "EXTERNAL": [], "AMBIGUOUS": []}
    seen = set()  # (doc, span) dedup within a doc

    for doc in docs:
        doc_rel = os.path.relpath(doc, REPO_ROOT)
        with open(doc, encoding="utf-8", errors="replace") as f:
            text = f.read()
        for span in BACKTICK_RE.findall(text):
            span = span.strip()
            if not looks_like_path(span):
                continue
            key = (doc_rel, span)
            if key in seen:
                continue
            seen.add(key)
            bucket, resolved = classify(span, repo_files_by_basename)
            baselined = bucket == "ABSENT" and (doc_rel, span) in baseline
            entry = {"doc": doc_rel, "cited": span, "detail": resolved, "baselined": baselined}
            results[bucket].append(entry)

    new_defects = [
        r for bucket in ("STALE", "UNSEALED", "ABSENT") for r in results[bucket]
        if not r.get("baselined")
    ]

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Scanned {len(docs)} docs matching EXP-*.md / FINDING__*.md / "
              f"README*.md anywhere in the repo tree\n")
        for bucket in ("SEALED", "STALE", "UNSEALED", "ABSENT", "EXTERNAL", "AMBIGUOUS"):
            baselined_n = sum(1 for r in results[bucket] if r.get("baselined"))
            suffix = f" ({baselined_n} baselined, already adjudicated)" if baselined_n else ""
            print(f"{bucket}: {len(results[bucket])}{suffix}")
        for bucket in ("STALE", "UNSEALED", "ABSENT", "AMBIGUOUS"):
            if results[bucket]:
                print(f"\n--- {bucket} ---")
                for r in results[bucket]:
                    mark = " [baselined]" if r.get("baselined") else ""
                    print(f"  {r['doc']}: `{r['cited']}`{mark}")
        if new_defects:
            print(f"\n{len(new_defects)} NEW defect(s) not in scripts/citation_baseline.txt "
                  f"-- fix (reseal.py) or, if genuinely unrecoverable, write a Correction "
                  f"section and add the pair to the baseline with a real reason.")

    return 1 if new_defects else 0


if __name__ == "__main__":
    sys.exit(main())
