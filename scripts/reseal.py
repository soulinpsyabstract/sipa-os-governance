#!/usr/bin/env python3
"""reseal.py -- the additive replacement for the ad-hoc TAG-regeneration
pattern used throughout this repo's history (a one-line printf that writes
FILE/SHA256/SIZE/DEVICE/TS and nothing else).

dipankarsarkar, 2026-08-29/30 (round 4 of the mirror-integrity exchange):
across 184 commits, 11 .TAG files have ever been modified (25 modify
events), and 5 of those events dropped exactly two fields -- FIXATED_BY and
NOTE -- that existed under an earlier, undocumented TAG convention. Nothing
else has ever been dropped. Root cause: every prior reseal was a full
overwrite of the five-line core schema, blind to whatever else the file
already held. No script in the repo has ever read or written FIXATED_BY;
the schema for it was never written down anywhere.

This script fixes the mechanism, not just one file: it reads the CURRENT
.TAG first (if one exists), keeps every field that isn't part of the core
five, recomputes SHA256/SIZE/TS fresh, and writes the union back. A reseal
can only ever ADD or UPDATE the core fields -- it can never silently drop
a field it doesn't recognize. This is the TAG-layer half of the answer to
his question ("does the rule reach the TAG layer at all") -- yes, now it
does, structurally, not just by remembering to be careful next time.

Usage: python3 reseal.py <path> [DEVICE]
Writes <path>.sha256 and <path>.TAG next to <path>.
"""
import hashlib
import os
import sys
from datetime import datetime

CORE_FIELDS = {"FILE", "SHA256", "SIZE", "DEVICE", "TS"}


def parse_tag(tag_path: str) -> dict:
    if not os.path.exists(tag_path):
        return {}
    fields = {}
    legacy_lines = []
    with open(tag_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if "=" not in line:
                # Older TAG convention: a single "TAG: STATUS-DATE" line,
                # no KEY=value shape at all (dipankarsarkar, round 5 --
                # found this dropped 5 real files silently, no
                # "(preserved: ...)" signal because the old code just
                # `continue`d past it instead of keeping it). Preserve the
                # raw line verbatim under a synthetic key so a legacy TAG
                # survives a reseal instead of being replaced outright.
                legacy_lines.append(line)
                continue
            k, v = line.split("=", 1)
            fields[k] = v
    if legacy_lines:
        fields["_LEGACY"] = "\n".join(legacy_lines)
    return fields


def reseal(path: str, device: str = "SERVER") -> None:
    if not os.path.isfile(path):
        raise SystemExit(f"reseal.py: not a file: {path}")

    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    size = os.path.getsize(path)
    ts = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    filename = os.path.basename(path)

    sha_path = path + ".sha256"
    with open(sha_path, "w") as f:
        f.write(f"{sha}  {filename}\n")

    tag_path = path + ".TAG"
    existing = parse_tag(tag_path)
    extra = {k: v for k, v in existing.items() if k not in CORE_FIELDS}
    legacy = extra.pop("_LEGACY", None)

    with open(tag_path, "w") as f:
        f.write(f"FILE={filename}\n")
        f.write(f"SHA256={sha}\n")
        f.write(f"SIZE={size}\n")
        f.write(f"DEVICE={device}\n")
        f.write(f"TS={ts}\n")
        for k, v in extra.items():
            f.write(f"{k}={v}\n")
        if legacy:
            f.write(legacy + "\n")

    preserved = list(extra)
    if legacy:
        preserved.append("legacy TAG line(s)")
    print(f"resealed {path}" + (f" (preserved: {', '.join(preserved)})" if preserved else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: reseal.py <path> [DEVICE]")
    reseal(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "SERVER")
