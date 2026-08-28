#!/usr/bin/env bash
# consequence_wrap.sh — wires CONSEQUENCE_EXECUTOR into real interactive use
# instead of leaving it exercised only by pytest fixtures (found 2026-08-28:
# consequence_prediction_feedback.jsonl had 25 lines, all 12 unique fixture
# commands from test_CONSEQUENCE_EXECUTOR.py, duplicated by two test runs —
# zero real production events).
#
# Sourced from ~/.bashrc (interactive shells only, by design — bash does not
# source .bashrc for non-interactive `bash -c "..."` invocations, so this does
# NOT intercept Claude Code's own automated Bash tool calls, only a human
# typing these commands by hand in a real terminal). That's the real-data
# source: every git filter-repo / git reset --hard / rm -rf a person actually
# runs, gated for real, logged for real.
#
# Scope note (consequence_gate.py's own WARNING applies): only the current
# directory's git toplevel is auto-detected as scope. A command whose real
# blast radius is elsewhere (e.g. `rm -rf ../other-repo`) won't have that
# repo scoped automatically — the drift re-check only compares what it's
# told to watch.

_cg_gate() {
  local cmd="$*"
  local repo_args=()
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    repo_args=(--git-repo "$(git rev-parse --show-toplevel)")
  fi
  python3 /home/sipa/bin/consequence_gate.py "$cmd" "${repo_args[@]}"
}

git() {
  if [ "$1" = "filter-repo" ] || { [ "$1" = "reset" ] && [ "$2" = "--hard" ]; }; then
    _cg_gate "git $*"
  else
    command git "$@"
  fi
}

rm() {
  local arg has_r=0 has_f=0
  for arg in "$@"; do
    case "$arg" in
      -*r*|-*R*) has_r=1 ;;
    esac
    case "$arg" in
      -*f*) has_f=1 ;;
    esac
  done
  if [ "$has_r" = 1 ] && [ "$has_f" = 1 ]; then
    _cg_gate "rm $*"
  else
    command rm "$@"
  fi
}
