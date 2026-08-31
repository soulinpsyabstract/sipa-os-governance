#!/usr/bin/env bash
# install-hooks.sh -- symlinks scripts/pre-commit into .git/hooks/pre-commit
# AND .git/hooks/pre-merge-commit (round 6: pre-commit alone doesn't fire on
# `git merge`, only on direct commits -- a merge with a genuine conflict, or
# any merge that isn't a fast-forward, needs its own hook name). Same script
# either way; check_citations.py doesn't care which git event triggered it.
# .git/hooks/ isn't tracked by git, so every clone needs to run this once.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
chmod +x scripts/pre-commit
ln -sf ../../scripts/pre-commit .git/hooks/pre-commit
ln -sf ../../scripts/pre-commit .git/hooks/pre-merge-commit
echo "installed: .git/hooks/pre-commit -> scripts/pre-commit"
echo "installed: .git/hooks/pre-merge-commit -> scripts/pre-commit"
