#!/usr/bin/env bash
# Daily content snapshot of the sipa-os-governance repo -- commits, files touched,
# experiments opened/closed, canon-file hashes. Modeled on the MLL L3 Report format
# (multi-section status snapshot), not the bare CI forensic ping style of
# payton-heart's daily_receipt.yml -- that stays as-is (it proves continuity), this
# is the separate content digest the architect actually asked for.
#
# Usage: daily_governance_report.sh [YYYY-MM-DD]   (defaults to yesterday, UTC)
#
# UTC day boundary, not Israel civil day (dipankarsarkar, 2026-08-26, second
# review round): a fixed `0 21 * * *` cron against an Israel-local label breaks
# twice a year at the DST transition -- 2026-10-24 gets reported twice (fire at
# 21:00Z lands at both 00:00 IDT and 23:00 IST on consecutive UTC days, both
# resolving to the same Israel "yesterday"), and 2026-03-26 never gets reported
# at all (the symmetric skip). A hash-suffixed filename stops the double from
# overwriting, but nothing flags that two reports now silently claim the same
# calendar day -- UTC has no transition to get wrong, so the problem doesn't
# reappear one level up. This is the same reasoning applied to
# weekly_governance_report.sh, symmetrically.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

DAY="${1:-$(date -u -d yesterday +%F)}"
OUT_DIR="$REPO/REPORTS"
# Filename includes the short commit hash the report was generated from, not
# just the day -- a hand-run and a later scheduled run for the same day used
# to collide on DAILY__<day>.md and silently overwrite each other (found by
# dipankarsarkar, 2026-08-21/26: same bug class, same fix shape as the
# GAP__<day>__<run-pair>.txt fix in payton-heart, commit 4711bed).
OUT="$OUT_DIR/DAILY__${DAY}__$(git rev-parse --short HEAD).md"
mkdir -p "$OUT_DIR"

# Window is UTC now too, matching DAY -- previously DAY was computed with an
# explicit zone but SINCE/UNTIL were bare "YYYY-MM-DD HH:MM:SS" strings that
# git parses in the process's own zone (UTC on the runner). Label and
# selector disagreeing by up to 3 hours was the actual blind spot: the range
# line could claim a window that hadn't finished yet at the moment the job
# fired (dipankarsarkar, 2026-08-26). Both sides are UTC now, so they agree
# by construction -- no zone to attach to either one.
SINCE="${DAY} 00:00:00"
UNTIL="${DAY} 23:59:59"

commit_count="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --oneline | wc -l | tr -d ' ')"
files_touched="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --name-only --pretty=format:"" | sort -u | { grep -v '^$' || true; } | wc -l | tr -d ' ')"

{
echo "════════════════════════════════════════════════════════════"
echo "  GOVERNANCE DAILY REPORT · ${DAY} (UTC)"
echo "  sipa-os-governance"
echo "════════════════════════════════════════════════════════════"
echo ""
echo ""
echo "[ CANON HASHES ]"
for f in scripts/judge_v3.py scripts/eval_vuln_gate_v2.py; do
  if [ -f "$f" ]; then
    printf "  %-40s = %s\n" "$f" "$(sha256sum "$f" | cut -c1-8)"
  fi
done
echo ""
echo ""
echo "[ GIT ACTIVITY ]"
echo "  commits            = $commit_count"
echo "  files touched      = $files_touched"
if [ "$commit_count" -gt 0 ]; then
  echo "  ── commits ──"
  TZ=UTC git log --since="$SINCE" --until="$UNTIL" --pretty=format:"  ·  %h  %s" | sed 's/^/  /'
  echo ""
fi
echo ""
echo ""
echo "[ EXPERIMENTS TOUCHED TODAY ]"
exp_today="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --name-only --diff-filter=A --pretty=format:"" -- 'AI_EXPERIMENTS/EXP-*.md' | sort -u | grep -v '^$' || true)"
if [ -n "$exp_today" ]; then
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    title="$(head -1 "$f" | sed 's/^# //')"
    echo "  NEW  · $(basename "$f")"
    echo "         $title"
  done <<< "$exp_today"
else
  echo "  (none created today)"
fi
echo ""
echo ""
echo "[ REPO STATUS ]"
echo "  total EXP docs     = $(ls AI_EXPERIMENTS/EXP-*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "  total scripts      = $(find scripts -maxdepth 1 \( -name '*.py' -o -name '*.sh' \) 2>/dev/null | wc -l | tr -d ' ')"
echo "  repo size          = $(du -sh . 2>/dev/null | cut -f1)"
echo "  HEAD               = $(git rev-parse --short HEAD)"
echo ""
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  Range (UTC) : ${SINCE} → ${UNTIL}"
echo "────────────────────────────────────────────────────────────"
} | tee "$OUT"

# Seal in basename-only form so `sha256sum -c` works from the seal's own
# directory on any host -- sealing the absolute $OUT path baked the runner's
# absolute path (/home/runner/work/... on CI vs /home/sipa/apps/... locally)
# into the seal itself, making it unverifiable except from the exact
# filesystem it was written on (dipankarsarkar, 2026-08-26).
( cd "$OUT_DIR" && sha256sum "$(basename "$OUT")" ) > "$OUT.sha256"

# Wall-clock generation time lives in a sidecar, not the hashed report body.
# Reasoning (dipankarsarkar, 2026-08-26 second round): on a zero-commit day,
# HEAD doesn't move between a hand run and the scheduled run, so the
# hash-suffixed filename is identical and the second run still overwrote the
# first -- the exact collision the filename fix was supposed to close, just
# gated behind a specific commit-count edge case instead of always. The only
# reason two structurally identical reports produced different bytes was
# NOW embedded in the payload. With NOW out, two same-day/same-HEAD runs are
# byte-identical: same name, same bytes, same seal, overwrite is a no-op.
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$OUT.generated_at"

echo ""
echo "OK: report -> $OUT"
