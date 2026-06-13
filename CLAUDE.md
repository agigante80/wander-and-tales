# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Wander & Tales is a public, multilingual library of **printable, cooperative,
adult-led story-adventure kits for kids** (print-and-play PDFs played with simple
dice and household objects). It is not a digital game. Worlds contain stories;
content is data and a layout-only build renders the PDFs. A companion **website**
(the `web/` Astro site) lets people read every story online and download the
printable kits; it is a reading and discovery surface, not a way to play.

## Status

This file plus the code are the source of truth; the full design history lives in
git. The project is built and working end to end: the `build` package (content model,
validation, and the `validate`/`lint` CLI), the `build/render/` PDF
pipeline, and the content for seven worlds (Floating Isles, the Greek-myth Sunlit Hills,
the Norse Snowlit Fjords, the Japanese Blossom Mountains of Yamato, the Celtic Emerald
Isles, the Epic-Cycle Windswept Shores of Troy, and the Portuguese-folklore Enchanted
Springs), twenty-one stories in all, in en-GB, es-ES, it-IT, and pt-PT. Each story builds
into three artifacts (a Tale Book, an Atlas, and a World Book) plus the
shared Guide for the Grown-Up, every PDF carrying an automatic git-derived version, a
colophon, and a per-page footer, assembled into the language-first `kits/` tree by
`python -m build rebuild`. `tests/conftest.py` builds a tiny valid world on a tmp path
for the data-layer tests.

## Commands

Use the project virtualenv at `.venv/`.

```bash
.venv/bin/python -m pytest                 # whole suite (config in pyproject.toml)
.venv/bin/python -m pytest tests/test_lint.py            # one file
.venv/bin/python -m pytest tests/test_lint.py::test_name # one test
.venv/bin/python -m pytest -k render                     # by keyword

.venv/bin/python -m build validate --root .   # load + validate all content
.venv/bin/python -m build lint --root .       # structural lint (exit 1 on error)

.venv/bin/python -m build render-tale-book --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple        # build one Tale Book into dist/
.venv/bin/python -m build render-atlas --root . \
  --world floating-isles --story sleeping-garden --locale en-GB  # build its Atlas
.venv/bin/python -m build render-guide --root . --locale en-GB  # build the Guide PDF
.venv/bin/python -m build prompts --root .            # export image generation prompts
.venv/bin/python -m build generate-images --root .    # generate PNGs (needs OPENAI_API_KEY in .env)

.venv/bin/python -m build manifest --root .     # regenerate site/manifest.json (the website's data feed)
.venv/bin/python -m build render-maps --root .  # render every story map to a PNG into maps/ (for the website)
.venv/bin/python -m build check --root .        # LanguageTool findings for a locale (needs a LanguageTool server; see langcheck.py)
```

The website lives in `web/` (an Astro + Tailwind app deployed to Cloudflare
Workers). It is a separate npm project; run its commands from `web/`:

```bash
cd web && npm install
npm run dev      # prepare-assets (resize art, copy kits/maps/fonts) then astro dev
npm run build    # prepare-assets then astro build into web/dist/
npm run deploy    # build then wrangler deploy
npm run audit     # Lighthouse pass via unlighthouse
```

Install (editable) into a fresh venv with `pip install -e ".[dev,render]"`. Core
runtime deps are `pydantic>=2.6` and `PyYAML>=6.0`; the `render` extra adds
`reportlab`, `cairosvg`, and `pypdf` (see `pyproject.toml`). DejaVu Sans and Serif
(the world prose faces) plus the adventure-sheet faces (Quicksand display, Nunito
body, Caveat handwriting, all OFL) are vendored under `build/assets/fonts/` and
embedded, so accents render and the build never depends on system fonts.

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
  `puzzles.md`), the world-level idea bank at
  `worlds/<world>/content/<locale>/idea-bank.md` (one per world, shared by its
  stories), the world's four example heroes at `worlds/<world>/heroes.yaml` (two
  young, two older, for the sample adventure sheets), and a repo-wide
  `lexicon/terms.yaml`.
- **Lint consumes models.** `lint.py` runs deterministic structural checks (unique
  canon/lexicon ids, story `world` matches its directory, every required content file
  present for every required locale, a world idea bank per locale) and returns
  `LintIssue`s. `__main__.py` wires these into the CLI. The story catalogue is the
  generated table in the root README (rebuilt by `library.py` from every `story.yaml`,
  so it cannot drift from the tags); there is no separate `catalog.md`.
- **`spelling.py` is a deliberate stub.** The path-scoped en-GB/es-ES spelling
  lint is deferred until locale content exists; `check_text` returns no findings
  today so callers can wire the seam in safely.
- **`langcheck.py` is the grammar-checker seam.** It strips a locale's Markdown
  to plain text (preserving offsets), POSTs it to a self-hosted LanguageTool
  server, and returns normalized `Finding`s with line numbers. It is a candidate
  finder for the locale-quality skills (`es-es-quality`, `it-it-quality`,
  `pt-pt-quality`), not an auto-fixer; the CLI exposes it as `build check`.
- **`fontspec.py` is the font vocabulary.** It is the single source of truth for
  which typefaces exist (family key to TTF faces); the model validates the world
  `fonts` block against it. A world declares its typeface in `world.yaml` under
  `fonts` (a `default` family plus an optional `by_locale` override); resolution
  is `by_locale[locale]`, then `default`, then the global default family.
- **`build/render/` is the layout-only PDF pipeline.** Builders take
  `(world, story, locale, reading_level)` and never hardcode a colour, font, or
  path. `markdown.py` parses the content GFM, `theme.py` themes pages from the
  world palette and resolved faces (with `tint()` for light fills), `chrome.py` holds
  the shared, palette-driven page chrome (header band, beat chip, prompt callout,
  rounded image) reused by both the sheet and the booklets, `flowables.py`/`pages.py`
  render, `glossary.py` builds the appendix from canon (the hero qualities or magics
  come first under their own clear heading, then places, characters, creatures, items,
  and any plain terms), `map.py` renders a hand-drawn map SVG via cairosvg and
  `mapgen.py` draws a generated trail map when there is none, `sheets.py` draws the
  age-tiered character sheets, and `kit.py` holds the shared merge/image/map-label
  helpers. `tale_book.py:build_tale_book` builds the grown-up's Tale Book (title,
  read-aloud story without images, rules, answers) per reading level, and
  `atlas.py:build_atlas` builds the player-facing Atlas (cover, map, one big picture per
  place, the hero sheet). Each story is a **Tale Book** (per level) plus an **Atlas**,
  and each world also has a **World Book** plus the shared Guide; `version.py` stamps an
  automatic git-derived version, `colophon.py` adds the end page, `footer.py` the
  per-page footer, and `library.py` rebuilds the whole library. Output is a language-first
  tree with self-describing, unversioned filenames (stable URLs):
  `dist|kits/<locale>/<world>/<story>/<world>-<story>-tale-book-<level>-<locale>.pdf`,
  `.../<world>-<story>-atlas-<locale>.pdf`, and
  `.../<world>/<world>-world-book-<locale>.pdf`. The git-derived version is no longer in
  the filename; it lives in each PDF's colophon and in the `manifest.json` per-PDF entry
  (`{path, version, updated}`), so a version bump updates a file in place instead of
  renaming it.
- **Maps are world-level or story-level, and may be per-locale.** A story map
  lives at `worlds/<world>/stories/<story>/assets/`, a world map at
  `worlds/<world>/assets/`. `map.py:find_map` resolves a kit's map in order: story
  map for the locale (`map.<locale>.svg`), story map generic (`map.svg`), then the
  same two at the world level. When the art has baked-in text, add a
  `map.<locale>.svg`. A map may also be a neutral template: text becomes `data-label`
  placeholders that `map.py:render_map_template` fills per locale from the story title,
  canon names, and `map_*` UI strings, so one `map.svg` serves every language. The
  Sleeping Garden uses this (its old `map.es-ES.svg` is gone), so en-GB kits include
  the map too.
- **Every story carries a map; `mapgen.py` generates one when none is drawn.** If
  `find_map` resolves nothing, `kit.py` calls `mapgen.render_generated_map`, which
  reads the story's own narration headings (`## Stop N: Name` plus the ending) and
  draws a canvas trail map: a START, the numbered stops, and a GOAL on a winding golden
  path, themed from the world palette and labelled per locale straight from the
  headings (so it scales to every story and language with no art). It is layout-only,
  like the sheet. The layout is shape-adaptive: up to five stops it winds vertically
  with outer labels; six or more it switches to a serpentine grid with labels under
  each marker, so a short or a long story both stay one readable A4 page. A hand-drawn
  `map.svg` always wins, so an author can replace a generated map with bespoke art
  later. The generated map reads `narration.simple.md` for all levels, and `mapgen.py`
  is in `version._RENDER_SOURCES` so its edits bump the MINOR version. Map labels come
  from the stop headings, so name stops as places.
- **A world declares whether its heroes have magic.** `world.yaml` carries
  `hero_powers` (`magic` by default, or `strength`), validated against
  `tags.HERO_POWERS`. It picks the character sheet's three-slot panel label set: a
  magic world (Floating Isles) says "My magics / My magic is / It can"; a wits-and-
  courage world (the five myth worlds) says "My strengths / My strength is / It helps
  me". The hero `magics:` list in `heroes.yaml` is the same shape either way (three
  canon ids); only the wording on the sheet changes, driven by the world. `sheets.py`
  resolves the label keys from `hero_powers`, so the panel never calls a quality a
  "magic".
- **The website consumes the build's output; it never re-derives content.** Data
  flows Python -> web in one direction. The Python CLI emits three feeds at the
  repo root: `site/manifest.json` (worlds, stories, tags, and per-PDF entries, via
  `build manifest` / `build/render/manifest.py`), the published PDFs under `kits/`,
  and story-map PNGs under `maps/` (via `build render-maps` /
  `build/render/web_map.py`). The `web/` Astro app reads these: `web/src/lib/content.ts`
  loads `site/manifest.json` and repo content, and `web/scripts/prepare-assets.mjs`
  (the prebuild step) resizes the source art to responsive WebP and copies the
  kits, maps, and brand fonts into `web/public/`. Pages are localized under
  `web/src/pages/[lang]/`. So a content change reaches the site by rebuilding the
  feeds (`build rebuild` / `build manifest` / `build render-maps`) and then
  rebuilding the web app; the site holds no story text of its own beyond the
  per-locale "why" pages in `web/src/content/why/`.

Authoring any kid-facing or grown-up-facing prose or YAML content is a content
task, not a coding task: use the `authoring-story-content` skill, which encodes
the voice, reading-level, peril-tone, and canon-name rules.

## Writing rule (must follow)

**Never use em dashes or en dashes anywhere**, in any file or text. Use a hyphen
only to connect words; do not use a hyphen as a substitute for an em or en dash.
Rewrite with commas, parentheses, a colon, or separate sentences. For number
ranges write "3 to 5", not a dash. A `PreToolUse` hook in `.claude/`
(`block-dashes.py`, the canonical forge-kit version 1) enforces this for file
writes and edits and for Bash commands (so a dash in a commit message or echo is
caught too); it activates on a normal session start.

## Core conventions (from the spec)

- **Languages**: British English (`en-GB`) is canonical; Spanish from Spain
  (`es-ES`), Italian (`it-IT`), and European Portuguese (`pt-PT`) are kept in sync
  (the `REQUIRED_LOCALES`, the single source of truth in `build/locales.py`). These
  are specific locales: write British spelling and idiom, peninsular Spanish
  (vosotros, full accents), natural Italian (voi for the players, full accents), and
  natural European Portuguese (vocês for the players, full accents). US English,
  Latin American Spanish, and Brazilian Portuguese are treated as separate languages
  that slot in later (like `pt-PT` versus `pt-BR`); never mix an Americanism into
  `en-GB`, a Latin turn of phrase into `es-ES`, or a Brazilian one into `pt-PT`.
  Adding a language is the `add-language` skill: it knows every file and action.
- **Content-driven**: content is text plus YAML metadata; Python builders are
  layout-only and take `(world, story, language, reading_level)`. Adding a world,
  story, language, or age tier is a content task, not a coding task.
- **Dice**: rules use abstract difficulty bands (Easy/Normal/Hard); every story
  must be playable with a single d6.
- **Tags**: age tiers `early`/`young`/`older`; peril `gentle`/`mild`/`heroic`;
  plus skills, players, play time. `players` is two or more (a grown-up and one or
  more children); the grown-up guides the story and plays along as a fellow
  adventurer, not just a referee. An `adult_gm` badge appears on every kit.
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
- `research/` the evidence base (why this matters) and the landscape scan (the wider
  field and ideas to improve the project), plus the marketing copy.

## Git

This is an open-source project: **commit and push at every change.** After each
logical change (a file or a small coherent set), make a descriptive commit and
push it to `origin`; do not leave work uncommitted or unpushed. A `Stop` hook in
`.claude/` is the backstop that auto-commits and pushes anything still pending
when a turn ends, so nothing is ever lost. End every commit message with the
standard co-author trailer. Work on `main`.
