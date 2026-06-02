# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Wits & Wonder is a public, multilingual library of **printable, cooperative,
adult-led story-adventure kits for kids** (print-and-play PDFs played with simple
dice and household objects). It is not a digital game. Worlds contain stories;
content is data and a layout-only build renders the PDFs.

## Status

The full, approved design lives at
`docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`;
treat the spec as the source of truth. The work is split into a sequence of plans
under `docs/superpowers/plans/`.

**Plans 1 and 2 are built.** Plan 1 (content model and tooling): the `build`
package, its pytest suite, and the `validate`/`lint`/`catalog` CLI. Plan 2 (PDF
build pipeline): the `build/render/` package (font embedding, the markdown to
PDF renderer, themed pages, glossary from canon, SVG map merge, character sheets,
kit assembly, the Guide renderer) and the `render`/`render-guide` CLI. The
Floating Isles / Sleeping Garden content already exists, so real kits build into
`dist/`. Still to come: the remaining `worlds/`, `lexicon/`, and `guide/` content
(Plans 3 to 5). `tests/conftest.py` still builds a tiny valid world on a tmp path
for the data-layer tests.

## Commands

Use the project virtualenv at `.venv/`.

```bash
.venv/bin/python -m pytest                 # whole suite (config in pyproject.toml)
.venv/bin/python -m pytest tests/test_lint.py            # one file
.venv/bin/python -m pytest tests/test_lint.py::test_name # one test
.venv/bin/python -m pytest -k catalog                    # by keyword

.venv/bin/python -m build validate --root .   # load + validate all content
.venv/bin/python -m build lint --root .       # structural lint (exit 1 on error)
.venv/bin/python -m build catalog --root . --out catalog.md

.venv/bin/python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple        # build one kit PDF into dist/
.venv/bin/python -m build render-guide --root . --locale en-GB  # build the Guide PDF
.venv/bin/python -m build prompts --root .            # export image generation prompts
.venv/bin/python -m build generate-images --root .    # generate PNGs (needs OPENAI_API_KEY in .env)
```

Install (editable) into a fresh venv with `pip install -e ".[dev,render]"`. Core
runtime deps are `pydantic>=2.6` and `PyYAML>=6.0`; the `render` extra adds
`reportlab`, `cairosvg`, and `pypdf` (see `pyproject.toml`). DejaVu Sans and Serif
are vendored under `build/assets/fonts/` and embedded, so accents render and the
build never depends on system fonts.

## Architecture

The `build/` directory is an importable Python package (`from build.models import
Story`), not a build-artifact folder. Rendered output goes to `dist/` (gitignored),
so there is no clash. Data flows in one direction:

- **Vocabularies are the single source of truth.** `locales.py` (canonical
  `en-GB`, synced `es-ES`), `tags.py` (age tiers, skills, peril, reading levels and
  the reading-level to age-tier map), and `dice.py` (Easy/Normal/Hard bands, the
  `1d6` floor, per-dice-set thresholds) define the allowed values. Everything else
  imports these constants instead of hardcoding strings.
- **Models enforce the schema.** `models.py` holds strict pydantic v2 models
  (`extra="forbid"`) for `World`, `Story`, `CanonEntry`, `LexiconTerm`. Validators
  call into the vocabularies: a story's `dice.minimum` must be `1d6`, every
  per-locale map (`title`, `names`, ...) must carry all `REQUIRED_LOCALES`, skills
  and peril and age tiers must be known. Invariants live here, not in callers.
- **Loaders read disk into models.** `content.py` parses YAML into those models.
  The content layout it expects: `worlds/<world>/world.yaml`,
  `worlds/<world>/canon/*.yaml` (lists of canon entries),
  `worlds/<world>/stories/<story>/story.yaml`, that story's prose under
  `content/<locale>/` (`narration.simple.md`, `narration.rich.md`, `rules.md`,
  `puzzles.md`, `idea-bank.md`), and a repo-wide `lexicon/terms.yaml`.
- **Lint and catalog consume models.** `lint.py` runs deterministic structural
  checks (unique canon/lexicon ids, story `world` matches its directory, every
  required content file present for every required locale) and returns
  `LintIssue`s. `catalog.py` generates `catalog.md` from every `story.yaml` so the
  catalog can never drift from the tags. `__main__.py` wires these into the CLI.
- **`spelling.py` is a deliberate stub.** The path-scoped en-GB/es-ES spelling
  lint is deferred until locale content exists; `check_text` returns no findings
  today so callers can wire the seam in safely.
- **`fontspec.py` is the font vocabulary.** It is the single source of truth for
  which typefaces exist (family key to TTF faces); the model validates the world
  `fonts` block against it. A world declares its typeface in `world.yaml` under
  `fonts` (a `default` family plus an optional `by_locale` override); resolution
  is `by_locale[locale]`, then `default`, then the global default family.
- **`build/render/` is the layout-only PDF pipeline.** Builders take
  `(world, story, locale, reading_level)` and never hardcode a colour, font, or
  path. `markdown.py` parses the content GFM, `theme.py` themes pages from the
  world palette and resolved faces, `flowables.py`/`pages.py` render, `glossary.py`
  builds the appendix from canon, `map.py` renders the SVG via cairosvg, `sheets.py`
  draws the age-tiered character sheets, and `kit.py` merges the ordered pages with
  pypdf into `dist/`. Output is `dist/<world>_<story>_<locale>_<level>.pdf`.
- **Maps are world-level or story-level, and may be per-locale.** A story map
  lives at `worlds/<world>/stories/<story>/assets/`, a world map at
  `worlds/<world>/assets/`. `map.py:find_map` resolves a kit's map in order: story
  map for the locale (`map.<locale>.svg`), story map generic (`map.svg`), then the
  same two at the world level. When the art has baked-in text, add a
  `map.<locale>.svg`; a locale with no matching map omits the map page rather than
  showing another language's labels. A map may also be a neutral template: text
  becomes `data-label` placeholders that `map.py:render_map_template` fills per
  locale from the story title, canon names, and `map_*` UI strings, so one `map.svg`
  serves every language. The Sleeping Garden uses this (its old `map.es-ES.svg` is
  gone), so en-GB kits now include the map too.

Authoring any kid-facing or grown-up-facing prose or YAML content is a content
task, not a coding task: use the `authoring-story-content` skill, which encodes
the voice, reading-level, peril-tone, and canon-name rules.

## Writing rule (must follow)

**Never use em dashes or en dashes anywhere**, in any file or text. Use a hyphen
only to connect words; do not use a hyphen as a substitute for an em or en dash.
Rewrite with commas, parentheses, a colon, or separate sentences. For number
ranges write "3 to 5", not a dash. A `PreToolUse` hook in `.claude/` enforces
this for file writes and edits (it activates on a normal session start).

## Core conventions (from the spec)

- **Languages**: British English (`en-GB`) is canonical; Spanish from Spain
  (`es-ES`) is kept in sync. These are specific locales: write British spelling
  and idiom, and peninsular Spanish (vosotros, full accents). US English, Latin
  American Spanish, and any other locale are treated as separate languages that
  slot in later with no code changes (like `pt-PT` versus `pt-BR`); never mix an
  Americanism into `en-GB` or a Latin turn of phrase into `es-ES`.
- **Content-driven**: content is text plus YAML metadata; Python builders are
  layout-only and take `(world, story, language, reading_level)`. Adding a world,
  story, language, or age tier is a content task, not a coding task.
- **Dice**: rules use abstract difficulty bands (Easy/Normal/Hard); every story
  must be playable with a single d6.
- **Tags**: age tiers `early`/`young`/`older`; peril `gentle`/`mild`/`heroic`;
  plus skills, players, play time. An `adult_gm` badge appears on every kit.
- **Canon**: each world has a name registry (`canon/`) and there is a repo-wide
  `lexicon/`; story prose follows canon, checked by a lightweight lint.
- **Fonts**: embed a Unicode font so accents render. DejaVu Sans and Serif are
  vendored; a world picks its typeface in `world.yaml` under `fonts` (a `default`
  family plus an optional `by_locale` override), validated against `fontspec.py`.
- **`visuals.py` is the image vocabulary** (roles, orientations). Worlds and
  stories declare illustrations in YAML (`images:`, plus a world `visual_style`).
  `prompts.py` composes copy-paste prompts (locale-neutral, text-free art; only
  `alt` is localized) and `generate.py` turns them into PNGs in `assets/` via the
  OpenAI Images API (the optional `images` extra: `pip install -e ".[images]"`, key
  from `.env`). Embedding images into PDFs is a later step.

## Verification

Per the spec, every authored `(story, language, reading_level)` combination must
build without error, and the canon/lexicon lint must pass with no warnings. The
PDF pipeline exists (Plan 2): after generating any PDF, rasterize it to PNG (for
example `pdftoppm -png -r 110 file.pdf out`) and eyeball it before declaring it
done; confirm accents render, layout is intact, and the map merges correctly.

## Layout pointers

- `build/render/` is the live PDF pipeline (Plan 2). The Sleeping Garden's story
  map is at `worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg`
  (es-ES only so far; see the map-resolution note in Architecture).
- The legacy `El_Jardin_Dormido_kit/` scripts have been removed: they were fully
  superseded by `build/render/` and their content was migrated into the schema.
  Recover the old `reportlab` decorative-drawing code from git history (it was
  deleted on the Plan 2 branch) if the canvas-drawn motifs are ever wanted.
- `research/` evidence base and marketing copy.
- `docs/superpowers/specs/` design specs; `docs/superpowers/plans/` the plan set.

## Git

This is an open-source project: **commit and push at every change.** After each
logical change (a file or a small coherent set), make a descriptive commit and
push it to `origin`; do not leave work uncommitted or unpushed. A `Stop` hook in
`.claude/` is the backstop that auto-commits and pushes anything still pending
when a turn ends, so nothing is ever lost. End every commit message with the
standard co-author trailer. Work on `main`.
