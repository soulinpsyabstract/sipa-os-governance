#!/usr/bin/env bash
# Weekly content snapshot of the sipa-os-governance repo -- same MLL L3 Report
# format as daily_governance_report.sh, aggregated over an ISO week instead of
# a single day. Mirrors the phone/server pattern (DAILY_REPORT.sh +
# WEEKLY_ARCHIVE.sh as separate, parallel jobs -- not one replacing the other).
#
# Usage: weekly_governance_report.sh [YYYY-Www]   (defaults to the current ISO week)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

WEEK="${1:-$(date +%G-W%V)}"
# Parse "YYYY-Www" into the Monday..Sunday date range for that ISO week.
YEAR="${WEEK%%-W*}"
WNUM="${WEEK#*-W}"
MONDAY="$(date -d "${YEAR}-01-04 +$(( (10#$WNUM - 1) * 7 )) days -$(( $(date -d "${YEAR}-01-04" +%u) - 1 )) days" +%F)"
SUNDAY="$(date -d "$MONDAY +6 days" +%F)"
NOW="$(date '+%Y-%m-%d__%H-%M-%S')"
OUT_DIR="$REPO/REPORTS"
OUT="$OUT_DIR/WEEKLY__${WEEK}.md"
mkdir -p "$OUT_DIR"

SINCE="${MONDAY} 00:00:00"
UNTIL="${SUNDAY} 23:59:59"

commit_count="$(git log --since="$SINCE" --until="$UNTIL" --oneline | wc -l | tr -d ' ')"
files_touched="$(git log --since="$SINCE" --until="$UNTIL" --name-only --pretty=format:"" | sort -u | { grep -v '^$' || true; } | wc -l | tr -d ' ')"

{
echo "════════════════════════════════════════════════════════════"
echo "  GOVERNANCE WEEKLY REPORT · ${WEEK} (${MONDAY} → ${SUNDAY})"
echo "  sipa-os-governance · generated ${NOW} IDT"
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
  while [ "$(date -d "$d" +%s)" -le "$(date -d "$SUNDAY" +%s)" ]; do
    n="$(git log --since="$d 00:00:00" --until="$d 23:59:59" --oneline | wc -l | tr -d ' ')"
    printf "  %s  ·  %s commit(s)\n" "$d" "$n"
    d="$(date -d "$d +1 day" +%F)"
  done
fi
echo ""
echo ""
echo "[ EXPERIMENTS OPENED THIS WEEK ]"
exp_week="$(git log --since="$SINCE" --until="$UNTIL" --name-only --diff-filter=A --pretty=format:"" -- 'AI_EXPERIMENTS/EXP-*.md' | sort -u | { grep -v '^$' || true; })"
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
echo "  Generated : ${NOW} IDT"
echo "  Range     : ${SINCE} → ${UNTIL}"
echo "────────────────────────────────────────────────────────────"
} | tee "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
echo ""
echo "OK: report -> $OUT"
