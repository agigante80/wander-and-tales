#!/usr/bin/env bash
# es-es-quality scanner. Flags likely Latin-American or non-peninsular problems in
# es-ES content: addressing the players as "ustedes", voseo, Latin-American
# vocabulary, dashes, and no-lose tone slips.
#
# It is a CANDIDATE FINDER, not an auto-fixer. Some false positives are expected
# (for example "papa" meaning pope, "medias" meaning halves, "manejar" meaning to
# manage, "usted" for a genuinely formal in-world character). Read every hit in
# context and apply references/es-es-guide.md.
#
# Usage:
#   scan.sh                 # scan every es-ES .md under worlds/ and guide/
#   scan.sh path [path...]  # scan only the given files or globs
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

if [ "$#" -gt 0 ]; then
  files=$(printf '%s\n' "$@")
else
  files=$(find worlds guide -path '*es-ES*' -name '*.md' 2>/dev/null)
fi
[ -z "$files" ] && { echo "no es-ES files found"; exit 0; }

total=0
scan() {
  local title="$1" pat="$2"
  local hits
  hits=$(printf '%s\n' "$files" | xargs -r grep -nPi "$pat" 2>/dev/null)
  if [ -n "$hits" ]; then
    local n
    n=$(printf '%s\n' "$hits" | wc -l | tr -d ' ')
    total=$((total + n))
    printf '\n## %s  (%s)\n' "$title" "$n"
    printf '%s\n' "$hits"
  fi
}

echo "# es-ES quality scan"

scan "ustedes address (use vosotros)" '\b(ustedes|usted)\b'
scan "voseo (use the tu forms)" '\b(vos|sos|tenés|querés|podés|hacés|sabés)\b'
scan "Latin-American vocabulary: use the peninsular word" \
  '\b(carro|computadora|celular|jugo|papas?|frijol\w*|porotos?|chévere|padrísimo|ahorita|platicar|enojar\w*|manejar|boleto|durazno|frutilla|arvejas?|vereda|anteojos|frazada)\b'
scan "okay: use 'vale'" '\b(okay|ok)\b'
scan "em/en dash: use comma, colon or parentheses" '[\x{2013}\x{2014}]'
scan "no-lose tone (derrota/fracaso/perder): use 'desvío' / 'otro camino'" \
  '\b(derrota\w*|fracas\w+|perder|perdéis|pierden|perdiste|perdió)\b'

printf '\n%s candidate line(s). These are candidates, not auto-fixes:\n' "$total"
echo "read each in context and apply .claude/skills/es-es-quality/references/es-es-guide.md."
