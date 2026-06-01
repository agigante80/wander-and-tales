# CLAUDE.md - Wits & Wonder

Guidance for working in this repository.

## What this project is

Wits & Wonder is a public, multilingual library of **printable, cooperative,
adult-led story-adventure kits for kids** (print-and-play PDFs played with simple
dice and household objects). It is not a digital game. Worlds contain stories;
content is data and a layout-only build renders the PDFs.

## Status

Design phase. The full, approved design lives at
`docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`.
The runtime structure described there (`worlds/`, `build/`, `templates/`,
`lexicon/`, `guide/`, `catalog`) is **not all created yet**; it will be built
during implementation. Treat the spec as the source of truth.

## Writing rule (must follow)

**Never use em dashes or en dashes anywhere**, in any file or text. Use a hyphen
only to connect words; do not use a hyphen as a substitute for an em or en dash.
Rewrite with commas, parentheses, a colon, or separate sentences. For number
ranges write "3 to 5", not a dash. A `PreToolUse` hook in `.claude/` enforces
this for files (it activates on a normal session start).

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

## Build toolchain

Python with `reportlab` (layout), `cairosvg` (SVG map), and `pypdf` (merge).
Install with `pip install reportlab cairosvg pypdf` (no `requirements.txt` yet).
Build output goes to `dist/`, which is gitignored. The content-driven `build/`
described in the spec does not exist yet; the legacy scripts under
`El_Jardin_Dormido_kit/scripts/` are the starting point being refactored into it.

There is no unified build, test suite, or CLI entrypoint yet. To run a legacy
script, `python El_Jardin_Dormido_kit/scripts/build_01_mapa_y_reglas.py`, but note:

- Output paths are hardcoded to `/home/claude/...` or `/mnt/user-data/outputs/`;
  change them to a local path before running.
- `build_01_mapa_y_reglas.py` reads `mapa.svg` from the current directory.
- `merge_all.py` expects the four PDFs in `../pdfs` and writes one merged file.

## Verification

After generating any PDF, rasterize it to PNG and eyeball it before declaring it
done: confirm accents render, layout is intact, and the map merges correctly.
Per the spec, every authored `(story, language, reading_level)` combination must
build without error, and the canon/lexicon lint must pass with no warnings.

## Layout pointers

- `El_Jardin_Dormido_kit/` legacy Spanish kit, being migrated into the schema as
  the story "The Sleeping Garden" in the world "The Floating Isles". Its inner
  `CLAUDE.md` describes the old kit and is superseded by this file.
- `research/` evidence base and marketing copy.
- `docs/superpowers/specs/` design specs.

## Git

Branch `main`. Commit only when asked. End commit messages with the standard
co-author trailer.
