#!/usr/bin/env bash
# install-hooks.sh -- symlinks scripts/pre-commit into .git/hooks/pre-commit.
# .git/hooks/ isn't tracked by git, so every clone needs to run this once.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
chmod +x scripts/pre-commit
ln -sf ../../scripts/pre-commit .git/hooks/pre-commit
echo "installed: .git/hooks/pre-commit -> scripts/pre-commit"
