---
name: es-es-quality
description: Use when writing, translating, or reviewing Wander & Tales content in peninsular Spanish (es-ES, Spain), or before publishing an es-ES build. It guards against the recurring problems (addressing the players as "ustedes" instead of "vosotros", voseo, and Latin-American vocabulary) plus spelling and accent drift, and it enforces the project rules (no-lose tone, no dashes, canon names, associational claims). Trigger on "check the Spanish", "review es-ES", "is this peninsular Spanish", "fix the Spanish register", "before publishing Spanish", or any task that authors or edits es-ES prose. The add-language skill invokes this when the new locale is es-ES.
---

# Keeping peninsular Spanish (es-ES) correct

Wander & Tales ships Spanish from Spain, never Latin American Spanish (which the
project treats as a separate language added later, like en-GB versus en-US). The
two traps are addressing the players as "ustedes" instead of "vosotros", and
Latin-American vocabulary. This skill is the guard against them and the tool for
cleaning up.

The rules live in `references/es-es-guide.md` (register, the ustedes-to-vosotros
table, voseo, vocabulary, accents, and the project rules). Read it before writing
or reviewing es-ES.

## When writing or translating es-ES

Load `references/es-es-guide.md` and obey it alongside the `authoring-story-content`
skill. The two things to get right every time:

1. Address the group of players as **"vosotros" with 2nd person plural verbs**
   ("hacéis", "leed", "vuestro", "os"), a single child as **"tú"**. Never
   "ustedes" or 3rd person plural for the players, and never voseo.
2. Use **peninsular vocabulary** (coche, ordenador, móvil, zumo, patata, vale,
   guay), never the Latin-American word.

## When reviewing es-ES (the "keeps an eye on it" job)

Two passes: a mechanical scan to gather candidates, then a judgment pass.

### Pass 1: scan (two finders, different jobs)

Run both. They catch almost entirely different problems, so use them together.

```bash
# A. Project register, vocabulary, tone (things LanguageTool cannot see):
bash .claude/skills/es-es-quality/scan.sh                 # all es-ES content
bash .claude/skills/es-es-quality/scan.sh worlds/<world>/stories/<story>/content/es-ES/*.md

# B. Grammar, spelling, accents (things scan.sh cannot see), via the
#    self-hosted LanguageTool server (URL from .env: LANGUAGETOOL_URL):
.venv/bin/python -m build check-lang --root . --locale es-ES
.venv/bin/python -m build check-lang --root . --locale es-ES --world <world> --story <story>
```

`scan.sh` finds ustedes address, voseo, Latin-American vocabulary, dashes, and
no-lose tone slips. `check-lang` finds spelling and accent errors. LanguageTool
has solid general Spanish grammar and accents but **no peninsular register**: it
will not enforce "vosotros" or flag a Latin-Americanism, so that judgment is this
skill's job. Both are candidate finders; expect false positives (for example
"papa" meaning pope, canon names flagged as spelling). The judgment pass decides.

`check-lang` needs the self-hosted LanguageTool server reachable at
`$LANGUAGETOOL_URL` (see `.env.example`). If it is down, `check-lang` exits
non-zero; `scan.sh` still runs without it.

### Pass 2: judgment and fix

For each candidate, read it in context and apply `references/es-es-guide.md`.

- Convert "ustedes" address to "vosotros" using the table (mind the reflexive
  imperative dropping its "-d": "sentaos", not "sentados").
- Replace Latin-American vocabulary with the peninsular word.
- Preserve everything else exactly: meaning, warmth, full accents, Markdown
  structure (heading levels and count, `## Stop N` headings as short place names,
  tables, italic prompt lines, bold labels), and the canon names.
- Run the reviewer checklist at the end of the guide before calling a file done.

## After fixing

Validate, rebuild, and commit like any content change:

```bash
.venv/bin/python -m build validate --root .   # OK
.venv/bin/python -m build lint --root .       # 0 errors
.venv/bin/python -m pytest -q                 # green
.venv/bin/python -m build rebuild --root . --out-dir kits   # FOREGROUND only
```

Rebuild in the foreground (never backgrounded: the Stop-hook auto-commit can race
a backgrounded rebuild and commit a partial kits tree). Then rebuild the website
if es-ES prose on a page changed, and commit and push.

## Scope and siblings

This skill covers es-ES. Its siblings are `pt-pt-quality` (European Portuguese,
guards the archaic "vós" register and Brazilian usage) and `it-it-quality` (warm,
natural Italian with "voi"). All three share the same shape (a register guide plus
a scanner) and the same `build check-lang` mechanical finder; only the register
guide is per locale. en-GB has no skill: it is the canonical source and is covered
by `authoring-story-content`.
