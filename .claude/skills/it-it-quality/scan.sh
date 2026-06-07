#!/usr/bin/env bash
# it-it-quality scanner. Flags likely register and naturalness problems in it-IT
# content: the formal "Lei" for players, anglicisms, dashes, the "pò" misspelling,
# and no-lose tone slips.
#
# It is a CANDIDATE FINDER, not an auto-fixer. Italian has more expected false
# positives than the other locales (for example "Lei" can legitimately mean "she"
# at the start of a sentence, and warmth cannot be regexed), so lean hard on the
# judgment pass and references/it-it-guide.md. The accent homographs (e/e, da/da,
# si/si) are NOT scanned because both forms are real words; check those by reading.
#
# Usage:
#   scan.sh                 # scan every it-IT .md under worlds/ and guide/
#   scan.sh path [path...]  # scan only the given files or globs
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

if [ "$#" -gt 0 ]; then
  files=$(printf '%s\n' "$@")
else
  files=$(find worlds guide -path '*it-IT*' -name '*.md' 2>/dev/null)
fi
[ -z "$files" ] && { echo "no it-IT files found"; exit 0; }

total=0
scan() {
  local title="$1" pat="$2"
  local hits
  hits=$(printf '%s\n' "$files" | xargs -r grep -nP "$pat" 2>/dev/null)
  if [ -n "$hits" ]; then
    local n
    n=$(printf '%s\n' "$hits" | wc -l | tr -d ' ')
    total=$((total + n))
    printf '\n## %s  (%s)\n' "$title" "$n"
    printf '%s\n' "$hits"
  fi
}

echo "# it-IT quality scan"

# Note: case-sensitive on purpose for "Lei" (formal you) versus "lei" (she).
scan "formal Lei for players (use tu/voi); noisy, 'Lei' can mean 'she'" \
  '\bLei\b'
scan "anglicisms: use the Italian word ('ok' is fine, so not flagged)" \
  '(?i)\b(game|team|level|player|score|cool)\b'
scan "po misspelling: write \"po'\" with an apostrophe, never the accented form" \
  '\bpò\b'
scan "accent error: closed-e words take the acute (perché, né, sé), not the grave" \
  '(?i)\b(perchè|affinchè|poichè|finchè|benchè|purchè|nè|sè)\b'
scan "apostrophe error: qual è and un altro (m) take no apostrophe" \
  '(?i)(\bqual[\x27\x{2019}]|\bun[\x27\x{2019}]altro\b)'
scan "em/en dash: use comma, colon or parentheses" '[\x{2013}\x{2014}]'
scan "no-lose tone (sconfitta/fallimento/perdere): use \"un'altra strada\"" \
  '(?i)\b(sconfitt\w+|falliment\w+|perd(ere|i|e|ono|iamo|ete)|pers[oaie])\b'

printf '\n%s candidate line(s). These are candidates, not auto-fixes:\n' "$total"
echo "read each in context and apply .claude/skills/it-it-quality/references/it-it-guide.md."
