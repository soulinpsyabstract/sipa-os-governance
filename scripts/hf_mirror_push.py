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
  3. Writes that sha (plus UTC push time) into MIRROR_PROVENANCE.md --
     a file that does NOT come out of the archive, deliberately, and
     carries no .sha256 of its own for the same reason. (dipankarsarkar,
     2026-08-29, round 2: the first version of this script stamped that
     block into README.md after archiving, which meant README.md was
     the one file in the mirror whose bytes didn't match the commit its
     own seal claimed to certify -- "the file that says everything came
     out of the archive is the file it is false about." A seal that
     makes a stamping exception for the file most likely to be read
     first isn't a smaller version of the original bug, it's the same
     bug moved to worse ground. The seal certifies the file as it
     exists UPSTREAM, no exceptions -- so provenance lives beside the
     archive, never inside it.) The sha is also in every HF commit
     message, which is the more durable place a forensic reader would
     check anyway -- tied to the upload event by the platform, not by
     a claim a file makes about itself.
  4. Uploads the archived tree plus that one added file as ONE atomic
     commit via upload_folder, so the mirror is a projection of a
     revision, not a snapshot of a moment -- his exact framing, taken
     literally.
  5. Passes delete_patterns=["*"] to upload_folder. Found live, 2026-08-31,
     round 6: `git rm`-ing the stale root EXP-024 duplicate locally and
     pushing did not remove it from the mirror -- upload_folder with no
     delete_patterns only adds/overwrites, never removes, so a file
     deleted upstream stays on the mirror forever. Same shape of bug as
     everything else this round: a step believed to make the mirror equal
     the commit, that in fact only ever grows it. delete_patterns=["*"]
     means "the archived tree IS the whole intended state" -- true here
     because the folder being uploaded is a full `git archive` of the
     commit, not a partial update.

No AI calls. Requires HF_TOKEN in the environment (sourced from
.sipa_env by the caller) and huggingface_hub installed.
"""
import os
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HF_REPO_ID = "SoulInPsyAbstract/sipa-os-governance"


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


def write_provenance_file(tree: Path, sha: str, commit_ts: str) -> str:
    """Write MIRROR_PROVENANCE.md -- a file that does not come out of
    `git archive` and gets no .sha256 sidecar, on purpose. It describes
    the copy; it isn't part of what the copy certifies. Returns the
    commit-message line so main() can put the same sha somewhere a
    forensic reader would find it even faster: the HF commit itself."""
    pushed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = (
        "# Mirror provenance\n\n"
        "This is not part of the archived repository -- it is written fresh on every "
        "push and carries no `.sha256` seal, deliberately. Every *other* file in this "
        "mirror is a byte-exact `git archive` of one GitHub commit, sealed at that "
        "commit; this file is the one exception, because a provenance stamp that lived "
        "inside README.md used to make README.md the one file whose seal didn't match "
        "its own upstream content (dipankarsarkar, 2026-08-29). Fixed by moving the "
        "stamp here instead of recomputing the seal around it.\n\n"
        f"- **Source commit:** [`{sha}`](https://github.com/soulinpsyabstract/sipa-os-governance/commit/{sha})\n"
        f"- **Committed upstream:** {commit_ts}\n"
        f"- **Pushed to this mirror:** {pushed_at}\n"
        "- **Method:** `git archive` of that exact commit, uploaded as one atomic "
        "commit via `scripts/hf_mirror_push.py`, which refuses to run on a dirty tree.\n"
    )
    (tree / "MIRROR_PROVENANCE.md").write_text(content)
    return f"Mirror GitHub commit {sha} (committed {commit_ts}), pushed {pushed_at}"


def main() -> int:
    refuse_if_dirty()
    sha = current_sha()
    commit_ts = commit_timestamp(sha)
    print(f"[hf_mirror_push] pushing commit {sha} ({commit_ts})")

    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        archive_commit_to(sha, tree)

        # Round 7, dipankarsarkar: pre-commit's own disk-vs-commit gap
        # (fixed in scripts/pre-commit this same round) has a second copy
        # here -- this script already extracts `tree` as a clean archive
        # of the commit before uploading it, which is exactly what the
        # citation checker should run against, not trust that pre-commit
        # already checked. Same code, second distribution path, closes
        # the gap for anyone who committed with --no-verify, from a clone
        # that never ran install-hooks.sh, or from CI (which currently
        # doesn't install hooks at all -- also his round-7 finding).
        check_result = subprocess.run(
            ["python3", str(tree / "scripts" / "check_citations.py")],
            cwd=tree,
        )
        if check_result.returncode != 0:
            print("[hf_mirror_push] REFUSED: check_citations.py failed against "
                  f"the archived tree for {sha} -- not pushing a commit the "
                  "gate itself would reject.")
            return 1

        # Round 8: the same reasoning extends to check_dataset_citations.py
        # -- the bucket check_citations.py structurally can't reach (a
        # .jsonl file, a citation field that's a URL). Same tree, same
        # refuse-on-failure policy.
        dataset_check_result = subprocess.run(
            ["python3", str(tree / "scripts" / "check_dataset_citations.py")],
            cwd=tree,
        )
        if dataset_check_result.returncode != 0:
            print("[hf_mirror_push] REFUSED: check_dataset_citations.py failed "
                  f"against the archived tree for {sha}.")
            return 1

        commit_msg = write_provenance_file(tree, sha, commit_ts)

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
            commit_message=commit_msg,
            delete_patterns=["*"],
        )
    print(f"[hf_mirror_push] DONE: mirror now projects commit {sha}, single atomic push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
