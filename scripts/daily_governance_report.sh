#!/usr/bin/env bash
# Daily content snapshot of the sipa-os-governance repo -- commits, files touched,
# experiments opened/closed, canon-file hashes. Modeled on the MLL L3 Report format
# (multi-section status snapshot), not the bare CI forensic ping style of
# payton-heart's daily_receipt.yml -- that stays as-is (it proves continuity), this
# is the separate content digest the architect actually asked for.
#
# Usage: daily_governance_report.sh [YYYY-MM-DD]   (defaults to today)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

DAY="${1:-$(TZ=Asia/Jerusalem date +%F)}"
# NOW is TZ-aware on purpose: the report labels this timestamp "IDT" below,
# and on GitHub Actions runners (UTC by default) an unqualified `date` call
# produced a UTC value under that label -- a real clock/label mismatch found
# by dipankarsarkar, 2026-08-26. Fixed at the source instead of trusting the
# runner's default zone.
NOW="$(TZ=Asia/Jerusalem date '+%Y-%m-%d__%H-%M-%S')"
OUT_DIR="$REPO/REPORTS"
# Filename includes the short commit hash the report was generated from, not
# just the day -- a hand-run and a later scheduled run for the same day used
# to collide on DAILY__<day>.md and silently overwrite each other (found by
# dipankarsarkar, 2026-08-21/26: same bug class, same fix shape as the
# GAP__<day>__<run-pair>.txt fix in payton-heart, commit 4711bed).
OUT="$OUT_DIR/DAILY__${DAY}__$(git rev-parse --short HEAD).md"
mkdir -p "$OUT_DIR"

SINCE="${DAY} 00:00:00"
UNTIL="${DAY} 23:59:59"

commit_count="$(git log --since="$SINCE" --until="$UNTIL" --oneline | wc -l | tr -d ' ')"
files_touched="$(git log --since="$SINCE" --until="$UNTIL" --name-only --pretty=format:"" | sort -u | { grep -v '^$' || true; } | wc -l | tr -d ' ')"

{
echo "════════════════════════════════════════════════════════════"
echo "  GOVERNANCE DAILY REPORT · ${DAY}"
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
echo "[ GIT ACTIVITY ]"
echo "  commits            = $commit_count"
echo "  files touched      = $files_touched"
if [ "$commit_count" -gt 0 ]; then
  echo "  ── commits ──"
  git log --since="$SINCE" --until="$UNTIL" --pretty=format:"  ·  %h  %s" | sed 's/^/  /'
  echo ""
fi
echo ""
echo ""
echo "[ EXPERIMENTS TOUCHED TODAY ]"
exp_today="$(git log --since="$SINCE" --until="$UNTIL" --name-only --diff-filter=A --pretty=format:"" -- 'AI_EXPERIMENTS/EXP-*.md' | sort -u | grep -v '^$' || true)"
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
echo "  Generated : ${NOW} IDT"
echo "  Range     : ${SINCE} → ${UNTIL}"
echo "────────────────────────────────────────────────────────────"
} | tee "$OUT"

# Seal in basename-only form so `sha256sum -c` works from the seal's own
# directory on any host -- sealing the absolute $OUT path baked the runner's
# absolute path (/home/runner/work/... on CI vs /home/sipa/apps/... locally)
# into the seal itself, making it unverifiable except from the exact
# filesystem it was written on (dipankarsarkar, 2026-08-26).
( cd "$OUT_DIR" && sha256sum "$(basename "$OUT")" ) > "$OUT.sha256"
echo ""
echo "OK: report -> $OUT"
