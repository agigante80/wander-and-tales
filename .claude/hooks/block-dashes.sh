#!/usr/bin/env bash
# PreToolUse hook: block em dashes (U+2014) and en dashes (U+2013) from being
# written into files via Write, Edit, MultiEdit, or NotebookEdit.
#
# Project rule: never use em or en dashes. The hyphen is only for connecting
# words; it must not stand in for an em or en dash. Rewrite with commas,
# parentheses, colons, or separate sentences instead.
#
# Reads the tool-call JSON on stdin, gathers every field that carries NEW
# content, and denies the call if either dash byte sequence is present.
# Matching is done in the C locale against the exact UTF-8 byte sequences
# (em dash = E2 80 94, en dash = E2 80 93) so it is locale independent.

set -uo pipefail

input="$(cat)"

# Collect the new-content fields across all four tools:
#   Write       -> .content
#   Edit        -> .new_string
#   NotebookEdit-> .new_source
#   MultiEdit   -> .edits[].new_string
text="$(printf '%s' "$input" | jq -r '
  [ .tool_input.content,
    .tool_input.new_string,
    .tool_input.new_source,
    ( .tool_input.edits[]?.new_string )
  ] | map(select(. != null)) | .[]' 2>/dev/null || true)"

if printf '%s' "$text" | LC_ALL=C grep -q -e $'\xe2\x80\x94' -e $'\xe2\x80\x93'; then
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: the content contains an em dash or en dash. Project rule: never use em or en dashes. Use a hyphen only to connect words, or rewrite using commas, parentheses, a colon, or separate sentences."}}
JSON
  exit 0
fi

exit 0
