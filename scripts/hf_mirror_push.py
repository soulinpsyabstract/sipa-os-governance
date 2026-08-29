#!/usr/bin/env python3
"""hf_mirror_push — the fix for the drift dipankarsarkar found 2026-08-29:
the HF dataset mirror was being fed from `hf upload <file>` calls against
whatever the working tree held at that moment, with no binding to a git
commit. Two symptoms of the same cause: an artifact and its .sha256 seal
could travel to the mirror in different, unrelated pushes (one file's
content from commit N next to another file's seal from commit N+1), and
files could arrive on the mirror with no seal at all if the push predated
the commit that generated it.

This script refuses to be that. It:
  1. Refuses to run if `git status --porcelain` is not empty -- no
     "close enough" push from a dirty tree.
  2. Resolves HEAD to a single sha and archives *that exact commit's
     tree* via `git archive`, not the working directory -- so the
     artifact and its seal are always read from the same git object,
     never from two different moments of the same file path.
  3. Writes that sha (plus UTC push time) into a marked, auto-generated
     block in README.md's dataset card, so "which commit is this copy"
     is answerable by reading the mirror itself instead of inferred
     from push timing.
  4. Uploads the archived tree as ONE atomic commit via upload_folder,
     so the mirror is a projection of a revision, not a snapshot of
     a moment -- his exact framing, taken literally.

No AI calls. Requires HF_TOKEN in the environment (sourced from
.sipa_env by the caller) and huggingface_hub installed.
"""
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HF_REPO_ID = "SoulInPsyAbstract/sipa-os-governance"

PROVENANCE_START = "<!-- MIRROR_PROVENANCE_START -->"
PROVENANCE_END = "<!-- MIRROR_PROVENANCE_END -->"


def run(cmd: list[str], **kw) -> str:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True, **kw).stdout.strip()


def refuse_if_dirty() -> None:
    status = run(["git", "status", "--porcelain"])
    if status:
        print("[hf_mirror_push] REFUSED: working tree is dirty, not pushing a mixed-moment mirror.")
        print(status)
        sys.exit(1)


def current_sha() -> str:
    return run(["git", "rev-parse", "HEAD"])


def commit_timestamp(sha: str) -> str:
    return run(["git", "show", "-s", "--format=%cI", sha])


def archive_commit_to(sha: str, dest: Path) -> None:
    """Extract the exact tree at `sha` -- not the working directory --
    so a file and its seal always come from the same git object."""
    dest.mkdir(parents=True, exist_ok=True)
    archive_path = dest.parent / f"{sha}.tar"
    with open(archive_path, "wb") as f:
        subprocess.run(["git", "archive", "--format=tar", sha], cwd=REPO_ROOT, stdout=f, check=True)
    with tarfile.open(archive_path) as tar:
        tar.extractall(dest, filter="data")
    archive_path.unlink()


def stamp_provenance(readme_path: Path, sha: str, commit_ts: str) -> None:
    pushed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    block = (
        f"{PROVENANCE_START}\n"
        f"**Mirror provenance:** this copy is `git archive` of GitHub commit "
        f"[`{sha}`](https://github.com/soulinpsyabstract/sipa-os-governance/commit/{sha}) "
        f"(committed {commit_ts}), pushed atomically at {pushed_at}. "
        f"Every artifact and its `.sha256` seal come from this same commit -- "
        f"never a working-tree snapshot, never mixed moments. "
        f"Pushed by `scripts/hf_mirror_push.py`, which refuses to run on a dirty tree.\n"
        f"{PROVENANCE_END}"
    )
    text = readme_path.read_text() if readme_path.exists() else ""
    pattern = re.compile(re.escape(PROVENANCE_START) + r".*?" + re.escape(PROVENANCE_END), re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(block, text)
    else:
        # Insert right after the YAML frontmatter (the second '---' line).
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = f"---{parts[1]}---\n\n{block}\n{parts[2]}"
        else:
            text = block + "\n\n" + text
    readme_path.write_text(text)


def main() -> int:
    refuse_if_dirty()
    sha = current_sha()
    commit_ts = commit_timestamp(sha)
    print(f"[hf_mirror_push] pushing commit {sha} ({commit_ts})")

    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        archive_commit_to(sha, tree)
        stamp_provenance(tree / "README.md", sha, commit_ts)

        from huggingface_hub import HfApi

        token = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_GRAND")
        if not token:
            print("[hf_mirror_push] REFUSED: no HF_TOKEN in environment.")
            return 1

        api = HfApi(token=token)
        api.upload_folder(
            folder_path=str(tree),
            repo_id=HF_REPO_ID,
            repo_type="dataset",
            commit_message=f"Mirror GitHub commit {sha}",
        )
    print(f"[hf_mirror_push] DONE: mirror now projects commit {sha}, single atomic push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
