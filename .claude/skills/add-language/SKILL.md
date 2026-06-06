---
name: add-language
description: Use when a maintainer wants to add a whole new language (locale) to the Wander & Tales project, for example "add German", "add European Portuguese", "add pt-BR", "support French", "translate the whole project into Polish". This is the maintainer-side, project-wide counterpart to create-story (which adds one story). It wires the locale through the build code, the test fixtures, every world's content (canon, heroes, idea banks, and every story at both reading levels), the repo-wide lexicon and the shared Guide, updates the docs and skills, then validates, rebuilds every kit, and publishes. Defers all voice, register, reading-level, peril-tone, and canon-name rules to the authoring-story-content skill. Trigger on "add <language>", "add a language", "support <language>", "make the kits available in <language>".
---

# Adding a language to Wander & Tales

The whole architecture rests on a list of synced locales (`build/locales.py`
`REQUIRED_LOCALES`). The models enforce that **every** localized field in **every**
world and story carries **all** of them, so adding a locale is all-or-nothing: until
every world, story, canon entry, hero set, idea bank, the lexicon and the Guide carry
the new language, nothing validates and nothing builds. This skill does that end to
end and leaves the maintainer with rebuilt PDFs, updated docs, and a published
library.

The goal: the maintainer says "add German" and you take every file and action
without further hand-holding, finishing with built kits and everything (skills,
READMEs, catalogue) correct.

Expect this to be large: roughly `(worlds x 13) + lexicon + guide` content files plus
many YAML maps. Fan the translation out across parallel subagents. Art does **not**
need regenerating: illustrations are locale-neutral and text-free; only the `alt`
text and the prose are per-language.

## Step 0: load the authoring rules

**Invoke the `authoring-story-content` skill first** and obey it for every piece of
prose and YAML: the no-lose ethos, the no em or en dash rule (a hook blocks file
writes containing one), the associational (non-causal) claims rule, reading levels,
peril tone, and canon-name discipline. It also holds the per-language register list,
which this skill extends.

## Step 1: pin down the locale (ask the maintainer)

The project uses **specific regional locales**, never a bare language (en-GB not en,
es-ES not es, pt-PT not pt). With `AskUserQuestion`, confirm:

- **The exact code** (e.g. `de-DE`, `fr-FR`, `pt-BR`, `en-US`, `es-419`). If the
  language has variants the project might want separately (pt-PT vs pt-BR, en-GB vs
  en-US), confirm which one; the other is a different locale added later.
- **The endonym** (native name) for the README link label and `_LANG_NAME`
  (e.g. "Deutsch", "Français", "Português"). Avoid dashes.
- **The register**: the pronoun used for the group of players (vosotros / voi / vocês
  / ihr / vous), the pronoun for a single child in italic prompts, and any spelling or
  idiom rules. Note explicitly that it must never drift into a sibling variant.
- **The localized tagline** (translate "Stories to wander through together").
- **The README level labels**: the new-language equivalents of "Tale (Simple)",
  "Tale (Rich)", and "Atlas".

## Step 2: wire the build code (deterministic)

Make these exact edits, then prove the strings parity:

1. `build/locales.py`: add the code to `SYNCED_LOCALES`.
2. `build/render/strings.py`: add a full `"<code>": { ... }` block to `UI` with
   **every** key that the `en-GB` block has, translated. A test
   (`tests/test_render_strings.py`) enforces that every locale has exactly the same
   keys, so copy the en-GB key set and translate the values. Mind the placeholders:
   keep `{number}`, `{updated}`, `{locale}`, `{code}`, `{url}` intact.
3. `build/render/library.py`: add the code to `_LANG_NAME` (the endonym) and to
   `_LEVEL_LABELS` (`simple`/`rich`/`atlas`). The README language **columns** are
   derived from `REQUIRED_LOCALES`, so there is nothing else to change there.
4. `build/render/theme.py`: add `"<code>": "_"` to the placeholder world `name` in
   `Theme.default()` (it validates against the model, which now requires the locale).
5. `build/spelling.py`: add the code to `_SCOPED_LOCALES`.

Verify:

```bash
.venv/bin/python -c "from build.render import strings; from build.locales import REQUIRED_LOCALES; \
  [exec('assert set(strings.UI[l])==set(strings.UI[\"en-GB\"]), l') for l in REQUIRED_LOCALES]; print('UI keys OK')"
.venv/bin/python -m pytest tests/test_render_strings.py -q
```

## Step 3: extend the test fixtures

Adding the locale makes every fixture-built world fail until it carries the locale:

- `tests/conftest.py`: in **both** fixtures (`sample_repo`, `repo_with_images`), add
  the locale everywhere a per-locale map appears: world `name`, canon `names` +
  `description`, story `title`, the content directories, the idea-bank locale loop, the
  lexicon term `names`, and every image `alt`.
- `tests/test_locales.py`: update the `REQUIRED_LOCALES` tuple and the
  `missing_locales` expectations (and the all-present mapping).
- Inline fixtures across `tests/*.py`: add the locale to every per-locale map. For
  fixtures the value need not be a real translation; mirror the `it-IT` value. Leave
  negative-path tests that deliberately omit a locale untouched.

This is mechanical and safe to delegate to one subagent. Then run the whole suite
green before touching content.

## Step 4: translate all existing content (fan out)

For **each** world under `worlds/*`, add the new locale to:

- `world.yaml`: `name`, `lore_summary`, and every image `alt` (NOT `visual_style`,
  `tone`, or any image `prompt`, which stay English and locale-neutral).
- `canon/*.yaml`: every entry's `names` **and** `description`. Choose natural
  canon names for the world and use them **consistently** in that world's prose.
- `heroes.yaml`: each `hero_of`, each `carry` item, and each image `alt` (NOT the
  hero `name` or the image `prompt`).
- `content/<code>/idea-bank.md` (translate from `content/en-GB/idea-bank.md`).
- every story: `story.yaml` `title` + every image `alt`; and
  `content/<code>/{narration.simple,narration.rich,rules,puzzles}.md`.

Plus repo-wide: `lexicon/terms.yaml` (every `names` map) and `guide/<code>/guide.md`
(translate the whole Guide).

**Dispatch one subagent per world in parallel**, plus one for the lexicon and Guide.
Give each subagent the register rules from Step 1, the canon-name-consistency rule,
the no-dash rule, and this structure rule: preserve the Markdown exactly (same heading
levels and count, same number of `## Stop N` headings in order, same tables with the
same row count, same italic prompt lines, same bold labels), and translate each
`## Stop N:` heading as a **short place name** (about 2 to 4 words) because the
headings become the generated map's labels.

### Gotchas (these bit us adding pt-PT; warn every subagent)

- **Native register, not textbook (the biggest miss).** Adding pt-PT, the subagents
  wrote the archaic "vós" register and Brazilian gerunds throughout, both wrong for
  Portugal and both the textbook default a non-native model reaches for. Every
  language has an equivalent trap (the form a learner is taught versus what natives
  actually say). Give each subagent the specific native forms to use and to avoid,
  not just the pronoun name. For pt-PT, route them through the **`pt-pt-quality`**
  skill (its register guide and scanner) and scan every file before you validate.
  When you add a new language, consider leaving behind a sibling guard skill the
  same way.
- **YAML colon trap.** A `: ` (colon then space) inside an **unquoted** YAML scalar
  value breaks parsing with "mapping values are not allowed here". Do not put `: `
  inside a canon `name` or `description` value; use a full stop, comma, or semicolon
  instead, or quote the whole value. After translating, parse-check every YAML file.
- **Identical names still need the key.** Even when a name is spelled the same in the
  new language (a proper noun like "Barcelos"), add the explicit `"<code>": Name`
  entry, or the model rejects the map as missing the locale.
- **strings.py key parity** is enforced by a test; the new UI block must have exactly
  the en-GB keys.

## Step 5: verify

```bash
.venv/bin/python -m build validate --root .   # must print OK
.venv/bin/python -m build lint --root .       # 0 [error] lines (image warnings are fine)
.venv/bin/python -m pytest -q                 # all green
```

Then run the whole-tree parse and missing-locale scan in
`references/checklist.md`, and **build one sample** in the new locale and eyeball it:

```bash
.venv/bin/python -m build render-tale-book --root . --world <w> --story <s> --locale <code> --reading-level simple
.venv/bin/python -m build render-atlas     --root . --world <w> --story <s> --locale <code>
.venv/bin/python -m build render-examples  --root . --world <w> --locale <code>
# rasterize a page each (pdftoppm -png -r 90 file.pdf out) and confirm:
#  - accents render, layout intact
#  - the generated trail map's START/stop/GOAL labels are in the new language
#  - the hero sheet's UI strings (magics/strengths, energy, "nobody loses") translate
```

## Step 6: update the docs and skills

Most internal prose now phrases the set as "`REQUIRED_LOCALES`", so it needs no edit.
Update the spots that name the languages explicitly or count them:

- **README**: the marketing language list and the "N languages" count (the intro
  line, the "comes in N languages" line, the create-your-own section, and the
  language list in the closing of that section). Keep these explicit and friendly.
- **CLAUDE.md**: the status sentence's locale list, and the **Languages** convention
  bullet (add the new register note: pronoun, spelling, "never drift into <sibling>").
- **CONTRIBUTING.md**: extend or keep generic.
- **`authoring-story-content` SKILL**: add a register bullet for the new language in
  rule 3 (the per-language list), and refresh the synced-locale parentheticals.
- Leave **this** skill and **create-story** as-is; they reference `REQUIRED_LOCALES`
  and do not enumerate.

## Step 7: rebuild and publish

1. Commit the source content **clean first**, so git-derived versions are not stamped
   dirty (no `+` suffix).
2. Run the full rebuild in the **FOREGROUND ONLY** (never backgrounded: the Stop-hook
   auto-commit can race a partial `kits/` tree):

   ```bash
   .venv/bin/python -m build rebuild --root . --out-dir kits
   ```

   It builds every kit in the new language and relinks the README catalogue; the new
   language column appears automatically (it is derived from `REQUIRED_LOCALES`). It
   also refreshes `site/manifest.json`, which the website reads.
3. Confirm no dirty `+` versions (`find kits -name '*+*'`), then commit the `kits/`
   tree, the README, and `site/manifest.json`, and push. End commit messages with the
   standard co-author trailer.

## Step 8: wire the website (`web/`)

The public site (`web/`, Astro) is locale-driven and is **not** derived from
`REQUIRED_LOCALES`, so the new language must be added there by hand:

- **`web/src/consts.ts`**: add the locale to `LANGS` (`{ code, locale, name }`, e.g.
  `{ code: "de", locale: "de-DE", name: "Deutsch" }`). The short `code` is the URL
  segment; the full `locale` keys hreflang and `og:locale`.
- **`web/src/lib/i18n.ts`**: add a UI block for the new `code` translating **every**
  key (it must match the `en` key set; missing keys fall back to English). This is the
  nav, buttons, footer, the reader labels, and the per-page meta descriptions.
- **`web/src/content/why/<code>.md`**: translate the "Why it works" page (keep the
  associational, non-causal claims and the verified source links).

Then render the new language's website trail maps and check the build:

```bash
.venv/bin/python -m build render-maps --root .   # writes maps/<world>/<story>/map-<locale>.png
cd web && npm run build                          # prepare-assets copies media/kits/maps; Astro builds every locale
```

Commit the `web/` changes, the new `maps/`, and `site/manifest.json`. The site
otherwise picks up the new language automatically from the manifest, media, and kits,
and redeploys on push.

## Quick checklist before you call it done

- [ ] Code wired: `locales.py`, `strings.py` (key parity test passes),
      `library.py` (`_LANG_NAME` + `_LEVEL_LABELS`), `theme.py`, `spelling.py`.
- [ ] Test fixtures extended; whole suite green.
- [ ] Every world + the lexicon + the Guide translated; `validate` OK, `lint` 0 errors.
- [ ] Whole-tree YAML parses; no `: ` breakage; no em or en dashes anywhere.
- [ ] A sample kit was built and eyeballed (map labels and UI strings in the new
      language).
- [ ] Docs and skills updated (marketing list, counts, the new register note).
- [ ] Website wired: `web/src/consts.ts` `LANGS`, a full `i18n.ts` UI block,
      `web/src/content/why/<code>.md`; `render-maps` run; `cd web && npm run build` OK.
- [ ] Rebuilt in the foreground, no dirty versions; `kits/`, README,
      `site/manifest.json`, `maps/`, and `web/` committed and pushed.

See `references/checklist.md` for the exact file list, the verification scripts, and
the per-language register table.
