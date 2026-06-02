# Wits & Wonder, Plan 2: PDF build pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the validated content from Plan 1 into printable kit PDFs: register per-world typefaces, embed Unicode fonts, render the per-story markdown (narration, rules, puzzles, idea bank) and the canon-derived glossary into themed A4 pages, merge in the SVG map, add an age-tiered character sheet, and assemble one kit PDF per `(world, story, locale, reading_level)` into `dist/`, plus a standalone Guide for the Grown-Up PDF per locale.

**Architecture:** A new sub-package `build/render/` holds layout-only code that imports Plan 1's models. Two new pieces of world identity are added: the world palette (already in `world.yaml`) drives colours, and a new `fonts` block drives the typeface, with a per-locale override inside each world. Fonts are a vocabulary (`build/fontspec.py`), the single source of truth for which families exist and which TTF faces back them; the model validates against it and the renderer registers from it. Content is clean GitHub-flavoured markdown, so the core is a small hand-rolled markdown to reportlab-flowables converter (no markdown-parser dependency: the toolchain stays exactly the three the spec names). A themed reportlab document template paints the world palette behind flowing content. The SVG map renders through cairosvg and pages merge through pypdf. Builders take `(world, story, locale, reading_level)` and never hardcode a string, a colour, a font, or an output path.

**Tech Stack:** Python 3.11+, reportlab (layout and flowables), cairosvg (SVG map to PDF), pypdf (page merge), DejaVu Sans and DejaVu Serif (vendored Unicode TTFs, embedded so accents render). Plan 1's `pydantic` models and YAML loaders are reused, with one additive model change (the world `fonts` block).

---

## The plan set and sequencing

This is **Plan 2** of the sequence introduced in Plan 1. It depends only on Plan 1's models and loaders and delivers built kit PDFs in `dist/`.

- Plan 1: Content model and tooling. Built.
- **Plan 2: PDF build pipeline** (this document).
- Plan 3: The Floating Isles and The Sleeping Garden content. The story already exists in the schema (migrated from El Jardin Dormido); Plan 3 finishes any content polish and wires the three character sheets. It can render kits the moment Plan 2 lands.
- Plan 4: Greek-myth world and one story.
- Plan 5: Guide for the Grown-Up content. Plan 2 ships the Guide *renderer* (tested against a fixture); Plan 5 authors the real `guide/<locale>/guide.md` and the rules-page callout.

### Decisions locked for this plan

- **Fonts are part of the world, overridable per locale.** `world.yaml` gains a `fonts` block: a `default` family for the world and an optional `by_locale` map. Resolution precedence is `by_locale[locale]`, then `default`, then the global default family. Two real families ship vendored (`dejavu-sans`, `dejavu-serif`) so the choice is meaningful; adding a bespoke storybook or carved-stone TTF later is just a new entry in `build/fontspec.py` plus the files.
- **The font registry is a vocabulary.** `build/fontspec.py` is the single source of truth for which families exist and which TTF faces (regular, bold, italic, bold-italic) back each. The model validates the world `fonts` block against it; the renderer registers faces from it. It is pure (no reportlab), so the model can import it without inverting the layering.
- **No markdown-parser dependency.** The content is constrained GFM (headings, bold, italics, bullet lists, one pipe table). A small line-based parser in `build/render/markdown.py` handles it, keeping the dependency surface exactly `reportlab`, `cairosvg`, `pypdf` as the spec prescribes.
- **Map labels stay as the existing art for now.** The legacy `mapa.svg` renders as-is. Canon-driven map labels (spec section 9) are a later enhancement, deferred on purpose so this plan ships a working merged kit.
- **Character sheets are generic and age-tiered.** They carry no world-specific magic list, so they are reusable by the Greek world. Labels are localised through `build/render/strings.py`; the typeface follows the same per-world, per-locale resolution.

---

## File structure (Plan 2)

```
pyproject.toml                       # add the `render` optional-deps group, the build.render package, font package-data
build/fontspec.py                    # NEW vocabulary: font families -> TTF faces; the single source of truth for fonts
build/assets/fonts/                  # vendored DejaVu Sans and Serif TTFs (8 files)
build/models.py                      # MODIFIED: add WorldFonts and World.fonts, validated against fontspec
build/render/
  __init__.py                        # marks the sub-package
  fonts.py                           # register a family with reportlab; resolve faces per (world, locale)
  theme.py                           # Theme from world palette; ParagraphStyles bound to the resolved faces; page painter
  markdown.py                        # parse GFM into blocks; convert inline markdown to reportlab markup
  flowables.py                       # blocks -> reportlab flowables (headings, paragraphs, bullets, tables)
  pages.py                           # render flowables and whole markdown files to themed PDFs; the guide renderer
  strings.py                         # localised UI strings for the glossary and character sheets
  glossary.py                        # build the who's-who appendix flowables from canon
  sheets.py                          # the three age-tiered character-sheet templates
  map.py                             # cairosvg: an SVG file to a single-page PDF
  kit.py                             # assemble the ordered pages into one kit PDF in dist/
build/__main__.py                    # add `render` and `render-guide` subcommands
worlds/floating-isles/world.yaml     # MODIFIED: declare the world's fonts block
worlds/floating-isles/assets/map.svg # the live map (copied from the legacy kit)
tests/
  test_fontspec.py
  test_models_fonts.py
  test_render_fonts.py
  test_render_markdown.py
  test_render_theme.py
  test_render_flowables.py
  test_render_pages.py
  test_render_strings.py
  test_render_glossary.py
  test_render_map.py
  test_render_sheets.py
  test_render_kit.py
  test_render_guide.py
  test_cli_render.py
```

Layering, top to bottom: `fontspec` is a pure vocabulary that both the model and the renderer read; `models` validates the world `fonts` block against it; inside `render`, `fonts` and `theme` are the foundation, `markdown` is pure, `flowables` joins markdown blocks to styled objects, `pages`/`glossary`/`sheets`/`map` build one kind of page each, and `kit` orchestrates the order and the merge. Nothing reaches back up a layer.

---

## Task 1: Font registry vocabulary and vendored faces

`build/fontspec.py` is the single source of truth for fonts. It is pure data (pathlib only, no reportlab), so the model can import it for validation.

**Files:**
- Create: `build/fontspec.py`
- Create: `build/assets/fonts/` (eight vendored TTFs)
- Modify: `pyproject.toml` (font package-data; the render deps are added in Task 3)
- Test: `tests/test_fontspec.py`

- [ ] **Step 1: Vendor the DejaVu Sans and Serif TTFs**

```bash
mkdir -p build/assets/fonts
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf             build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf        build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf     build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf            build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf       build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf     build/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf build/assets/fonts/
```
Expected: `ls build/assets/fonts/` lists exactly those eight `.ttf` files. (DejaVu ships under the permissive Bitstream Vera and Arev licences, so vendoring and redistribution are fine.)

- [ ] **Step 2: Add font package-data to pyproject**

In `pyproject.toml`, replace the `[tool.setuptools]` block with one that keeps the package list and adds the font files as package data:

```toml
[tool.setuptools]
packages = ["build", "build.render"]

[tool.setuptools.package-data]
"build" = ["assets/fonts/*.ttf"]
```

- [ ] **Step 3: Write the failing test**

`tests/test_fontspec.py`:

```python
import pytest

from build import fontspec


def test_known_families_include_sans_and_serif():
    assert "dejavu-sans" in fontspec.KNOWN_FAMILIES
    assert "dejavu-serif" in fontspec.KNOWN_FAMILIES
    assert fontspec.DEFAULT_FAMILY == "dejavu-sans"


def test_faces_for_returns_four_existing_files():
    faces = fontspec.faces_for("dejavu-serif")
    for filename in (faces.normal, faces.bold, faces.italic, faces.bold_italic):
        assert fontspec.font_path(filename).is_file()


def test_faces_for_unknown_family_raises():
    with pytest.raises(KeyError):
        fontspec.faces_for("papyrus")
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fontspec.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.fontspec'`.

- [ ] **Step 5: Implement the vocabulary**

`build/fontspec.py`:

```python
"""Font registry: the single source of truth for which typefaces exist.

A family is a named set of four TTF faces (regular, bold, italic, bold-italic).
Worlds choose a family by key in world.yaml; the model validates against
KNOWN_FAMILIES here, and the renderer registers the faces with reportlab. This
module is pure (pathlib only) so the model can import it without pulling in any
rendering dependency. Add a new typeface by vendoring its TTFs and adding one
entry below.
"""

from dataclasses import dataclass
from pathlib import Path

FONT_DIR = Path(__file__).parent / "assets" / "fonts"


@dataclass(frozen=True)
class FaceFiles:
    normal: str
    bold: str
    italic: str
    bold_italic: str


FAMILIES: dict[str, FaceFiles] = {
    "dejavu-sans": FaceFiles(
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique.ttf",
    ),
    "dejavu-serif": FaceFiles(
        "DejaVuSerif.ttf",
        "DejaVuSerif-Bold.ttf",
        "DejaVuSerif-Italic.ttf",
        "DejaVuSerif-BoldItalic.ttf",
    ),
}

DEFAULT_FAMILY = "dejavu-sans"
KNOWN_FAMILIES = tuple(FAMILIES)


def faces_for(family: str) -> FaceFiles:
    """Return the four face filenames for a family. Raises KeyError if unknown."""
    return FAMILIES[family]


def font_path(filename: str) -> Path:
    """Absolute path to a vendored TTF by filename."""
    return FONT_DIR / filename
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_fontspec.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add build/fontspec.py build/assets/fonts/ pyproject.toml tests/test_fontspec.py
git commit -m "feat: font registry vocabulary with vendored DejaVu Sans and Serif"
```

---

## Task 2: World fonts in the content model

Extend the model so `world.yaml` can declare its typeface, validated against the registry, with a per-locale override.

**Files:**
- Modify: `build/models.py`
- Modify: `worlds/floating-isles/world.yaml`
- Test: `tests/test_models_fonts.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models_fonts.py`:

```python
import pytest
from pydantic import ValidationError

from build.models import World


def _world(fonts=None):
    data = {"id": "w", "name": {"en-GB": "W", "es-ES": "W"}}
    if fonts is not None:
        data["fonts"] = fonts
    return data


def test_world_without_fonts_is_valid_and_none():
    world = World.model_validate(_world())
    assert world.fonts is None


def test_world_with_default_family_parses():
    world = World.model_validate(_world({"default": "dejavu-serif"}))
    assert world.fonts.default == "dejavu-serif"
    assert world.fonts.by_locale == {}


def test_world_with_per_locale_override_parses():
    world = World.model_validate(
        _world({"default": "dejavu-serif", "by_locale": {"es-ES": "dejavu-sans"}})
    )
    assert world.fonts.by_locale["es-ES"] == "dejavu-sans"


def test_unknown_default_family_fails():
    with pytest.raises(ValidationError) as err:
        World.model_validate(_world({"default": "papyrus"}))
    assert "papyrus" in str(err.value)


def test_unknown_override_family_fails():
    with pytest.raises(ValidationError):
        World.model_validate(
            _world({"default": "dejavu-sans", "by_locale": {"es-ES": "comic"}})
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_models_fonts.py -v`
Expected: FAIL (currently `World` forbids the extra `fonts` key, so validation raises; the assertions on `world.fonts` cannot pass).

- [ ] **Step 3: Add the model**

In `build/models.py`, add `fontspec` to the imports:

```python
from build import dice, fontspec, locales, tags
```

Add the `WorldFonts` model just above `class World`:

```python
class WorldFonts(_Strict):
    """A world's typeface: a default family plus optional per-locale overrides.

    Resolution at render time is by_locale[locale], then default. Families are
    validated against the fontspec registry so a typo fails at load, not at draw.
    """

    default: str
    by_locale: dict[str, str] = {}

    @field_validator("default")
    @classmethod
    def _known_default(cls, value: str) -> str:
        if value not in fontspec.KNOWN_FAMILIES:
            raise ValueError(
                f"font family {value!r} not in {fontspec.KNOWN_FAMILIES}"
            )
        return value

    @field_validator("by_locale")
    @classmethod
    def _known_overrides(cls, value: dict[str, str]) -> dict[str, str]:
        bad = {
            loc: fam
            for loc, fam in value.items()
            if fam not in fontspec.KNOWN_FAMILIES
        }
        if bad:
            raise ValueError(f"unknown font families in by_locale: {bad}")
        return value
```

Add the field to `World` (after `lore_summary`):

```python
    fonts: WorldFonts | None = None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_models_fonts.py -v`
Expected: PASS.

- [ ] **Step 5: Declare the Floating Isles font**

Append a `fonts` block to `worlds/floating-isles/world.yaml` (a soft storybook serif for the body, demonstrating the feature; change the family later if you prefer the sans look):

```yaml
fonts:
  default: dejavu-serif
```

Then confirm the existing content still loads and validates:

Run: `.venv/bin/python -m build validate --root .`
Expected: `OK: validated 1 story file(s)`.

- [ ] **Step 6: Run the existing model suite to confirm no regression**

Run: `.venv/bin/python -m pytest tests/test_models.py tests/test_content.py -q`
Expected: PASS (the new optional field does not disturb existing tests).

- [ ] **Step 7: Commit**

```bash
git add build/models.py worlds/floating-isles/world.yaml tests/test_models_fonts.py
git commit -m "feat: per-world fonts in the content model with per-locale override"
```

---

## Task 3: Render dependencies and font resolution

Install the render extras and add the renderer-side font module: register a family's faces with reportlab and resolve which family a `(world, locale)` pair should use.

**Files:**
- Modify: `pyproject.toml`
- Create: `build/render/__init__.py`
- Create: `build/render/fonts.py`
- Test: `tests/test_render_fonts.py`

- [ ] **Step 1: Add the render dependency group**

In `pyproject.toml`, replace the `[project.optional-dependencies]` block with:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
render = [
    "reportlab>=4.0",
    "cairosvg>=2.7",
    "pypdf>=4.0",
]
```

- [ ] **Step 2: Install the render dependencies**

`cairosvg` needs the system Cairo library. On Debian or Ubuntu it is usually present as `libcairo2`; if import fails later, install it with the system package manager.

Run:
```bash
.venv/bin/pip install -e ".[dev,render]"
```
Expected: install succeeds; `.venv/bin/python -c "import reportlab, cairosvg, pypdf"` exits 0.

- [ ] **Step 3: Write the failing test**

`tests/test_render_fonts.py`:

```python
from reportlab.pdfbase import pdfmetrics

from build import fontspec
from build.models import World
from build.render import fonts


def _world(fonts_block=None):
    data = {"id": "w", "name": {"en-GB": "W", "es-ES": "W"}}
    if fonts_block is not None:
        data["fonts"] = fonts_block
    return World.model_validate(data)


def test_register_family_is_idempotent_and_registers_faces():
    fonts.register_family("dejavu-sans")
    faces = fonts.register_family("dejavu-sans")  # twice must not raise
    registered = set(pdfmetrics.getRegisteredFontNames())
    assert {faces.normal, faces.bold, faces.italic, faces.bold_italic} <= registered


def test_resolve_family_defaults_when_world_has_no_fonts():
    assert fonts.resolve_family(_world(), "en-GB") == fontspec.DEFAULT_FAMILY
    assert fonts.resolve_family(None, "en-GB") == fontspec.DEFAULT_FAMILY


def test_resolve_family_uses_world_default():
    world = _world({"default": "dejavu-serif"})
    assert fonts.resolve_family(world, "en-GB") == "dejavu-serif"
    assert fonts.resolve_family(world, "es-ES") == "dejavu-serif"


def test_per_locale_override_wins_within_a_world():
    world = _world({"default": "dejavu-sans", "by_locale": {"es-ES": "dejavu-serif"}})
    assert fonts.resolve_family(world, "en-GB") == "dejavu-sans"
    assert fonts.resolve_family(world, "es-ES") == "dejavu-serif"


def test_resolve_faces_registers_and_returns_the_resolved_family():
    world = _world({"default": "dejavu-serif"})
    faces = fonts.resolve_faces(world, "en-GB")
    assert faces.normal == "dejavu-serif"
    assert faces.bold in set(pdfmetrics.getRegisteredFontNames())
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_fonts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.fonts'`.

- [ ] **Step 5: Implement the package marker and the fonts module**

`build/render/__init__.py`:

```python
"""Layout-only PDF rendering for Wits & Wonder kits (Plan 2)."""
```

`build/render/fonts.py`:

```python
"""Register typefaces with reportlab and resolve the family for a world+locale.

The set of families and their TTF files comes from the fontspec vocabulary; this
module turns a family key into registered reportlab font names (one per face) and
applies the world's font choices. A face is named '<family>' for normal and
'<family>-bold', '<family>-italic', '<family>-bolditalic' for the rest.
"""

from dataclasses import dataclass

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from build import fontspec
from build.models import World


@dataclass(frozen=True)
class FontFaces:
    normal: str
    bold: str
    italic: str
    bold_italic: str


_registered: set[str] = set()


def register_family(family: str) -> FontFaces:
    """Register a family's four faces with reportlab. Safe to call repeatedly."""
    faces = FontFaces(
        normal=family,
        bold=f"{family}-bold",
        italic=f"{family}-italic",
        bold_italic=f"{family}-bolditalic",
    )
    if family in _registered:
        return faces
    files = fontspec.faces_for(family)
    pdfmetrics.registerFont(TTFont(faces.normal, str(fontspec.font_path(files.normal))))
    pdfmetrics.registerFont(TTFont(faces.bold, str(fontspec.font_path(files.bold))))
    pdfmetrics.registerFont(TTFont(faces.italic, str(fontspec.font_path(files.italic))))
    pdfmetrics.registerFont(
        TTFont(faces.bold_italic, str(fontspec.font_path(files.bold_italic)))
    )
    pdfmetrics.registerFontFamily(
        family,
        normal=faces.normal,
        bold=faces.bold,
        italic=faces.italic,
        boldItalic=faces.bold_italic,
    )
    _registered.add(family)
    return faces


def resolve_family(world: World | None, locale: str) -> str:
    """Family key for a world and locale: by_locale, then default, then global."""
    if world is not None and world.fonts is not None:
        if locale in world.fonts.by_locale:
            return world.fonts.by_locale[locale]
        return world.fonts.default
    return fontspec.DEFAULT_FAMILY


def resolve_faces(world: World | None, locale: str) -> FontFaces:
    """Resolve the family for a world+locale and register it, returning its faces."""
    return register_family(resolve_family(world, locale))
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_fonts.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml build/render/__init__.py build/render/fonts.py tests/test_render_fonts.py
git commit -m "feat: render deps and per-world, per-locale font resolution"
```

---

## Task 4: Markdown block parser

Pure: no reportlab, no I/O. Turns a markdown string into a list of block objects. Inline markup is left as raw text and converted in Task 5.

**Files:**
- Create: `build/render/markdown.py`
- Test: `tests/test_render_markdown.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_markdown.py`:

```python
from build.render import markdown as md


def test_headings_and_levels():
    blocks = md.parse_markdown("# Title\n\n## Section\n")
    assert blocks == [md.Heading(1, "Title"), md.Heading(2, "Section")]


def test_paragraph_joins_wrapped_lines():
    blocks = md.parse_markdown("One line\nwrapped onto two.\n")
    assert blocks == [md.Para("One line wrapped onto two.")]


def test_bullets_collect_and_join_continuations():
    text = "- first item that\n  wraps\n- second item\n"
    blocks = md.parse_markdown(text)
    assert blocks == [md.Bullets(["first item that wraps", "second item"])]


def test_pipe_table_parses_header_and_rows():
    text = "| Roll | Surprise |\n|---|---|\n| 1 | A hint. |\n| 2 | A star. |\n"
    blocks = md.parse_markdown(text)
    assert blocks == [
        md.Table(["Roll", "Surprise"], [["1", "A hint."], ["2", "A star."]])
    ]


def test_mixed_document_keeps_order():
    text = "# T\n\nIntro para.\n\n## S\n\n- a\n- b\n"
    blocks = md.parse_markdown(text)
    assert blocks == [
        md.Heading(1, "T"),
        md.Para("Intro para."),
        md.Heading(2, "S"),
        md.Bullets(["a", "b"]),
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_markdown.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.markdown'`.

- [ ] **Step 3: Implement the parser**

`build/render/markdown.py`:

```python
"""Parse the constrained GitHub-flavoured markdown used by kit content.

Pure and dependency-free. It recognises ATX headings, blank-line-separated
paragraphs, '-' or '*' bullet lists (with wrapped continuation lines), and GFM
pipe tables. Inline markup (**bold**, *italic*) is preserved as raw text and
converted to reportlab markup later, in inline_to_rl.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")
_TABLE_DIVIDER = re.compile(r"^\s*\|?\s*:?-{1,}.*$")


@dataclass(frozen=True)
class Heading:
    level: int
    text: str


@dataclass(frozen=True)
class Para:
    text: str


@dataclass(frozen=True)
class Bullets:
    items: list[str]


@dataclass(frozen=True)
class Table:
    headers: list[str]
    rows: list[list[str]]


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _is_block_start(line: str) -> bool:
    return (
        _is_blank(line)
        or _HEADING.match(line) is not None
        or _BULLET.match(line) is not None
        or line.lstrip().startswith("|")
    )


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_markdown(text: str) -> list:
    """Return an ordered list of Heading, Para, Bullets and Table blocks."""
    lines = text.split("\n")
    blocks: list = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            blocks.append(Heading(len(heading.group(1)), heading.group(2).strip()))
            i += 1
            continue

        if (
            line.lstrip().startswith("|")
            and i + 1 < n
            and _TABLE_DIVIDER.match(lines[i + 1])
        ):
            headers = _split_row(line)
            i += 2  # skip header and divider
            rows: list[list[str]] = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            blocks.append(Table(headers, rows))
            continue

        bullet = _BULLET.match(line)
        if bullet:
            items: list[str] = [bullet.group(1).strip()]
            i += 1
            while i < n and not _is_block_start(lines[i]):
                items[-1] = f"{items[-1]} {lines[i].strip()}"
                i += 1
            while i < n and _BULLET.match(lines[i]):
                items.append(_BULLET.match(lines[i]).group(1).strip())
                i += 1
                while i < n and not _is_block_start(lines[i]):
                    items[-1] = f"{items[-1]} {lines[i].strip()}"
                    i += 1
            blocks.append(Bullets(items))
            continue

        para = [line.strip()]
        i += 1
        while i < n and not _is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(Para(" ".join(para)))
    return blocks
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_markdown.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/markdown.py tests/test_render_markdown.py
git commit -m "feat: dependency-free markdown block parser for kit content"
```

---

## Task 5: Inline markdown to reportlab markup

reportlab paragraphs accept a small HTML-like markup. This converter escapes the dangerous characters and turns `**bold**` and `*italic*` into that markup. It lives in `markdown.py` beside the parser.

**Files:**
- Modify: `build/render/markdown.py`
- Test: `tests/test_render_markdown.py` (extend)

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_render_markdown.py`:

```python
def test_inline_escapes_then_bolds_and_italics():
    assert md.inline_to_rl("a & b < c") == "a &amp; b &lt; c"
    assert md.inline_to_rl("**Easy** and *soft*") == "<b>Easy</b> and <i>soft</i>"


def test_inline_bold_wins_over_italic_for_double_stars():
    assert md.inline_to_rl("**both**") == "<b>both</b>"


def test_inline_collapses_newlines_to_spaces():
    assert md.inline_to_rl("line one\nline two") == "line one line two"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_markdown.py -k inline -v`
Expected: FAIL with `AttributeError: module 'build.render.markdown' has no attribute 'inline_to_rl'`.

- [ ] **Step 3: Implement the converter**

Add to `build/render/markdown.py`:

```python
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def inline_to_rl(text: str) -> str:
    """Convert inline markdown to reportlab paragraph markup.

    Escapes &, < and > first (so content cannot inject markup), then turns
    **bold** and *italic* into <b> and <i>. Bold is handled before italic so a
    double star is never mistaken for two italics. Newlines collapse to spaces.
    """
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    bolded = _BOLD.sub(r"<b>\1</b>", escaped)
    italicised = _ITALIC.sub(r"<i>\1</i>", bolded)
    return " ".join(italicised.split("\n"))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_markdown.py -v`
Expected: PASS (parser and inline tests).

- [ ] **Step 5: Commit**

```bash
git add build/render/markdown.py tests/test_render_markdown.py
git commit -m "feat: inline markdown to reportlab markup conversion"
```

---

## Task 6: Theme, styles bound to the resolved faces, and the page painter

The theme reads the world palette into named colours, builds the paragraph styles from a given set of resolved font faces, and provides the background painter.

**Files:**
- Create: `build/render/theme.py`
- Test: `tests/test_render_theme.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_theme.py`:

```python
from reportlab.lib.colors import HexColor

from build.models import World
from build.render import fonts, theme


def _world():
    return World.model_validate(
        {
            "id": "floating-isles",
            "name": {"en-GB": "The Floating Isles", "es-ES": "Las Islas Flotantes"},
            "palette": ["#fef9ef", "#4ea24a", "#2bb3a3", "#d36fb0",
                        "#3f8fd6", "#f2a93b", "#8a6fd6"],
        }
    )


def test_theme_from_world_maps_palette_by_role():
    th = theme.Theme.from_world(_world())
    assert th.background == HexColor("#fef9ef")
    assert th.primary == HexColor("#4ea24a")


def test_theme_default_fills_in_when_palette_is_short():
    bare = World.model_validate(
        {"id": "x", "name": {"en-GB": "X", "es-ES": "X"}, "palette": []}
    )
    th = theme.Theme.from_world(bare)
    assert th.background is not None and th.primary is not None


def test_make_styles_binds_to_the_given_faces():
    faces = fonts.register_family("dejavu-serif")
    styles = theme.make_styles(theme.Theme.default(), faces)
    assert styles["body"].fontName == faces.normal
    assert styles["h1"].fontName == faces.bold
    assert set(styles) >= {"h1", "h2", "h3", "body", "bullet"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_theme.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.theme'`.

- [ ] **Step 3: Implement the theme**

`build/render/theme.py`:

```python
"""World palette to named colours, paragraph styles, and the page painter.

The world.yaml palette is an ordered list; this module gives each slot a role
(background, primary, then accent colours) and falls back to sensible defaults
when a palette is short or absent. Paragraph styles are bound to a set of
resolved font faces (see render.fonts), so a world's typeface flows through here.
"""

from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

from build.models import World
from build.render.fonts import FontFaces

_DEFAULT_PALETTE = (
    "#fef9ef",  # background (cream)
    "#4ea24a",  # primary (leaf green)
    "#2bb3a3",  # teal
    "#d36fb0",  # rose
    "#3f8fd6",  # blue
    "#f2a93b",  # gold
    "#8a6fd6",  # purple
)
_TEXT = HexColor("#3a5a32")
_BORDER = HexColor("#9ccf8a")


def _slot(palette: list[str], index: int) -> Color:
    if index < len(palette) and palette[index]:
        return HexColor(palette[index])
    return HexColor(_DEFAULT_PALETTE[index])


@dataclass(frozen=True)
class Theme:
    background: Color
    primary: Color
    teal: Color
    rose: Color
    blue: Color
    gold: Color
    purple: Color
    text: Color = _TEXT
    border: Color = _BORDER

    @classmethod
    def from_world(cls, world: World) -> "Theme":
        p = list(world.palette or [])
        return cls(
            background=_slot(p, 0),
            primary=_slot(p, 1),
            teal=_slot(p, 2),
            rose=_slot(p, 3),
            blue=_slot(p, 4),
            gold=_slot(p, 5),
            purple=_slot(p, 6),
        )

    @classmethod
    def default(cls) -> "Theme":
        return cls.from_world(
            World.model_validate(
                {"id": "_", "name": {"en-GB": "_", "es-ES": "_"},
                 "palette": list(_DEFAULT_PALETTE)}
            )
        )


def make_styles(theme: "Theme", faces: FontFaces) -> dict[str, ParagraphStyle]:
    """Build the paragraph styles bound to the resolved font faces."""
    body = ParagraphStyle(
        "body", fontName=faces.normal, fontSize=10, leading=14,
        textColor=theme.text, spaceAfter=6,
    )
    return {
        "h1": ParagraphStyle(
            "h1", parent=body, fontName=faces.bold, fontSize=18, leading=24,
            textColor=white, backColor=theme.primary, alignment=TA_CENTER,
            borderPadding=(7, 8, 7, 8), spaceAfter=12, spaceBefore=2,
        ),
        "h2": ParagraphStyle(
            "h2", parent=body, fontName=faces.bold, fontSize=13,
            textColor=theme.primary, spaceBefore=10, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", parent=body, fontName=faces.bold, fontSize=11,
            textColor=theme.teal, spaceBefore=6, spaceAfter=2,
        ),
        "body": body,
        "bullet": ParagraphStyle(
            "bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=3,
        ),
    }


def page_painter(theme: "Theme"):
    """Return an onPage(canvas, doc) callback that paints background and border."""

    def paint(canvas, doc) -> None:
        width, height = doc.pagesize
        canvas.saveState()
        canvas.setFillColor(theme.background)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(theme.border)
        canvas.setLineWidth(3)
        canvas.setDash(2, 10)
        canvas.roundRect(8 * mm, 8 * mm, width - 16 * mm, height - 16 * mm, 10,
                         fill=0, stroke=1)
        canvas.restoreState()

    return paint
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_theme.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/theme.py tests/test_render_theme.py
git commit -m "feat: theme, face-bound paragraph styles, and the page painter"
```

---

## Task 7: Blocks to flowables, and content files to a PDF

Wire markdown blocks to reportlab flowables, then render a full markdown file into a themed PDF using the world+locale font. After this task a real, viewable kit page exists in the world's chosen typeface.

**Files:**
- Create: `build/render/flowables.py`
- Create: `build/render/pages.py`
- Test: `tests/test_render_flowables.py`
- Test: `tests/test_render_pages.py`

- [ ] **Step 1: Write the failing test for flowables**

`tests/test_render_flowables.py`:

```python
from reportlab.platypus import Paragraph, Table as RLTable

from build.render import flowables, fonts, theme
from build.render import markdown as md


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def test_heading_and_paragraph_become_paragraphs():
    blocks = [md.Heading(1, "Title"), md.Para("Some **bold** text.")]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    paragraphs = [f for f in flows if isinstance(f, Paragraph)]
    assert len(paragraphs) == 2
    assert "<b>bold</b>" in paragraphs[1].text


def test_table_block_becomes_a_reportlab_table():
    blocks = [md.Table(["Roll", "Surprise"], [["1", "A hint."]])]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    assert any(isinstance(f, RLTable) for f in flows)


def test_bullets_become_one_paragraph_each():
    blocks = [md.Bullets(["one", "two", "three"])]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    paragraphs = [f for f in flows if isinstance(f, Paragraph)]
    assert len(paragraphs) == 3
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_flowables.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.flowables'`.

- [ ] **Step 3: Implement flowables**

`build/render/flowables.py`:

```python
"""Turn markdown blocks into reportlab flowables using the themed styles.

Table fonts are taken from the style dict (body and a bold heading style), so a
world's typeface flows through tables as well as prose.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from build.render import markdown as md
from build.render.theme import Theme

CONTENT_WIDTH = 210 * mm - 36 * mm  # A4 width minus the page margins
_BULLET = "•"


def _table_style(theme: Theme, body_font: str, head_font: str) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), theme.primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), head_font),
            ("FONTNAME", (0, 1), (-1, -1), body_font),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, theme.primary),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _col_widths(ncols: int) -> list[float]:
    if ncols == 2:
        return [22 * mm, CONTENT_WIDTH - 22 * mm]
    return [CONTENT_WIDTH / ncols] * ncols


def blocks_to_flowables(blocks: list, styles: dict, theme: Theme) -> list:
    """Map each block to one or more reportlab flowables, in order."""
    body_font = styles["body"].fontName
    head_font = styles["h2"].fontName
    flows: list = []
    for block in blocks:
        if isinstance(block, md.Heading):
            key = {1: "h1", 2: "h2"}.get(block.level, "h3")
            flows.append(Paragraph(md.inline_to_rl(block.text), styles[key]))
        elif isinstance(block, md.Para):
            flows.append(Paragraph(md.inline_to_rl(block.text), styles["body"]))
        elif isinstance(block, md.Bullets):
            for item in block.items:
                flows.append(
                    Paragraph(md.inline_to_rl(item), styles["bullet"],
                              bulletText=_BULLET)
                )
        elif isinstance(block, md.Table):
            data = [
                [Paragraph(md.inline_to_rl(cell), styles["body"]) for cell in row]
                for row in [block.headers, *block.rows]
            ]
            table = Table(data, colWidths=_col_widths(len(block.headers)))
            table.setStyle(_table_style(theme, body_font, head_font))
            flows.append(Spacer(1, 4))
            flows.append(table)
            flows.append(Spacer(1, 6))
    return flows
```

- [ ] **Step 4: Run the flowables test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_flowables.py -v`
Expected: PASS.

- [ ] **Step 5: Write the failing test for pages**

`tests/test_render_pages.py`:

```python
from pypdf import PdfReader

from build.models import World
from build.render import pages


def _world(fonts_block=None):
    data = {
        "id": "floating-isles",
        "name": {"en-GB": "The Floating Isles", "es-ES": "Las Islas Flotantes"},
        "palette": ["#fef9ef", "#4ea24a", "#2bb3a3"],
    }
    if fonts_block is not None:
        data["fonts"] = fonts_block
    return World.model_validate(data)


def test_render_markdown_file_writes_a_valid_pdf(tmp_path):
    src = tmp_path / "narration.simple.md"
    src.write_text(
        "# The Sleeping Garden\n\nThis morning the island is quiet. Demasiado "
        "silencio: accents like ñ and á must render.\n\n## Stop 1\n\n- look\n- try\n",
        encoding="utf-8",
    )
    out = tmp_path / "narration.pdf"
    pages.render_markdown_file(src, out, _world({"default": "dejavu-serif"}), "en-GB")
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 1


def test_render_flowables_accepts_landscape(tmp_path):
    out = tmp_path / "land.pdf"
    pages.render_flowables([], out, _world(), landscape_page=True)
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 6: Run the pages test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_pages.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.pages'`.

- [ ] **Step 7: Implement pages**

`build/render/pages.py`:

```python
"""Render flowables, and whole markdown files, into themed PDFs.

The font is resolved per (world, locale) so each page is drawn in the world's
typeface, honouring any per-locale override.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from build.models import World
from build.render import flowables, fonts, theme
from build.render import markdown as md


def _doc(out_path: Path, *, landscape_page: bool) -> SimpleDocTemplate:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return SimpleDocTemplate(
        str(out_path), pagesize=landscape(A4) if landscape_page else A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )


def render_flowables(
    flows: list, out_path: Path, world: World, *, landscape_page: bool = False
) -> Path:
    """Build a themed PDF from ready-made flowables (already styled)."""
    th = theme.Theme.from_world(world)
    doc = _doc(out_path, landscape_page=landscape_page)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path


def render_markdown_file(src: Path, out_path: Path, world: World, locale: str) -> Path:
    """Parse a markdown content file and render it in the world+locale typeface."""
    faces = fonts.resolve_faces(world, locale)
    th = theme.Theme.from_world(world)
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    return render_flowables(flows, out_path, world)


def render_guide(src: Path, out_path: Path, locale: str = "en-GB") -> Path:
    """Render the world-agnostic Guide for the Grown-Up to a themed PDF.

    The guide is shared across worlds, so it uses the default theme and the
    default family (DejaVu covers en-GB and es-ES today). Per-locale guide
    typography is deferred until a locale needs a different script.
    """
    faces = fonts.resolve_faces(None, locale)
    th = theme.Theme.default()
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = _doc(out_path, landscape_page=False)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path
```

- [ ] **Step 8: Run the pages test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_pages.py -v`
Expected: PASS.

- [ ] **Step 9: Manual visual check (optional but recommended)**

Render a real narration file in the Floating Isles serif and eyeball it:
```bash
.venv/bin/python -c "
from pathlib import Path
from build.content import load_world
from build.render import pages
w = load_world(Path('worlds/floating-isles/world.yaml'))
src = Path('worlds/floating-isles/stories/sleeping-garden/content/es-ES/narration.simple.md')
pages.render_markdown_file(src, Path('dist/_preview_narration_es.pdf'), w, 'es-ES')
print('wrote dist/_preview_narration_es.pdf')
"
```
Open it (or rasterise with `pdftoppm -png -r 120 dist/_preview_narration_es.pdf dist/_preview` if poppler is available) and confirm the Spanish accents render, the typeface is the serif the world declared, and the green title banner appears. `dist/` is gitignored, so nothing is committed.

- [ ] **Step 10: Commit**

```bash
git add build/render/flowables.py build/render/pages.py \
        tests/test_render_flowables.py tests/test_render_pages.py
git commit -m "feat: markdown to flowables and content files to themed PDFs"
```

---

## Task 8: Localised UI strings

A small resource of the non-content labels the layout needs (glossary headings, character-sheet field labels). These are layout strings, not story content, so they live in the render package.

**Files:**
- Create: `build/render/strings.py`
- Test: `tests/test_render_strings.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_strings.py`:

```python
import pytest

from build.locales import REQUIRED_LOCALES
from build.render import strings


def test_every_required_locale_has_every_key():
    keys = set(strings.UI["en-GB"])
    for locale in REQUIRED_LOCALES:
        assert set(strings.UI[locale]) == keys, locale


def test_ui_returns_text_and_raises_on_unknown_key():
    assert strings.ui("en-GB", "glossary_title")
    assert strings.ui("es-ES", "glossary_title")
    with pytest.raises(KeyError):
        strings.ui("en-GB", "no_such_key")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_strings.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.strings'`.

- [ ] **Step 3: Implement the strings**

`build/render/strings.py`:

```python
"""Localised layout labels (not story content). en-GB canonical, es-ES synced."""

UI: dict[str, dict[str, str]] = {
    "en-GB": {
        "glossary_title": "Who's Who and What's What",
        "group_place": "Places",
        "group_character": "Characters",
        "group_creature": "Creatures",
        "group_item": "Items",
        "group_term": "Words to Know",
        "sheet_title": "My Adventure Sheet",
        "sheet_name": "My name",
        "sheet_magic": "My magic (write or draw it)",
        "sheet_energy": "My energy stars (colour one in when you spend it)",
        "sheet_draw": "Draw your hero",
        "sheet_inventory": "What I am carrying",
        "sheet_notes": "Notes",
        "sheet_footer": "Here nobody loses. If a try does not work, find another way.",
    },
    "es-ES": {
        "glossary_title": "Quien es Quien y Que es Que",
        "group_place": "Lugares",
        "group_character": "Personajes",
        "group_creature": "Criaturas",
        "group_item": "Objetos",
        "group_term": "Palabras que conviene saber",
        "sheet_title": "Mi Ficha de Aventura",
        "sheet_name": "Mi nombre",
        "sheet_magic": "Mi magia (escribela o dibujala)",
        "sheet_energy": "Mis estrellas de energia (colorea una al gastarla)",
        "sheet_draw": "Dibuja a tu heroe o heroina",
        "sheet_inventory": "Lo que llevo conmigo",
        "sheet_notes": "Notas",
        "sheet_footer": "Aqui nadie pierde. Si algo no sale, se busca otra manera.",
    },
}


def ui(locale: str, key: str) -> str:
    """Return the label for a locale and key. Raises KeyError if either is absent."""
    return UI[locale][key]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_strings.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/strings.py tests/test_render_strings.py
git commit -m "feat: localised layout strings for glossary and sheets"
```

---

## Task 9: Glossary appendix from canon

The glossary is generated from canon, so it can never disagree with the world bible. It groups entries by kind and prints the locale name and description.

**Files:**
- Create: `build/render/glossary.py`
- Test: `tests/test_render_glossary.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_glossary.py`:

```python
from reportlab.platypus import Paragraph

from build.models import CanonEntry
from build.render import fonts, glossary, theme


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def _entries():
    return [
        CanonEntry.model_validate(
            {"id": "great-garden", "kind": "place",
             "names": {"en-GB": "The Great Garden", "es-ES": "El Gran Jardin"},
             "description": {"en-GB": "The green heart of the island.",
                             "es-ES": "El corazon verde de la isla."}}
        ),
        CanonEntry.model_validate(
            {"id": "mist-cat", "kind": "creature",
             "names": {"en-GB": "Mist Cat", "es-ES": "Gato de Niebla"},
             "description": {"en-GB": "A gentle cat made of fog.",
                             "es-ES": "Un gato amable hecho de niebla."}}
        ),
    ]


def test_glossary_titles_and_names_appear_for_locale():
    flows = glossary.glossary_flowables(_entries(), "en-GB", _styles(), theme.Theme.default())
    text = " ".join(f.text for f in flows if isinstance(f, Paragraph))
    assert "Who's Who" in text
    assert "Places" in text and "Creatures" in text
    assert "The Great Garden" in text and "green heart" in text


def test_glossary_uses_the_requested_locale():
    flows = glossary.glossary_flowables(_entries(), "es-ES", _styles(), theme.Theme.default())
    text = " ".join(f.text for f in flows if isinstance(f, Paragraph))
    assert "El Gran Jardin" in text and "Gato de Niebla" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_glossary.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.glossary'`.

- [ ] **Step 3: Implement the glossary**

`build/render/glossary.py`:

```python
"""Build the who's-who glossary appendix straight from canon entries.

Generated, never hand-written, so it cannot drift from the world bible. Entries
are grouped by kind in a fixed order and printed with the locale name and
(optional) description.
"""

from reportlab.platypus import Paragraph

from build.models import CanonEntry
from build.render import markdown as md
from build.render import strings
from build.render.theme import Theme

_KIND_ORDER = ("place", "character", "creature", "item", "term")
_KIND_LABEL = {
    "place": "group_place",
    "character": "group_character",
    "creature": "group_creature",
    "item": "group_item",
    "term": "group_term",
}


def glossary_flowables(
    entries: list[CanonEntry], locale: str, styles: dict, theme: Theme
) -> list:
    """Return flowables for a glossary page: a title, then a group per kind."""
    flows: list = [Paragraph(strings.ui(locale, "glossary_title"), styles["h1"])]
    for kind in _KIND_ORDER:
        group = [e for e in entries if e.kind == kind]
        if not group:
            continue
        flows.append(Paragraph(strings.ui(locale, _KIND_LABEL[kind]), styles["h2"]))
        for entry in sorted(group, key=lambda e: e.names[locale]):
            name = entry.names[locale]
            desc = (entry.description or {}).get(locale, "")
            line = f"**{name}**" + (f" - {desc}" if desc else "")
            flows.append(Paragraph(md.inline_to_rl(line), styles["body"]))
    return flows
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_glossary.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/glossary.py tests/test_render_glossary.py
git commit -m "feat: glossary appendix generated from canon"
```

---

## Task 10: SVG map to a PDF page

cairosvg renders the world's map SVG into a single-page PDF that pypdf can later merge.

**Files:**
- Create: `build/render/map.py`
- Create: `worlds/floating-isles/assets/map.svg` (copied from the legacy kit)
- Test: `tests/test_render_map.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_map.py`:

```python
from build.render import map as kit_map

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text x="20" y="60" font-size="16">Mapa</text></svg>'
)


def test_svg_renders_to_a_pdf(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TINY_SVG, encoding="utf-8")
    out = tmp_path / "map.pdf"
    result = kit_map.render_svg_to_pdf(svg, out)
    assert result == out
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.map'`.

- [ ] **Step 3: Implement the map renderer**

`build/render/map.py`:

```python
"""Render a world map SVG to a single-page PDF via cairosvg.

Canon-driven map labels are deferred (spec section 9); for now the SVG art is
rendered as authored. The page keeps the SVG's own aspect ratio, so the map is
typically landscape and merges cleanly with the portrait content pages.
"""

from pathlib import Path

import cairosvg


def render_svg_to_pdf(svg_path: Path, out_path: Path) -> Path:
    """Convert an SVG file to a one-page PDF at out_path. Returns out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(out_path))
    return out_path
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -v`
Expected: PASS.

- [ ] **Step 5: Copy the legacy map into the world's assets**

```bash
mkdir -p worlds/floating-isles/assets
cp El_Jardin_Dormido_kit/scripts/mapa.svg worlds/floating-isles/assets/map.svg
```
Expected: `worlds/floating-isles/assets/map.svg` exists. (Its baked-in Spanish labels are a known limitation until canon-driven labels arrive; the art is correct.)

- [ ] **Step 6: Commit**

```bash
git add build/render/map.py worlds/floating-isles/assets/map.svg tests/test_render_map.py
git commit -m "feat: render the world map SVG to a PDF page"
```

---

## Task 11: Character sheet templates (three age tiers)

Generic, age-tiered sheets with localised labels, drawn in the resolved typeface. They carry no world-specific magic list, so the Greek world reuses them unchanged.

**Files:**
- Create: `build/render/sheets.py`
- Test: `tests/test_render_sheets.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_sheets.py`:

```python
import pytest
from pypdf import PdfReader

from build.render import fonts, sheets, theme
from build.tags import AGE_TIERS


def _faces():
    return fonts.register_family("dejavu-sans")


@pytest.mark.parametrize("tier", AGE_TIERS)
def test_each_tier_renders_one_page(tmp_path, tier):
    out = tmp_path / f"sheet_{tier}.pdf"
    sheets.render_character_sheet(out, "en-GB", tier, theme.Theme.default(), _faces())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1


def test_unknown_tier_raises(tmp_path):
    with pytest.raises(ValueError):
        sheets.render_character_sheet(
            tmp_path / "x.pdf", "en-GB", "tween", theme.Theme.default(), _faces()
        )


def test_spanish_sheet_renders(tmp_path):
    out = tmp_path / "sheet_es.pdf"
    sheets.render_character_sheet(out, "es-ES", "young", theme.Theme.default(), _faces())
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_sheets.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.sheets'`.

- [ ] **Step 3: Implement the sheets**

`build/render/sheets.py`:

```python
"""The three age-tiered character sheets: early, young, older.

Generic across worlds (no magic list baked in), localised through strings.py and
drawn in the resolved font faces. 'early' is mostly a drawing space and a name;
'young' adds a magic line and energy stars; 'older' adds an inventory and notes.
"""

import math
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import strings
from build.render.fonts import FontFaces
from build.render.theme import Theme
from build.tags import AGE_TIERS

W, H = A4


def _star(c, cx: float, cy: float, r: float, stroke) -> None:
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.setFillColor(white)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.5)
    c.drawPath(p, fill=1, stroke=1)


def render_character_sheet(
    out_path: Path, locale: str, tier: str, theme: Theme, faces: FontFaces
) -> Path:
    """Render a one-page character sheet for an age tier. Raises on unknown tier."""
    if tier not in AGE_TIERS:
        raise ValueError(f"unknown age tier {tier!r}, expected one of {AGE_TIERS}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)

    def label(x: float, y: float, text: str) -> None:
        c.setFillColor(theme.primary)
        c.setFont(faces.bold, 12)
        c.drawString(x, y, text)

    def line(x: float, y: float, width: float) -> None:
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.2)
        c.line(x, y, x + width, y)

    # background and border
    c.setFillColor(theme.background)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(theme.border)
    c.setLineWidth(3)
    c.setDash(2, 10)
    c.roundRect(8 * mm, 8 * mm, W - 16 * mm, H - 16 * mm, 10, fill=0, stroke=1)
    c.setDash()

    # title banner
    c.setFillColor(theme.primary)
    c.roundRect(18 * mm, H - 38 * mm, W - 36 * mm, 18 * mm, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(faces.bold, 20)
    c.drawCentredString(W / 2, H - 31 * mm, strings.ui(locale, "sheet_title"))

    y = H - 52 * mm
    label(20 * mm, y, strings.ui(locale, "sheet_name"))
    line(60 * mm, y - 1 * mm, W - 80 * mm)

    if tier in ("young", "older"):
        y -= 14 * mm
        label(20 * mm, y, strings.ui(locale, "sheet_magic"))
        line(20 * mm, y - 8 * mm, W - 40 * mm)

        y -= 20 * mm
        label(20 * mm, y, strings.ui(locale, "sheet_energy"))
        for i in range(5):
            _star(c, 28 * mm + i * 22 * mm, y - 12 * mm, 8 * mm, theme.gold)
        y -= 22 * mm

    box_h = 70 * mm if tier == "early" else 44 * mm
    label(20 * mm, y, strings.ui(locale, "sheet_draw"))
    c.setStrokeColor(theme.teal)
    c.setLineWidth(1.5)
    c.setDash(4, 4)
    c.roundRect(20 * mm, y - 6 * mm - box_h, W - 40 * mm, box_h, 8, fill=0, stroke=1)
    c.setDash()
    y -= box_h + 14 * mm

    if tier == "older":
        label(20 * mm, y, strings.ui(locale, "sheet_inventory"))
        for k in range(3):
            line(20 * mm, y - 8 * mm - k * 8 * mm, W - 40 * mm)
        y -= 34 * mm
        label(20 * mm, y, strings.ui(locale, "sheet_notes"))
        for k in range(2):
            line(20 * mm, y - 8 * mm - k * 8 * mm, W - 40 * mm)

    c.setFillColor(theme.text)
    c.setFont(faces.italic, 9)
    c.drawCentredString(W / 2, 14 * mm, strings.ui(locale, "sheet_footer"))
    c.showPage()
    c.save()
    return out_path
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_sheets.py -v`
Expected: PASS (three tiers plus the unknown-tier and Spanish cases).

- [ ] **Step 5: Commit**

```bash
git add build/render/sheets.py tests/test_render_sheets.py
git commit -m "feat: three age-tiered character-sheet templates"
```

---

## Task 12: Kit assembly and page merge

Load the world, story and canon, render each page to a temporary PDF in the right order using the resolved typeface, and merge them with pypdf into one kit PDF in `dist/`. The output name encodes the full tuple.

**Files:**
- Create: `build/render/kit.py`
- Test: `tests/test_render_kit.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_kit.py` (uses the `sample_repo` fixture from Plan 1's `tests/conftest.py`, adding a tiny map so the map page is exercised):

```python
from pypdf import PdfReader

from build.render import kit

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def _add_map(sample_repo):
    assets = sample_repo / "worlds" / "floating-isles" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_TINY_SVG, encoding="utf-8")


def test_build_kit_writes_one_merged_pdf(sample_repo, tmp_path):
    _add_map(sample_repo)
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    assert out.name == "floating-isles_sleeping-garden_en-GB_simple.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    # map + narration + rules + puzzles + idea-bank + glossary + sheet = at least 7
    assert len(PdfReader(str(out)).pages) >= 7


def test_build_kit_skips_missing_map(sample_repo, tmp_path):
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "rich",
        out_dir=tmp_path,
    )
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 6


def test_reading_level_selects_narration_file():
    assert kit.NARRATION_BY_LEVEL == {
        "simple": "narration.simple.md",
        "rich": "narration.rich.md",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.kit'`.

- [ ] **Step 3: Implement the kit builder**

`build/render/kit.py`:

```python
"""Assemble one printable kit PDF per (world, story, locale, reading_level).

Loads content through Plan 1's loaders, resolves the world+locale typeface, then
renders each page to a temporary PDF in a fixed order and merges them with pypdf
into dist/. The map page is optional: if the world has no assets/map.svg, the kit
builds without it.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build import content
from build.render import fonts, glossary, map as kit_map, pages, sheets, theme

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}

# Grown-up-facing prose pages that follow the kid-facing narration.
_PROSE_PAGES = ("rules.md", "puzzles.md", "idea-bank.md")


def _merge(parts: list[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path


def build_kit(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    reading_level: str,
    *,
    out_dir: Path | None = None,
) -> Path:
    """Build the kit PDF and return its path under out_dir (default dist/)."""
    if reading_level not in NARRATION_BY_LEVEL:
        raise ValueError(f"unknown reading level {reading_level!r}")

    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    content_dir = story_dir / "content" / locale

    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")
    canon = content.load_canon(world_dir / "canon")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    out_dir = out_dir if out_dir is not None else root / "dist"
    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        map_svg = world_dir / "assets" / "map.svg"
        if map_svg.is_file():
            parts.append(kit_map.render_svg_to_pdf(map_svg, tmp_path / "00_map.pdf"))

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_markdown_file(narration, tmp_path / "10_narration.pdf", world, locale)
        )

        for index, filename in enumerate(_PROSE_PAGES, start=2):
            src = content_dir / filename
            parts.append(
                pages.render_markdown_file(
                    src, tmp_path / f"{index}0_{filename}.pdf", world, locale
                )
            )

        gloss = glossary.glossary_flowables(canon, locale, styles, th)
        parts.append(pages.render_flowables(gloss, tmp_path / "80_glossary.pdf", world))

        sheet = tmp_path / "90_sheet.pdf"
        sheets.render_character_sheet(sheet, locale, story.age.recommended, th, faces)
        parts.append(sheet)

        out_path = out_dir / f"{world_id}_{story_id}_{locale}_{reading_level}.pdf"
        return _merge(parts, out_path)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: PASS.

- [ ] **Step 5: Build the real Sleeping Garden kits and eyeball them**

```bash
.venv/bin/python -c "
from pathlib import Path
from build.render import kit
for locale in ('en-GB', 'es-ES'):
    for level in ('simple', 'rich'):
        out = kit.build_kit(Path('.'), 'floating-isles', 'sleeping-garden', locale, level)
        print('built', out)
"
```
Expected: four PDFs under `dist/`. Open the es-ES one and confirm accents render, the typeface is the world's serif, the map merges, and pages are in order.

- [ ] **Step 6: Commit**

```bash
git add build/render/kit.py tests/test_render_kit.py
git commit -m "feat: assemble and merge the kit PDF per locale and reading level"
```

---

## Task 13: Standalone Guide for the Grown-Up PDF

The Guide *renderer* already exists (`pages.render_guide`, added in Task 7). This task pins it with its own test so Plan 5 only has to write the prose at `guide/<locale>/guide.md`.

**Files:**
- Test: `tests/test_render_guide.py`

- [ ] **Step 1: Write the test**

`tests/test_render_guide.py`:

```python
from pypdf import PdfReader

from build.render import pages


def test_render_guide_builds_a_pdf_from_markdown(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(
        "# Guide for the Grown-Up\n\nYou have three jobs: narrator, gentle "
        "referee, and biggest fan.\n\n## Yes, and\n\nNever just say no.\n",
        encoding="utf-8",
    )
    out = tmp_path / "guide.pdf"
    pages.render_guide(guide, out)
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 1


def test_render_guide_accepts_spanish(tmp_path):
    guide = tmp_path / "guia.md"
    guide.write_text("# Guia\n\nTienes tres trabajos.\n", encoding="utf-8")
    out = tmp_path / "guia.pdf"
    pages.render_guide(guide, out, "es-ES")
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_guide.py -v`
Expected: PASS (the renderer was implemented in Task 7).

- [ ] **Step 3: Commit**

```bash
git add tests/test_render_guide.py
git commit -m "test: pin the standalone Guide for the Grown-Up renderer"
```

---

## Task 14: CLI: render and render-guide

Extend the Plan 1 CLI so kits and the guide build from the command line, matching the existing `validate`/`lint`/`catalog` style.

**Files:**
- Modify: `build/__main__.py`
- Test: `tests/test_cli_render.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli_render.py`:

```python
from build.__main__ import main

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def test_render_builds_a_kit(sample_repo, tmp_path, capsys):
    assets = sample_repo / "worlds" / "floating-isles" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_TINY_SVG, encoding="utf-8")
    code = main([
        "render", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--reading-level", "simple",
        "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert "floating-isles_sleeping-garden_en-GB_simple.pdf" in capsys.readouterr().out
    assert (tmp_path / "floating-isles_sleeping-garden_en-GB_simple.pdf").is_file()


def test_render_guide_builds_from_root(sample_repo, tmp_path, capsys):
    guide_dir = sample_repo / "guide" / "en-GB"
    guide_dir.mkdir(parents=True)
    (guide_dir / "guide.md").write_text("# Guide\n\nThree jobs.\n", encoding="utf-8")
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "Guide_for_the_Grown-Up_en-GB.pdf").is_file()


def test_render_guide_missing_markdown_returns_one(sample_repo, tmp_path):
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "es-ES", "--out-dir", str(tmp_path),
    ])
    assert code == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py -v`
Expected: FAIL (argparse rejects the unknown `render` subcommand, raising SystemExit).

- [ ] **Step 3: Extend the CLI**

In `build/__main__.py`, add the two subparsers inside `main`, after the existing `catalog` parser is configured and before `args = parser.parse_args(argv)`:

```python
    render_parser = sub.add_parser("render", help="build a kit PDF")
    _add_root(render_parser)
    render_parser.add_argument("--world", required=True)
    render_parser.add_argument("--story", required=True)
    render_parser.add_argument("--locale", required=True)
    render_parser.add_argument("--reading-level", required=True,
                               choices=("simple", "rich"))
    render_parser.add_argument("--out-dir", type=Path, default=None)

    guide_parser = sub.add_parser("render-guide", help="build the Guide PDF")
    _add_root(guide_parser)
    guide_parser.add_argument("--locale", required=True)
    guide_parser.add_argument("--out-dir", type=Path, default=None)
```

Then add the two command branches before the final `return 2`:

```python
    if args.command == "render":
        from build.render import kit

        out = kit.build_kit(
            args.root, args.world, args.story, args.locale, args.reading_level,
            out_dir=args.out_dir,
        )
        print(f"built {out}")
        return 0

    if args.command == "render-guide":
        from build.render import pages

        src = args.root / "guide" / args.locale / "guide.md"
        if not src.is_file():
            print(f"no guide markdown at {src}")
            return 1
        out_dir = args.out_dir if args.out_dir is not None else args.root / "dist"
        out = out_dir / f"Guide_for_the_Grown-Up_{args.locale}.pdf"
        pages.render_guide(src, out, args.locale)
        print(f"built {out}")
        return 0
```

(The render deps are imported lazily inside the branches so `validate`, `lint` and `catalog` keep working in an environment without the render extra installed.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py -v`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: every test passes (Plan 1 and Plan 2).

- [ ] **Step 6: Commit**

```bash
git add build/__main__.py tests/test_cli_render.py
git commit -m "feat: render and render-guide CLI commands"
```

---

## Task 15: Documentation refresh

Update the docs that Plan 1 left pointing forward, so the repo reflects that the PDF pipeline now exists, including per-world fonts.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md status and commands**

In `CLAUDE.md`, in the "Status" section, change the line that says the PDF build pipeline is "Still to come" so Plan 2 is listed as built. In the "Commands" section, add the render commands:

```bash
.venv/bin/python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple        # build one kit PDF into dist/
.venv/bin/python -m build render-guide --root . --locale en-GB  # build the Guide PDF
```

Update the dependency note: the render extras (`reportlab`, `cairosvg`, `pypdf`) install via `pip install -e ".[dev,render]"`, and DejaVu Sans and Serif are vendored under `build/assets/fonts/`.

- [ ] **Step 2: Document fonts and the architecture additions**

In the "Architecture" section, add a short note that `build/fontspec.py` is the font vocabulary (families to TTF faces), that a world declares its typeface in `world.yaml` under `fonts` (a `default` plus an optional `by_locale` override), and that `build/render/` holds the layout-only pipeline. In "Layout pointers", note that the El Jardin Dormido scripts are now refactored into `build/render/` and the live map is at `worlds/floating-isles/assets/map.svg`.

- [ ] **Step 3: Run the suite once more as a sanity check**

Run: `.venv/bin/python -m pytest -q`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: mark Plan 2 built and document render commands and fonts"
```

---

## Self-review

**Spec coverage (section 11, build pipeline, and the section 12 system items that are rendering):**
- Layout-only builders taking `(world, story, locale, reading_level)`: Task 12 `kit.build_kit`. Covered. No hardcoded output paths; output is `dist/` or an explicit `out_dir`.
- Toolchain `reportlab` + `cairosvg` + `pypdf`: Tasks 3, 7, 10, 12. Covered, with no fourth parser dependency.
- Unicode font embedding, selectable per language: Tasks 1, 3 (`fontspec.py`, vendored TTFs, `resolve_family`/`resolve_faces`). Covered, and extended per the user's request to be per-world with a per-locale override (Task 2 model, Task 3 resolver). Task 7's manual check confirms Spanish accents in the world's typeface.
- Per-kit pages (map + rules + narration + puzzles + glossary) and the character sheet: Tasks 7, 9, 10, 11, 12. Covered, with the idea bank included as an extra grown-up page.
- Glossary generated from canon: Task 9. Covered. Map labels from canon are explicitly deferred (the map art still renders, Task 10).
- Rules-page newcomer callout: the callout text lives in the authored `rules.md` (already present in the migrated content), so it renders through Task 7 with no extra code; wiring it for new stories is Plan 5's job.
- Standalone Guide for the Grown-Up PDF per locale: Task 7 renderer, Task 13 test, Task 14 `render-guide` CLI. Content is authored in Plan 5; the build is delivered here, as the spec requires.
- GitHub Action on release (optional): not included, per its optional status and its dependence on having more than one story; it belongs in a later, separate change.

**Items intentionally NOT in this plan (and where they go):** the actual world, story, and guide *prose* (Plans 3 to 5); canon-driven map labels (deferred enhancement); release automation (optional, later). The Sleeping Garden content already exists, so Task 12's manual step builds real kits end to end.

**Placeholder scan:** every code step contains complete, runnable code. The only deferred item, canon-driven map labels, is called out in prose, not left as a TODO; the map still renders as authored art.

**Type and name consistency across tasks:** `fontspec.FAMILIES/KNOWN_FAMILIES/DEFAULT_FAMILY/faces_for/font_path/FaceFiles`; `models.WorldFonts` and `World.fonts`; `fonts.register_family`, `fonts.resolve_family`, `fonts.resolve_faces`, and `fonts.FontFaces` (with `.normal/.bold/.italic/.bold_italic`); `markdown.parse_markdown`, `markdown.inline_to_rl`, and the blocks `Heading/Para/Bullets/Table`; `theme.Theme.from_world/default`, `theme.make_styles(theme, faces)`, `theme.page_painter`; `flowables.blocks_to_flowables(blocks, styles, theme)`; `pages.render_flowables(flows, out, world, *, landscape_page)`, `pages.render_markdown_file(src, out, world, locale)`, `pages.render_guide(src, out, locale)`; `glossary.glossary_flowables(entries, locale, styles, theme)`; `map.render_svg_to_pdf`; `sheets.render_character_sheet(out, locale, tier, theme, faces)`; `kit.build_kit(root, world_id, story_id, locale, reading_level, *, out_dir)` and `kit.NARRATION_BY_LEVEL`; `strings.ui(locale, key)` and `strings.UI`. The kit reads content through Plan 1's `content.load_world/load_story/load_canon`, resolves faces once per `(world, locale)`, and selects the sheet tier from `story.age.recommended`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-wits-and-wonder-02-pdf-build-pipeline.md`.

Plans 3 to 5 build on this pipeline. The Sleeping Garden content already exists in the schema, so the moment Plan 2 lands, real kits render end to end in the world's chosen typeface.

Two execution options:

1. **Subagent-Driven (recommended):** a fresh subagent per task, with two-stage review between tasks and fast iteration.
2. **Inline Execution:** execute the tasks in this session with checkpoints for review.

Which approach?
