# add-language reference: exact files, scripts, and register table

Run everything from the repo root with the project virtualenv (`.venv/bin/python`).

## A. Code files that need a new per-locale entry

These are the only code files that hardcode the locale set. Everything else reads
`build/locales.py` `REQUIRED_LOCALES` and follows automatically.

| File | What to add |
|---|---|
| `build/locales.py` | the code in `SYNCED_LOCALES` |
| `build/render/strings.py` | a full `"<code>": { ... }` `UI` block, every en-GB key translated |
| `build/render/library.py` | `_LANG_NAME["<code>"] = "<Endonym>"` and a `_LEVEL_LABELS["<code>"]` row (`simple`/`rich`/`atlas`) |
| `build/render/theme.py` | `"<code>": "_"` in the `Theme.default()` placeholder world `name` |
| `build/spelling.py` | the code in `_SCOPED_LOCALES` |

The README language **columns** in `build/render/library.py` come from
`REQUIRED_LOCALES` (the `locales = REQUIRED_LOCALES` line in `readme_block`), so they
extend on their own. Do not re-hardcode them.

## B. Test files

| File | What to do |
|---|---|
| `tests/conftest.py` | add the locale to both fixtures everywhere a per-locale map appears (world name, canon names+description, story title, content dirs, idea-bank loop, lexicon term, image alts) |
| `tests/test_locales.py` | update the `REQUIRED_LOCALES` tuple and `missing_locales` expectations and the all-present mapping |
| other `tests/*.py` | add the locale to every inline per-locale map (mirror the it-IT value; real translation not needed); leave negative-path tests untouched |

## C. Content per world (repeat for every `worlds/<world>/`)

- `world.yaml`: `name`, `lore_summary`, every image `alt`.
- `canon/*.yaml`: every entry `names` + `description`.
- `heroes.yaml`: every `hero_of`, every `carry` item, every image `alt`.
- `content/<code>/idea-bank.md`.
- per story `stories/<story>/`: `story.yaml` `title` + image `alt`s, and
  `content/<code>/{narration.simple.md,narration.rich.md,rules.md,puzzles.md}`.

Do **not** translate: `visual_style`, `tone`, image `prompt`, hero `name`, canon
`id`, `first_seen`, tags, dice, palette, fonts.

## D. Repo-wide content

- `lexicon/terms.yaml`: every entry `names`.
- `guide/<code>/guide.md`: translate the whole Guide from `guide/en-GB/guide.md`.

## E. Docs and skills

- `README.md`: the explicit language list and the "N languages" count (intro,
  the per-kit line, the create-your-own section).
- `CLAUDE.md`: the status sentence's locale list and the **Languages** convention
  bullet (add the register note).
- `CONTRIBUTING.md`: the language list (or keep generic).
- `.claude/skills/authoring-story-content/SKILL.md`: add a register bullet for the
  new language in rule 3, and refresh the synced-locale parentheticals.

## F. Verification scripts

UI string key parity (a test also enforces this):

```bash
.venv/bin/python -c "from build.render import strings; from build.locales import REQUIRED_LOCALES; \
  [exec('assert set(strings.UI[l])==set(strings.UI[\"en-GB\"]), l') for l in REQUIRED_LOCALES]; print('UI keys OK')"
```

Whole-tree YAML parse + missing-locale scan (catches the `: ` colon trap and any map
that forgot the new locale):

```bash
.venv/bin/python - <<'PY'
import yaml, pathlib
from build.locales import REQUIRED_LOCALES
REQ=set(REQUIRED_LOCALES); bad=0
for f in sorted(pathlib.Path("worlds").rglob("*.yaml"))+[pathlib.Path("lexicon/terms.yaml")]:
    try: data=yaml.safe_load(f.read_text())
    except Exception as e: print("PARSE ERROR",f,str(e).splitlines()[0]); bad+=1; continue
    def walk(o):
        global bad
        if isinstance(o,dict):
            if "en-GB" in o and REQ-set(o): print(f,"missing",sorted(REQ-set(o))); bad+=1
            for v in o.values(): walk(v)
        elif isinstance(o,list):
            for v in o: walk(v)
    walk(data)
print("ALL CLEAN" if not bad else f"{bad} problems")
PY
```

No em or en dashes anywhere in the new content:

```bash
grep -rnP "[\x{2013}\x{2014}]" worlds/ guide/ lexicon/ build/ .claude/ && echo "DASHES FOUND" || echo "no dashes"
```

Full gate:

```bash
.venv/bin/python -m build validate --root .
.venv/bin/python -m build lint --root . | grep -c '\[error\]'   # expect 0
.venv/bin/python -m pytest -q
```

## G. Register table (extend it as languages are added)

The canonical voice is en-GB; every other locale is synced, specific, and must not
drift into a sibling variant.

| Locale | Players pronoun | Notes / never |
|---|---|---|
| `en-GB` | (canonical) | British spelling and idiom (colour, organise, maths). Never US English. |
| `es-ES` | vosotros | Peninsular Spanish, full accents. Never Latin American. |
| `it-IT` | voi | Natural, warm Italian, full accents. |
| `pt-PT` | vocês (and tu for a single child) | European Portuguese, full accents. Never Brazilian. |

When you add a row here, also add the matching register bullet to rule 3 of the
`authoring-story-content` skill, so future authors keep the voice right.

## H. Reminders

- Rebuild is **foreground only** (`python -m build rebuild --root . --out-dir kits`):
  the Stop-hook auto-commit can race a backgrounded rebuild and commit a partial tree.
- Commit sources clean **before** rebuilding so versions are not stamped dirty (`+`).
- Art is locale-neutral and text-free; adding a language regenerates **no** images.
- The generated trail map labels come from the `## Stop N:` headings, so translate
  those as short place names.
