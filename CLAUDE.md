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

**Plan 1 (content model and tooling) is built**: the `build` package, its pytest
suite, and the `validate`/`lint`/`catalog` CLI all exist and pass. Still to come:
the PDF build pipeline (Plan 2: `templates/`, font embedding, layout-only
builders, page merge), then the actual `worlds/`, `lexicon/`, and `guide/` content
(Plans 3 to 5). So the `worlds/` tree the loaders read does not have real content
yet; `tests/conftest.py` builds a tiny valid world on a tmp path to test against.

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
```

Install (editable) into a fresh venv with `pip install -e ".[dev]"`. Runtime deps
are `pydantic>=2.6` and `PyYAML>=6.0` (see `pyproject.toml`). The PDF renderer
deps (`reportlab`, `cairosvg`, `pypdf`) arrive with Plan 2 and are not installed
yet.

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
- **Fonts**: embed a Unicode font (e.g. DejaVu Sans) so accents render.

## Verification

Per the spec, every authored `(story, language, reading_level)` combination must
build without error, and the canon/lexicon lint must pass with no warnings. Once
the PDF pipeline exists (Plan 2): after generating any PDF, rasterize it to PNG
and eyeball it before declaring it done; confirm accents render, layout is intact,
and the map merges correctly.

## Layout pointers

- `El_Jardin_Dormido_kit/scripts/` legacy Spanish kit layout scripts. The kit's
  content has been migrated into the schema (the world "The Floating Isles", the
  story "The Sleeping Garden"); only these `reportlab`/`cairosvg`/`pypdf` scripts
  and `mapa.svg` remain, kept as the layout starting point to refactor into the
  Plan 2 PDF pipeline. Their output paths are hardcoded to `/home/claude/...` or
  `/mnt/user-data/outputs/`; change them to a local path before running.
- `research/` evidence base and marketing copy.
- `docs/superpowers/specs/` design specs; `docs/superpowers/plans/` the plan set.

## Git

This is an open-source project: **commit at every change.** After each logical
change (a file or a small coherent set), make a descriptive commit; do not leave
work uncommitted. A `Stop` hook in `.claude/` is the backstop that auto-commits
anything still pending when a turn ends, so nothing is ever lost. End every
commit message with the standard co-author trailer. Work on `main`; push only
when asked.
