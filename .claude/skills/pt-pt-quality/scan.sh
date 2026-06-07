#!/usr/bin/env bash
# pt-pt-quality scanner. Flags likely European-Portuguese problems in pt-PT
# content: the archaic "vos" register, Brazilian gerunds, pt-BR vocabulary,
# dashes, and no-lose tone slips.
#
# It is a CANDIDATE FINDER, not an auto-fixer. Some false positives are expected
# (for example "verdes", "testes", "quando", "lindo"). Read every hit in context
# and apply references/pt-pt-guide.md. The "vos" conjugations are irregular, so
# never blind-replace; use the conversion table in the guide.
#
# Usage:
#   scan.sh                 # scan every pt-PT .md under worlds/ and guide/
#   scan.sh path [path...]  # scan only the given files or globs
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

if [ "$#" -gt 0 ]; then
  files=$(printf '%s\n' "$@")
else
  files=$(find worlds guide -path '*pt-PT*' -name '*.md' 2>/dev/null)
fi
[ -z "$files" ] && { echo "no pt-PT files found"; exit 0; }

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

echo "# pt-PT quality scan"

scan "vós pronoun (not the enclitic -vos, which the guide keeps)" '(?<![-\w])v[oó]s\b'
scan "vos preterite (-stes)" '\b\w+stes\b'
scan "vos inflected infinitive / future subj (-rdes)" '\b\w+rdes\b'
scan "vos imperfect subj (-sseis)" '\b\w+sseis\b'
scan "vos present (sois, estais, ides, fazeis, dizeis, podeis, ...)" \
  '\b(sois|estais|ides|dais|tendes|vindes|fazeis|dizeis|vedes|podeis|quereis|sabeis|ouvis|encontrais|chegais|falais|olhais|trocais|estendeis|arregaçais|escolheis)\b'
scan "vos imperative (Lede, Parai, Ouvi, Pedi, Fazei, Deixai, Ide, ...)" \
  '\b(lede|vede|ouvi|pedi|fazei|dizei|ide|vinde|tende|sede|dai|parai|olhai|deixai|trazei|tomai|tentai|procurai|cantai|brincai|ajudai|esperai|escolhei|imprimi|lançai|ponde)\b'
scan "vos imperfect (estaveis, ereis, fazieis, ieis)" \
  '\b(estáveis|éreis|fazíeis|tínheis|íeis)\b'
scan "gerund (-ando/-endo/-indo): prefer 'a + infinitivo'" \
  '\b(?!quando|lindo|brando|comando|grande|fernando)\w+(ando|endo|indo)\b'
scan "pt-BR vocabulary: use the pt-PT word" \
  '\b(coringa|ónibus|onibus|trem|celular|banheiro|geladeira|suco|sorvete|açougue|xícara|xicara|garot[oa]s?|bonitinh[oa]|você|pra|tô)\b'
scan "em/en dash: use comma, colon or parentheses" '[\x{2013}\x{2014}]'
scan "no-lose tone (derrota/fracasso/perder): use 'desvio' / 'outro caminho'" \
  '\b(derrota\w*|fracass\w+|perde(r|u|ste|ram)\w*)\b'

printf '\n%s candidate line(s). These are candidates, not auto-fixes:\n' "$total"
echo "read each in context and apply .claude/skills/pt-pt-quality/references/pt-pt-guide.md."
