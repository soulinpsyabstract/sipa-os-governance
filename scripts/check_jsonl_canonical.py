#!/usr/bin/env python3
"""check_jsonl_canonical -- every tracked *.jsonl line round-trips byte for
byte through json.dumps(json.loads(line), ensure_ascii=False).

dipankarsarkar's round-44/round-46 finding (check_locator_precision.py's
own docstring, round 44): a re-serialization with a stray ensure_ascii
default silently turns real Cyrillic characters into \\u-escaped ASCII in
the raw file, changing zero parsed values (so every existing per-field
invariant this repo runs stays green) but breaking the one contract this
project has repeatedly said the raw line exists to honor: "a string a
reader can ctrl-F without trusting anyone." A reader who ctrl-F's a
Cyrillic word cannot match an escaped sequence. Demonstrated live:
commit e67a6ee (round 43) introduced exactly this regression on 6 lines
of misbehavior_incidents_seed_v1.jsonl (OPENCLAW + 5 SIPA-2026 records);
commit 72b0020 (round 44) fixed it by re-serializing with
ensure_ascii=False. Round 44's own docstring named this a real, permanent
gap: "a future re-serialization ... could reintroduce the exact same
regression, silently, since no invariant here currently reads raw bytes
to catch it." This script is that invariant.

The check is intentionally NOT "no \\u in the raw line" -- dipankarsarkar
demonstrated that grep would be wrong on a correct file:
misbehavior_raw_candidates_ui_archives_v1.jsonl has (at least) four lines
whose `quote` field legitimately contains a literal `\\uXXXX`-style
substring as PARSED TEXT, not as a serialization artifact -- the archived
ChatGPT tool call (`search("...")`) was already escaped when the UI
exported it, so the escape sequence is the verbatim content, not this
project's own json.dumps choice. Grepping for `\\u` would misclassify
those four correct lines as violations; round-tripping the parsed value
does not, because ensure_ascii=False only changes how NON-ASCII
CHARACTERS get encoded during serialization -- it does not touch ASCII
text that already reads as literal backslash-u-hex, wherever that text
came from. Confirmed live: all four lines pass this check unchanged.

The round-trip is also strictly stronger than an ensure_ascii-only check:
it catches key reordering, a stray indent= or separators= argument, or any
other non-canonical serialization choice a future writer might introduce
-- anything json.dumps(json.loads(line)) wouldn't reproduce byte for byte,
not only the ensure_ascii axis specifically.

Usage:
    python3 scripts/check_jsonl_canonical.py [root]

    root defaults to the repository root (two levels up from this file);
    pre-commit passes the scratch extraction of the tree being committed,
    same convention as check_seals.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check(root: Path) -> int:
    files = sorted(root.glob("AI_EXPERIMENTS/DATASETS*/*.jsonl"))
    if not files:
        print("[check_jsonl_canonical] no *.jsonl files found under AI_EXPERIMENTS/DATASETS*/")
        return 0

    total_lines = 0
    total_fails: list[tuple[Path, int]] = []

    for path in files:
        rel = path.relative_to(root)
        lines = path.read_text(encoding="utf-8").split("\n")
        # A trailing newline produces one empty trailing element; a file with
        # no trailing newline does not. Drop only that specific artifact, not
        # any genuinely blank line a writer might have left mid-file.
        if lines and lines[-1] == "":
            lines = lines[:-1]
        for i, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            total_lines += 1
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as e:
                total_fails.append((rel, i))
                print(f"[check_jsonl_canonical] {rel}:{i}: not valid JSON ({e})")
                continue
            canonical = json.dumps(parsed, ensure_ascii=False)
            if canonical != line:
                total_fails.append((rel, i))

    print(f"[check_jsonl_canonical] files checked: {len(files)}")
    print(f"[check_jsonl_canonical] lines checked: {total_lines}")

    if total_fails:
        by_file: dict[Path, list[int]] = {}
        for rel, i in total_fails:
            by_file.setdefault(rel, []).append(i)
        print(f"[check_jsonl_canonical] NON-CANONICAL: {len(total_fails)} line(s) do not round-trip through json.dumps(json.loads(line), ensure_ascii=False)")
        for rel, line_nums in by_file.items():
            print(f"  - {rel}: lines {', '.join(str(n) for n in line_nums)}")
        return 1

    print("[check_jsonl_canonical] OK: every line in every tracked *.jsonl round-trips byte for byte")
    return 0


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    sys.exit(check(root))


if __name__ == "__main__":
    main()
