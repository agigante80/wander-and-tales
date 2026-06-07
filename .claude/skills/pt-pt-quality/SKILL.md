---
name: pt-pt-quality
description: Use when writing, translating, or reviewing Wander & Tales content in European Portuguese (pt-PT), or before publishing a pt-PT build. It guards against the two recurring native-speaker problems (the archaic "vós" register and Brazilian gerunds) plus pt-BR vocabulary, wrong clitic placement, and spelling drift, and it enforces the project rules (no-lose tone, no dashes, canon names, associational claims). Trigger on "check the Portuguese", "review pt-PT", "is this European Portuguese", "fix the Portuguese register", "before publishing Portuguese", or any task that authors or edits pt-PT prose. The add-language skill invokes this when the new locale is pt-PT.
---

# Keeping European Portuguese (pt-PT) correct

Wander & Tales ships European Portuguese (Portugal), never Brazilian. A
native-speaker review found the whole pt-PT corpus had been authored in the
archaic "vós" register with Brazilian gerunds: both wrong for Portugal, both easy
for a non-native model to produce because textbooks teach them. This skill is the
guard so it does not happen again, and the tool for cleaning up when it has.

The rules live in `references/pt-pt-guide.md` (register, the full "vós" to "vocês"
conversion table, gerunds, clitics, vocabulary, spelling, and the project rules).
Read it before writing or reviewing pt-PT.

## When writing or translating pt-PT

Load `references/pt-pt-guide.md` and obey it alongside the `authoring-story-content`
skill. The two things to get right every time:

1. Address the group as **"vocês" with 3rd person plural verbs** ("Leiam",
   "São", "fizeram"), a single child as **"tu"**. Never "vós" or its 2nd person
   plural verbs.
2. Use **"a + infinitivo"** for ongoing actions ("está a dormir"), never the
   gerund ("dormindo").

## When reviewing pt-PT (the "keeps an eye on it" job)

Two passes: a mechanical scan to gather candidates, then a judgment pass.

### Pass 1: scan (two finders, different jobs)

Run both. They catch almost entirely different problems, so use them together.

```bash
# A. Project register, vocabulary, tone (things LanguageTool cannot see):
bash .claude/skills/pt-pt-quality/scan.sh                 # all pt-PT content
bash .claude/skills/pt-pt-quality/scan.sh worlds/<world>/stories/<story>/content/pt-PT/*.md

# B. Grammar, spelling, accents (things scan.sh cannot see), via the
#    self-hosted LanguageTool server (URL from .env: LANGUAGETOOL_URL):
.venv/bin/python -m build check-lang --root . --locale pt-PT
.venv/bin/python -m build check-lang --root . --locale pt-PT --world <world> --story <story>
```

`scan.sh` finds the archaic "vós" register, Brazilian gerunds, pt-BR vocabulary,
dashes, and no-lose tone slips. `check-lang` finds spelling, accent, and agreement
errors. Both are candidate finders, not auto-fixers; expect false positives (for
example "verdes", "testes", "quando", "lindo" from the scanner, and canon names
flagged as spelling by LanguageTool). The judgment pass decides.

`check-lang` needs the self-hosted LanguageTool server reachable at
`$LANGUAGETOOL_URL` (see `.env.example`). If it is down, `check-lang` exits
non-zero and prints the URL it tried; `scan.sh` still runs without it.

### Pass 2: judgment and fix

For each candidate, read it in context and apply `references/pt-pt-guide.md`.

- **Never blind-replace "vós" forms.** The conjugations are irregular; use the
  conversion table in the guide (sois to são, Lede to Leiam, fizestes to fizeram,
  enfrentardes to enfrentarem, and so on). Keep "vosso/vossa" and the "-vos"
  clitic where they read naturally with "vocês".
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
if pt-PT prose on a page changed, and commit and push.

## Scope and siblings

This skill covers pt-PT. The same shape (a register guide plus a scanner) suits
the other synced locales: es-ES has its own peninsular-Spanish review history
(avoid Latin-Americanisms, use vosotros) and it-IT prefers warm colloquial Italian
(voi). If those grow their own guards, mirror this layout under a sibling skill.
