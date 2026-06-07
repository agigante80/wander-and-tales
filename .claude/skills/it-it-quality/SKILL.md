---
name: it-it-quality
description: Use when writing, translating, or reviewing Wander & Tales content in Italian (it-IT), or before publishing an it-IT build. It guards against the recurring problems (the formal "Lei" for players instead of "voi", stiff textbook phrasing instead of warm colloquial Italian, anglicisms, and homograph accent slips like e/e or da/da) and enforces the project rules (no-lose tone, no dashes, canon names, associational claims). Trigger on "check the Italian", "review it-IT", "is this natural Italian", "fix the Italian register", "before publishing Italian", or any task that authors or edits it-IT prose. The add-language skill invokes this when the new locale is it-IT.
---

# Keeping Italian (it-IT) natural and warm

Wander & Tales ships Italian that sounds like a warm parent talking to a child,
never stiff or textbook-literal. The two things to protect are the register
(address the players as "voi", never the formal "Lei") and the warmth (natural,
colloquial, cosy, not grammatically correct but cold). This skill is the guard and
the cleanup tool.

LanguageTool's Italian is thin (spelling and accents only, around 140 rules), so
this skill and a native reviewer carry the grammar and the warmth. The rules live
in `references/it-it-guide.md` (register, warmth, anglicisms, the homograph
accents, and the project rules). Read it before writing or reviewing it-IT.

## When writing or translating it-IT

Load `references/it-it-guide.md` and obey it alongside the `authoring-story-content`
skill. The two things to get right every time:

1. Address the group of players as **"voi" with 2nd person plural verbs** ("fate",
   "leggete", "vostro", "vi"), a single child as **"tu"**. Never the formal "Lei".
2. Write **warm and colloquial**, the way a kind parent speaks ("dai, proviamo
   insieme!", "che bello!"), not stiff or literal ("tentiamo di procedere").

## When reviewing it-IT (the "keeps an eye on it" job)

Two passes: a mechanical scan to gather candidates, then a judgment pass. Italian
leans more on the judgment pass than the other locales, because warmth and the
homograph accents cannot be found by a scanner.

### Pass 1: scan (two finders, different jobs)

Run both. They catch different problems, so use them together.

```bash
# A. Project register, anglicisms, tone (things LanguageTool cannot see):
bash .claude/skills/it-it-quality/scan.sh                 # all it-IT content
bash .claude/skills/it-it-quality/scan.sh worlds/<world>/stories/<story>/content/it-IT/*.md

# B. Spelling and accents (things scan.sh cannot see), via the self-hosted
#    LanguageTool server (URL from .env: LANGUAGETOOL_URL):
.venv/bin/python -m build check-lang --root . --locale it-IT
.venv/bin/python -m build check-lang --root . --locale it-IT --world <world> --story <story>
```

`scan.sh` finds the formal "Lei", anglicisms, dashes, the "pò" misspelling, and
no-lose tone slips. `check-lang` finds spelling and missing accents on non-words.
Neither finds the homograph accents (e/è, da/dà, sì/si, lì/li) or the warmth: both
are a reading job. LanguageTool's Italian is the weakest of the four locales, so
expect it to catch less; the judgment pass and a native reviewer carry the weight.
Both are candidate finders; expect false positives (for example "Lei" meaning
"she" at the start of a sentence). The judgment pass decides.

`check-lang` needs the self-hosted LanguageTool server reachable at
`$LANGUAGETOOL_URL` (see `.env.example`). If it is down, `check-lang` exits
non-zero; `scan.sh` still runs without it.

### Pass 2: judgment and fix

For each candidate, and reading for warmth throughout, apply
`references/it-it-guide.md`.

- Convert any formal "Lei" address for the players to "tu" or "voi".
- Rewrite stiff, literal phrasing into warm, spoken Italian.
- Check the homograph accents by hand (è/e, dà/da, sì/si, lì/li, né/ne, sé/se).
- Preserve everything else exactly: meaning, full accents, Markdown structure
  (heading levels and count, `## Stop N` headings as short place names, tables,
  italic prompt lines, bold labels), and the canon names.
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
if it-IT prose on a page changed, and commit and push.

## Scope and siblings

This skill covers it-IT. Its siblings are `pt-pt-quality` (European Portuguese,
guards the archaic "vós" register) and `es-es-quality` (peninsular Spanish, guards
"ustedes" address and Latin-American vocabulary). All three share the same shape (a
register guide plus a scanner) and the same `build check-lang` mechanical finder;
only the register guide is per locale. en-GB has no skill: it is the canonical
source and is covered by `authoring-story-content`.
