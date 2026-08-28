#!/usr/bin/env bash
# Weekly content snapshot of the sipa-os-governance repo -- same MLL L3 Report
# format as daily_governance_report.sh, aggregated over an ISO week instead of
# a single day. Mirrors the phone/server pattern (DAILY_REPORT.sh +
# WEEKLY_ARCHIVE.sh as separate, parallel jobs -- not one replacing the other).
#
# Usage: weekly_governance_report.sh [YYYY-Www]   (defaults to last ISO week, UTC)
#
# UTC week boundary, not Israel civil week -- same reasoning as
# daily_governance_report.sh (dipankarsarkar, 2026-08-26, symmetric fix):
# a fixed weekly cron against an Israel-local label breaks at the same two
# DST transitions a fixed daily cron does, just measured in weeks instead of
# days. UTC has no transition to get wrong.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

OUT_DIR="$REPO/REPORTS"
mkdir -p "$OUT_DIR"
INDEX="$OUT_DIR/INDEX.tsv"

# WEEK no longer depends on "now" when not given explicitly, same reasoning
# and same fix shape as DAY in daily_governance_report.sh (dipankarsarkar,
# 2026-08-27, third round) -- picks up the ISO week after whatever
# INDEX.tsv last recorded as "weekly", so a delayed run still reports the
# one correct next week instead of "current week relative to whenever it
# woke up". Falls back to the pre-existing default when INDEX.tsv has no
# prior weekly row (first run / pre-index history).
if [ -n "${1:-}" ]; then
  WEEK="$1"
else
  LAST_WEEKLY="$(awk -F'\t' '$1=="weekly"{d=$2} END{print d}' "$INDEX" 2>/dev/null || true)"
  if [ -n "$LAST_WEEKLY" ]; then
    LY="${LAST_WEEKLY%%-W*}"
    LW="${LAST_WEEKLY#*-W}"
    LAST_MONDAY="$(date -u -d "${LY}-01-04 +$(( (10#$LW - 1) * 7 )) days -$(( $(date -u -d "${LY}-01-04" +%u) - 1 )) days" +%F)"
    WEEK="$(date -u -d "$LAST_MONDAY +7 days" +%G-W%V)"
  else
    WEEK="$(date -u +%G-W%V)"
  fi
  # Clamp -- same overshoot the daily script had (dipankarsarkar, 2026-08-27,
  # fourth round): the cursor has no ceiling, so a verification dispatch can
  # walk it into a week that hasn't closed (or started) yet. Cap at the last
  # ISO week that has actually finished; a cursor that's behind is untouched.
  LAST_CLOSED_WEEK="$(date -u -d 'last week' +%G-W%V)"
  if [ "$WEEK" \> "$LAST_CLOSED_WEEK" ]; then
    WEEK="$LAST_CLOSED_WEEK"
  fi
fi
# Parse "YYYY-Www" into the Monday..Sunday date range for that ISO week.
YEAR="${WEEK%%-W*}"
WNUM="${WEEK#*-W}"
MONDAY="$(date -u -d "${YEAR}-01-04 +$(( (10#$WNUM - 1) * 7 )) days -$(( $(date -u -d "${YEAR}-01-04" +%u) - 1 )) days" +%F)"
SUNDAY="$(date -u -d "$MONDAY +6 days" +%F)"
# Commit hash in the filename, same fix/reason as the daily report and the
# GAP__ fix in payton-heart (4711bed) -- a re-run for the same ISO week must
# not silently overwrite an earlier run's report under the same path.
OUT="$OUT_DIR/WEEKLY__${WEEK}__$(git rev-parse --short HEAD).md"

SINCE="${MONDAY} 00:00:00"
UNTIL="${SUNDAY} 23:59:59"

commit_count="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --oneline | wc -l | tr -d ' ')"
files_touched="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --name-only --pretty=format:"" | sort -u | { grep -v '^$' || true; } | wc -l | tr -d ' ')"

{
echo "════════════════════════════════════════════════════════════"
echo "  GOVERNANCE WEEKLY REPORT · ${WEEK} (${MONDAY} → ${SUNDAY}, UTC)"
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
echo "[ GIT ACTIVITY (WEEK) ]"
echo "  commits            = $commit_count"
echo "  files touched      = $files_touched"
if [ "$commit_count" -gt 0 ]; then
  echo "  ── daily breakdown ──"
  d="$MONDAY"
  while [ "$(date -u -d "$d" +%s)" -le "$(date -u -d "$SUNDAY" +%s)" ]; do
    n="$(TZ=UTC git log --since="$d 00:00:00" --until="$d 23:59:59" --oneline | wc -l | tr -d ' ')"
    printf "  %s  ·  %s commit(s)\n" "$d" "$n"
    d="$(date -u -d "$d +1 day" +%F)"
  done
fi
echo ""
echo ""
echo "[ EXPERIMENTS OPENED THIS WEEK ]"
exp_week="$(TZ=UTC git log --since="$SINCE" --until="$UNTIL" --name-only --diff-filter=A --pretty=format:"" -- 'AI_EXPERIMENTS/EXP-*.md' | sort -u | { grep -v '^$' || true; })"
if [ -n "$exp_week" ]; then
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    title="$(head -1 "$f" | sed 's/^# //')"
    echo "  NEW  · $(basename "$f")"
    echo "         $title"
  done <<< "$exp_week"
else
  echo "  (none created this week)"
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

# Basename-only seal -- checkable with `sha256sum -c` from the seal's own
# directory on any host, unlike the previous absolute-path seal (dipankarsarkar,
# 2026-08-26).
( cd "$OUT_DIR" && sha256sum "$(basename "$OUT")" ) > "$OUT.sha256"

# Wall-clock generation time in a sidecar, not the hashed body -- same reason
# as daily_governance_report.sh: two same-week/same-HEAD runs must be byte
# identical so a re-run overwrite is a true no-op, not a silent content change
# hidden behind an unmoved hash suffix.
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$OUT.generated_at"

# Append-only per-period canonical-report index, shared with
# daily_governance_report.sh (dipankarsarkar, 2026-08-27, third round) --
# see that script's comment for the full reasoning. Same file, kind=weekly
# rows interleaved with kind=daily rows. `event` column added fourth round --
# see daily script's comment for why (schedule vs workflow_dispatch, gap
# watcher must count schedule rows only).
#
# Header self-heals instead of `[ -f ] || ...` -- same fifth-round fix and
# reasoning as daily_governance_report.sh: that guard never fires again
# once the file exists, so a column added later never reaches the header,
# and the file goes ragged for any strict TSV parser. Must use the exact
# same EXPECTED_HEADER string as the daily script -- same file, one schema.
INDEX="$OUT_DIR/INDEX.tsv"
EXPECTED_HEADER="$(printf 'kind\tperiod\tfile\thead\tcommits\tgenerated_at\tevent')"
if [ ! -f "$INDEX" ]; then
  printf '%s\n' "$EXPECTED_HEADER" > "$INDEX"
elif [ "$(head -1 "$INDEX")" != "$EXPECTED_HEADER" ]; then
  { printf '%s\n' "$EXPECTED_HEADER"; tail -n +2 "$INDEX"; } > "$INDEX.tmp"
  mv "$INDEX.tmp" "$INDEX"
fi
printf 'weekly\t%s\t%s\t%s\t%s\t%s\t%s\n' "$WEEK" "$(basename "$OUT")" "$(git rev-parse --short HEAD)" "$commit_count" "$(cat "$OUT.generated_at")" "${GITHUB_EVENT_NAME:-manual}" >> "$INDEX"

echo ""
echo "OK: report -> $OUT"
