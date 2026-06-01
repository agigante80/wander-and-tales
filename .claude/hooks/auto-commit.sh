#!/usr/bin/env bash
# Stop hook: commit any uncommitted working-tree changes.
#
# This is an open-source project and the rule (CLAUDE.md) is to commit at every
# change. Claude makes descriptive commits during a turn; this hook is the
# backstop that guarantees nothing is ever left uncommitted when Claude stops.
# It stages everything, commits only when there is something staged (never an
# empty commit), and never fails the turn.

set -uo pipefail

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$root" 2>/dev/null || exit 0

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

git add -A
if ! git diff --cached --quiet; then
  git commit -q \
    -m "chore: auto-commit working changes" \
    -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" \
    >/dev/null 2>&1 || true
fi
exit 0
