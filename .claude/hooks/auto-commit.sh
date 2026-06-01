#!/usr/bin/env bash
# Stop hook: commit and push any pending working-tree changes.
#
# This is an open-source project and the rule (CLAUDE.md) is to commit and push
# at every change. Claude makes descriptive commits during a turn; this hook is
# the backstop that guarantees nothing is ever left uncommitted or unpushed when
# Claude stops. It stages everything, commits only when there is something staged
# (never an empty commit), then pushes the current branch to origin. It never
# fails the turn.

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

# Push the current branch to origin if a remote is configured. This also pushes
# any descriptive commits Claude made by hand during the turn. Never fail the
# turn: a missing remote, no network, or an auth prompt is swallowed.
if git remote get-url origin >/dev/null 2>&1; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
    git push -q origin "HEAD:$branch" >/dev/null 2>&1 || true
  fi
fi
exit 0
