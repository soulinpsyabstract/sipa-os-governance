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

DAY="${1:-$(date +%F)}"
NOW="$(date '+%Y-%m-%d__%H-%M-%S')"
OUT_DIR="$REPO/REPORTS"
OUT="$OUT_DIR/DAILY__${DAY}.md"
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

sha256sum "$OUT" > "$OUT.sha256"
echo ""
echo "OK: report -> $OUT"
