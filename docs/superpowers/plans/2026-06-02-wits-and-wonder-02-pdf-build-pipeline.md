# Wits & Wonder, Plan 2: PDF build pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the validated content from Plan 1 into printable kit PDFs: embed a Unicode font, render the per-story markdown (narration, rules, puzzles, idea bank) and the canon-derived glossary into themed A4 pages, merge in the SVG map, add an age-tiered character sheet, and assemble one kit PDF per `(world, story, locale, reading_level)` into `dist/`, plus a standalone Guide for the Grown-Up PDF per locale.

**Architecture:** A new sub-package `build/render/` holds layout-only code that imports Plan 1's models. Content is clean GitHub-flavoured markdown, so the core is a small hand-rolled markdown to reportlab-flowables converter (no markdown-parser dependency: the toolchain stays exactly the three the spec names). A themed reportlab document template paints the world palette (background, dashed border) behind flowing content; headings, paragraphs, bullet lists and tables become flowables. The SVG map renders through cairosvg and pages merge through pypdf. Builders take `(world, story, locale, reading_level)` and never hardcode a string, a colour, or an output path.

**Tech Stack:** Python 3.11+, reportlab (layout and flowables), cairosvg (SVG map to PDF), pypdf (page merge), DejaVu Sans (vendored Unicode TTFs, embedded so accents render). Plan 1's `pydantic` models and YAML loaders are reused unchanged.

---

## The plan set and sequencing

This is **Plan 2** of the sequence introduced in Plan 1. It depends only on Plan 1's models and loaders and delivers built kit PDFs in `dist/`.

- Plan 1: Content model and tooling. Built.
- **Plan 2: PDF build pipeline** (this document).
- Plan 3: The Floating Isles and The Sleeping Garden content. The story already exists in the schema (migrated from El Jardin Dormido); Plan 3 finishes any remaining content polish and wires the three character sheets. It can begin rendering kits the moment Plan 2 lands.
- Plan 4: Greek-myth world and one story.
- Plan 5: Guide for the Grown-Up content. Plan 2 ships the Guide *renderer* (tested against a fixture); Plan 5 authors the real `guide/<locale>/guide.md` and the rules-page callout.

### Decisions locked for this plan

- **No markdown-parser dependency.** The content is constrained GFM (headings, bold, italics, bullet lists, one pipe table). A small line-based parser in `build/render/markdown.py` handles it, keeping the dependency surface exactly `reportlab`, `cairosvg`, `pypdf` as the spec prescribes.
- **DejaVu Sans, vendored.** The four TTFs (regular, bold, oblique, bold-oblique) are copied into `build/render/assets/fonts/` and committed, so the build never depends on system fonts. The font is selected per locale through `font_family_for_locale`, so a future CJK world plugs in without touching layout code.
- **Map labels stay as the existing art for now.** The legacy `mapa.svg` renders as-is. Canon-driven map labels (spec section 9) are a later enhancement, deferred on purpose so this plan ships a working merged kit.
- **Character sheets are generic and age-tiered.** They carry no world-specific magic list, so they are reusable by the Greek world. Labels are localised through `build/render/strings.py`.

---

## File structure (Plan 2)

```
pyproject.toml                       # add the `render` optional-deps group and the build.render package
build/render/
  __init__.py                        # marks the sub-package
  assets/fonts/                      # vendored DejaVu Sans TTFs (regular, bold, oblique, bold-oblique)
  fonts.py                           # register DejaVu with reportlab; per-locale family selection
  theme.py                           # Theme from world palette; ParagraphStyles; the page-background painter
  markdown.py                        # parse GFM into blocks; convert inline markdown to reportlab markup
  flowables.py                       # blocks -> reportlab flowables (headings, paragraphs, bullets, tables)
  pages.py                           # render a list of flowables to a themed PDF; per-content-file and guide builders
  strings.py                         # localised UI strings for the glossary and character sheets
  glossary.py                        # build the who's-who appendix flowables from canon
  sheets.py                          # the three age-tiered character-sheet templates
  map.py                             # cairosvg: an SVG file to a single-page PDF
  kit.py                             # assemble the ordered pages into one kit PDF in dist/
build/__main__.py                    # add `render` and `render-guide` subcommands
tests/
  test_render_fonts.py
  test_render_markdown.py
  test_render_flowables.py
  test_render_pages.py
  test_render_glossary.py
  test_render_sheets.py
  test_render_map.py
  test_render_kit.py
  test_cli_render.py
```

A note on layering: `fonts` and `theme` are the foundation; `markdown` is pure (no reportlab); `flowables` joins markdown blocks to styled reportlab objects; `pages`, `glossary`, `sheets`, `map` each build one kind of page; `kit` orchestrates the order and the merge. Nothing reaches back up a layer.

---

## Task 1: Render dependencies and vendored font embedding

**Files:**
- Modify: `pyproject.toml`
- Create: `build/render/__init__.py`
- Create: `build/render/assets/fonts/` (four vendored TTFs)
- Create: `build/render/fonts.py`
- Test: `tests/test_render_fonts.py`

- [ ] **Step 1: Add the render dependency group and the sub-package to packaging**

In `pyproject.toml`, extend the optional dependencies and the package list. Replace the `[project.optional-dependencies]` and `[tool.setuptools]` blocks with:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
render = [
    "reportlab>=4.0",
    "cairosvg>=2.7",
    "pypdf>=4.0",
]

[tool.setuptools]
packages = ["build", "build.render"]

[tool.setuptools.package-data]
"build.render" = ["assets/fonts/*.ttf"]
```

- [ ] **Step 2: Install the render dependencies**

`cairosvg` needs the system Cairo library. On Debian or Ubuntu it is usually already present as `libcairo2`; if import fails later, install it with the system package manager.

Run:
```bash
.venv/bin/pip install -e ".[dev,render]"
```
Expected: install succeeds; `.venv/bin/python -c "import reportlab, cairosvg, pypdf"` prints nothing and exits 0.

- [ ] **Step 3: Vendor the DejaVu Sans TTFs**

Copy the four faces from the system DejaVu install into the package so the build is self-contained:

```bash
mkdir -p build/render/assets/fonts
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf            build/render/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf       build/render/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf    build/render/assets/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf build/render/assets/fonts/
```
Expected: `ls build/render/assets/fonts/` lists exactly those four `.ttf` files. (DejaVu ships under the permissive Bitstream Vera and Arev licences, so vendoring and redistribution are fine.)

- [ ] **Step 4: Write the failing test**

`tests/test_render_fonts.py`:

```python
from reportlab.pdfbase import pdfmetrics

from build.render import fonts


def test_register_is_idempotent_and_registers_all_faces():
    fonts.register_fonts()
    fonts.register_fonts()  # calling twice must not raise
    registered = set(pdfmetrics.getRegisteredFontNames())
    assert {
        fonts.BODY,
        fonts.BODY_BOLD,
        fonts.BODY_ITALIC,
        fonts.BODY_BOLD_ITALIC,
    } <= registered


def test_family_mapping_resolves_bold_and_italic():
    fonts.register_fonts()
    # reportlab resolves <b>/<i> markup through the family map
    assert pdfmetrics.getFont(fonts.BODY).face is not None


def test_font_family_for_locale_defaults_to_dejavu():
    assert fonts.font_family_for_locale("en-GB") == fonts.FAMILY
    assert fonts.font_family_for_locale("es-ES") == fonts.FAMILY
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_fonts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.fonts'`.

- [ ] **Step 6: Implement the package marker and the fonts module**

`build/render/__init__.py`:

```python
"""Layout-only PDF rendering for Wits & Wonder kits (Plan 2)."""
```

`build/render/fonts.py`:

```python
"""Embed and select the Unicode font for kit rendering.

DejaVu Sans is vendored under assets/fonts so the build never depends on system
fonts. The family is selectable per locale, so a future world in another script
(for example a CJK world) plugs in here without any layout code changing.
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path(__file__).parent / "assets" / "fonts"

FAMILY = "DejaVuSans"
BODY = "DejaVuSans"
BODY_BOLD = "DejaVuSans-Bold"
BODY_ITALIC = "DejaVuSans-Oblique"
BODY_BOLD_ITALIC = "DejaVuSans-BoldOblique"

_FACES = {
    BODY: "DejaVuSans.ttf",
    BODY_BOLD: "DejaVuSans-Bold.ttf",
    BODY_ITALIC: "DejaVuSans-Oblique.ttf",
    BODY_BOLD_ITALIC: "DejaVuSans-BoldOblique.ttf",
}

_registered = False


def register_fonts() -> None:
    """Register every DejaVu face and the family map. Safe to call repeatedly."""
    global _registered
    if _registered:
        return
    for name, filename in _FACES.items():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
    pdfmetrics.registerFontFamily(
        FAMILY,
        normal=BODY,
        bold=BODY_BOLD,
        italic=BODY_ITALIC,
        boldItalic=BODY_BOLD_ITALIC,
    )
    _registered = True


def font_family_for_locale(locale: str) -> str:
    """The font family to use for a locale. DejaVu covers en-GB and es-ES today."""
    return FAMILY
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_fonts.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml build/render/__init__.py build/render/fonts.py \
        build/render/assets/fonts/ tests/test_render_fonts.py
git commit -m "feat: render deps and vendored DejaVu font embedding"
```

---

## Task 2: Markdown block parser

This module is pure: no reportlab, no I/O. It turns a markdown string into a list of block objects. Inline markup is left as raw text and converted in Task 3.

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
converted to reportlab markup later, in flowables.py.
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

## Task 3: Inline markdown to reportlab markup

reportlab paragraphs accept a small HTML-like markup (`<b>`, `<i>`, `<br/>`). This converter escapes the dangerous characters and turns `**bold**` and `*italic*` into that markup. It lives in `markdown.py` beside the parser.

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
Expected: PASS (all parser and inline tests).

- [ ] **Step 5: Commit**

```bash
git add build/render/markdown.py tests/test_render_markdown.py
git commit -m "feat: inline markdown to reportlab markup conversion"
```

---

## Task 4: Theme and the page painter

The theme reads the world palette into named colours, builds the paragraph styles (using the registered fonts), and provides the background painter that draws the cream fill and the dashed rounded border on every page.

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


def test_make_styles_uses_registered_body_font():
    fonts.register_fonts()
    styles = theme.make_styles(theme.Theme.default())
    assert styles["body"].fontName == fonts.BODY
    assert styles["h1"].fontName == fonts.BODY_BOLD
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
when a palette is short or absent, so rendering never crashes on thin content.
"""

from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

from build.models import World
from build.render import fonts

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


def make_styles(theme: "Theme") -> dict[str, ParagraphStyle]:
    """Build the paragraph styles. register_fonts() must have run first."""
    body = ParagraphStyle(
        "body", fontName=fonts.BODY, fontSize=10, leading=14,
        textColor=theme.text, spaceAfter=6,
    )
    return {
        "h1": ParagraphStyle(
            "h1", parent=body, fontName=fonts.BODY_BOLD, fontSize=18, leading=24,
            textColor=white, backColor=theme.primary, alignment=TA_CENTER,
            borderPadding=(7, 8, 7, 8), spaceAfter=12, spaceBefore=2,
        ),
        "h2": ParagraphStyle(
            "h2", parent=body, fontName=fonts.BODY_BOLD, fontSize=13,
            textColor=theme.primary, spaceBefore=10, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", parent=body, fontName=fonts.BODY_BOLD, fontSize=11,
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
git commit -m "feat: world-palette theme, paragraph styles, and page painter"
```

---

## Task 5: Blocks to flowables, and one content file to a PDF

This task wires markdown blocks to reportlab flowables, then renders a full markdown file (a narration page) into a themed PDF. After this task a real, viewable kit page exists.

**Files:**
- Create: `build/render/flowables.py`
- Create: `build/render/pages.py`
- Test: `tests/test_render_flowables.py`
- Test: `tests/test_render_pages.py`

- [ ] **Step 1: Write the failing test for flowables**

`tests/test_render_flowables.py`:

```python
from reportlab.platypus import Paragraph, Table as RLTable

from build.render import fonts, flowables, theme
from build.render import markdown as md


def _styles():
    fonts.register_fonts()
    return theme.make_styles(theme.Theme.default())


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
"""Turn markdown blocks into reportlab flowables using the themed styles."""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from build.render import markdown as md
from build.render.theme import Theme

CONTENT_WIDTH = 210 * mm - 36 * mm  # A4 width minus the page margins
_BULLET = "•"


def _table_style(theme: Theme) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), theme.primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "DejaVuSans"),
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
            table.setStyle(_table_style(theme))
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


def _world():
    return World.model_validate(
        {"id": "floating-isles",
         "name": {"en-GB": "The Floating Isles", "es-ES": "Las Islas Flotantes"},
         "palette": ["#fef9ef", "#4ea24a", "#2bb3a3"]}
    )


def test_render_markdown_file_writes_a_valid_pdf(tmp_path):
    src = tmp_path / "narration.simple.md"
    src.write_text(
        "# The Sleeping Garden\n\nThis morning the island is quiet. Demasiado "
        "silencio: accents like ñ and á must render.\n\n## Stop 1\n\n- look\n- try\n",
        encoding="utf-8",
    )
    out = tmp_path / "narration.pdf"
    pages.render_markdown_file(src, out, _world())
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
"""Render flowables, and whole markdown files, into themed PDFs."""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from build.models import World
from build.render import fonts, flowables, theme
from build.render import markdown as md


def _prepare(world: World) -> tuple[theme.Theme, dict]:
    fonts.register_fonts()
    th = theme.Theme.from_world(world)
    return th, theme.make_styles(th)


def render_flowables(
    flows: list, out_path: Path, world: World, *, landscape_page: bool = False
) -> Path:
    """Build a themed PDF from ready-made flowables."""
    th, _ = _prepare(world)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pagesize = landscape(A4) if landscape_page else A4
    doc = SimpleDocTemplate(
        str(out_path), pagesize=pagesize,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path


def render_markdown_file(src: Path, out_path: Path, world: World) -> Path:
    """Parse a markdown content file and render it as a themed PDF page set."""
    th, styles = _prepare(world)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    return render_flowables(flows, out_path, world)
```

- [ ] **Step 8: Run the pages test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_pages.py -v`
Expected: PASS.

- [ ] **Step 9: Manual visual check (optional but recommended)**

Render a real narration file and eyeball it:
```bash
.venv/bin/python -c "
from pathlib import Path
from build.content import load_world
from build.render import pages
w = load_world(Path('worlds/floating-isles/world.yaml'))
src = Path('worlds/floating-isles/stories/sleeping-garden/content/es-ES/narration.simple.md')
pages.render_markdown_file(src, Path('dist/_preview_narration_es.pdf'), w)
print('wrote dist/_preview_narration_es.pdf')
"
```
Open the PDF (or rasterise it with `pdftoppm -png -r 120 dist/_preview_narration_es.pdf dist/_preview` if poppler is available) and confirm the Spanish accents (ñ, á, í) render and the green title banner appears. Delete the preview afterwards; `dist/` is gitignored so nothing is committed.

- [ ] **Step 10: Commit**

```bash
git add build/render/flowables.py build/render/pages.py \
        tests/test_render_flowables.py tests/test_render_pages.py
git commit -m "feat: markdown blocks to flowables and a content file to a themed PDF"
```

---

## Task 6: Localised UI strings

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

## Task 7: Glossary appendix from canon

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
    fonts.register_fonts()
    styles = theme.make_styles(theme.Theme.default())
    flows = glossary.glossary_flowables(_entries(), "en-GB", styles, theme.Theme.default())
    text = " ".join(f.text for f in flows if isinstance(f, Paragraph))
    assert "Who's Who" in text
    assert "Places" in text and "Creatures" in text
    assert "The Great Garden" in text and "green heart" in text


def test_glossary_uses_the_requested_locale():
    fonts.register_fonts()
    styles = theme.make_styles(theme.Theme.default())
    flows = glossary.glossary_flowables(_entries(), "es-ES", styles, theme.Theme.default())
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

## Task 8: SVG map to a PDF page

cairosvg renders the world's map SVG into a single-page PDF that pypdf can later merge.

**Files:**
- Create: `build/render/map.py`
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

The migrated world needs its map where the kit builder will look for it:
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

## Task 9: Character sheet templates (three age tiers)

Generic, age-tiered sheets with localised labels. They carry no world-specific magic list, so the Greek world reuses them unchanged. They are drawn directly on the canvas (form layout, not flowing prose), reusing the theme painter for the background.

**Files:**
- Create: `build/render/sheets.py`
- Test: `tests/test_render_sheets.py`

- [ ] **Step 1: Write the failing test**

`tests/test_render_sheets.py`:

```python
import pytest
from pypdf import PdfReader

from build.render import sheets, theme
from build.tags import AGE_TIERS


@pytest.mark.parametrize("tier", AGE_TIERS)
def test_each_tier_renders_one_page(tmp_path, tier):
    out = tmp_path / f"sheet_{tier}.pdf"
    sheets.render_character_sheet(out, "en-GB", tier, theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1


def test_unknown_tier_raises(tmp_path):
    with pytest.raises(ValueError):
        sheets.render_character_sheet(tmp_path / "x.pdf", "en-GB", "tween",
                                      theme.Theme.default())


def test_spanish_sheet_renders(tmp_path):
    out = tmp_path / "sheet_es.pdf"
    sheets.render_character_sheet(out, "es-ES", "young", theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_sheets.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.sheets'`.

- [ ] **Step 3: Implement the sheets**

`build/render/sheets.py`:

```python
"""The three age-tiered character sheets: early, young, older.

Generic across worlds (no magic list baked in) and localised through strings.py.
'early' is mostly a drawing space and a name; 'young' adds a magic line and
energy stars; 'older' adds an inventory and notes.
"""

import math
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import fonts, strings
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


def _label(c, theme: Theme, x: float, y: float, text: str) -> None:
    c.setFillColor(theme.primary)
    c.setFont(fonts.BODY_BOLD, 12)
    c.drawString(x, y, text)


def _write_line(c, theme: Theme, x: float, y: float, width: float) -> None:
    c.setStrokeColor(theme.teal)
    c.setLineWidth(1.2)
    c.line(x, y, x + width, y)


def render_character_sheet(
    out_path: Path, locale: str, tier: str, theme: Theme
) -> Path:
    """Render a one-page character sheet for an age tier. Raises on unknown tier."""
    if tier not in AGE_TIERS:
        raise ValueError(f"unknown age tier {tier!r}, expected one of {AGE_TIERS}")
    fonts.register_fonts()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)

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
    c.setFont(fonts.BODY_BOLD, 20)
    c.drawCentredString(W / 2, H - 31 * mm, strings.ui(locale, "sheet_title"))

    y = H - 52 * mm
    _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_name"))
    _write_line(c, theme, 60 * mm, y - 1 * mm, W - 80 * mm)

    if tier in ("young", "older"):
        y -= 14 * mm
        _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_magic"))
        _write_line(c, theme, 20 * mm, y - 8 * mm, W - 40 * mm)

        y -= 20 * mm
        _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_energy"))
        for i in range(5):
            _star(c, 28 * mm + i * 22 * mm, y - 12 * mm, 8 * mm, theme.gold)
        y -= 22 * mm

    # drawing box (every tier, largest for 'early')
    box_h = 70 * mm if tier == "early" else 44 * mm
    _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_draw"))
    c.setStrokeColor(theme.teal)
    c.setLineWidth(1.5)
    c.setDash(4, 4)
    c.roundRect(20 * mm, y - 6 * mm - box_h, W - 40 * mm, box_h, 8, fill=0, stroke=1)
    c.setDash()
    y -= box_h + 14 * mm

    if tier == "older":
        _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_inventory"))
        for k in range(3):
            _write_line(c, theme, 20 * mm, y - 8 * mm - k * 8 * mm, W - 40 * mm)
        y -= 34 * mm
        _label(c, theme, 20 * mm, y, strings.ui(locale, "sheet_notes"))
        for k in range(2):
            _write_line(c, theme, 20 * mm, y - 8 * mm - k * 8 * mm, W - 40 * mm)

    c.setFillColor(theme.text)
    c.setFont(fonts.BODY_ITALIC, 9)
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

## Task 10: Kit assembly and page merge

This task orchestrates everything: it loads the world, story and canon, renders each page to a temporary PDF in the right order, and merges them with pypdf into one kit PDF in `dist/`. The output name encodes the full tuple, so every `(world, story, locale, reading_level)` is distinct.

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
    # No assets/map.svg: the kit still builds, one page fewer.
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "rich",
        out_dir=tmp_path,
    )
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 6


def test_reading_level_selects_narration_file(sample_repo, tmp_path):
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

Loads content through Plan 1's loaders, renders each page to a temporary PDF in
a fixed order, and merges them with pypdf into dist/. The map page is optional:
if the world has no assets/map.svg, the kit builds without it.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build import content
from build.render import flowables, glossary, map as kit_map, pages, sheets, theme

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}

# Grown-up-facing pages that follow the kid-facing narration.
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

    out_dir = out_dir if out_dir is not None else root / "dist"
    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        map_svg = world_dir / "assets" / "map.svg"
        if map_svg.is_file():
            parts.append(kit_map.render_svg_to_pdf(map_svg, tmp_path / "00_map.pdf"))

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_markdown_file(narration, tmp_path / "10_narration.pdf", world)
        )

        for index, filename in enumerate(_PROSE_PAGES, start=2):
            src = content_dir / filename
            parts.append(
                pages.render_markdown_file(src, tmp_path / f"{index}0_{filename}.pdf", world)
            )

        from build.render import fonts
        fonts.register_fonts()
        styles = theme.make_styles(th)
        gloss = glossary.glossary_flowables(canon, locale, styles, th)
        parts.append(pages.render_flowables(gloss, tmp_path / "80_glossary.pdf", world))

        sheet = tmp_path / "90_sheet.pdf"
        sheets.render_character_sheet(sheet, locale, story.age.recommended, th)
        parts.append(sheet)

        out_path = out_dir / f"{world_id}_{story_id}_{locale}_{reading_level}.pdf"
        return _merge(parts, out_path)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: PASS.

- [ ] **Step 5: Build the real Sleeping Garden kit and eyeball it**

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
Expected: four PDFs under `dist/`. Open at least the es-ES one and confirm accents render, the map merges, and pages are in order. (`dist/` is gitignored, so nothing is committed.)

- [ ] **Step 6: Commit**

```bash
git add build/render/kit.py tests/test_render_kit.py
git commit -m "feat: assemble and merge the kit PDF per locale and reading level"
```

---

## Task 11: Standalone Guide for the Grown-Up PDF

The Guide content (`guide/<locale>/guide.md`) is authored in Plan 5. This task ships the *renderer* so Plan 5 only has to write prose. The guide is world-agnostic, so it uses the default theme.

**Files:**
- Modify: `build/render/pages.py`
- Test: `tests/test_render_guide.py`

- [ ] **Step 1: Write the failing test**

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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_guide.py -v`
Expected: FAIL with `AttributeError: module 'build.render.pages' has no attribute 'render_guide'`.

- [ ] **Step 3: Implement render_guide**

Add to `build/render/pages.py` (the imports `A4`, `SimpleDocTemplate`, `md`, `fonts`, `flowables`, `theme` are already present from Task 5):

```python
def render_guide(src: Path, out_path: Path, locale: str = "en-GB") -> Path:
    """Render the world-agnostic Guide for the Grown-Up to a themed PDF.

    Uses the default theme because the guide is shared across all worlds. The
    locale argument is accepted for symmetry and future per-locale typography;
    DejaVu covers en-GB and es-ES today.
    """
    fonts.register_fonts()
    th = theme.Theme.default()
    styles = theme.make_styles(th)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_guide.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/pages.py tests/test_render_guide.py
git commit -m "feat: standalone Guide for the Grown-Up PDF renderer"
```

---

## Task 12: CLI: render and render-guide

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
    out = capsys.readouterr().out
    assert "floating-isles_sleeping-garden_en-GB_simple.pdf" in out
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

(The `render` deps are imported lazily inside the branches so `validate`, `lint` and `catalog` keep working in an environment without the render extra installed.)

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

## Task 13: Documentation refresh

Update the docs that Plan 1 left pointing forward, so the repo reflects that the PDF pipeline now exists.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md` (if present; skip if absent)

- [ ] **Step 1: Update CLAUDE.md status and commands**

In `CLAUDE.md`, in the "Status" section, change the line that says the PDF build pipeline is "Still to come" so Plan 2 is listed as built, and in the "Commands" section add the render commands under the existing CLI examples:

```bash
.venv/bin/python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple        # build one kit PDF into dist/
.venv/bin/python -m build render-guide --root . --locale en-GB  # build the Guide PDF
```

Also update the dependency note: the render extras (`reportlab`, `cairosvg`, `pypdf`) are now installed via `pip install -e ".[dev,render]"`, and DejaVu Sans is vendored under `build/render/assets/fonts/`.

- [ ] **Step 2: Update the layout pointer**

In `CLAUDE.md` under "Layout pointers", note that the El Jardin Dormido scripts have now been refactored into `build/render/`, and that the live map lives at `worlds/floating-isles/assets/map.svg`. Keep the legacy scripts reference only if they are still useful; otherwise note they are superseded.

- [ ] **Step 3: Run the suite once more as a sanity check**

Run: `.venv/bin/python -m pytest -q`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: mark Plan 2 PDF pipeline built and document render commands"
```

---

## Self-review

**Spec coverage (section 11, build pipeline, and the section 12 system items that are rendering):**
- Layout-only builders taking `(world, story, locale, reading_level)`: Task 10 `kit.build_kit`. Covered. No hardcoded output paths; output is `dist/` or an explicit `out_dir`.
- Toolchain `reportlab` + `cairosvg` + `pypdf`: Tasks 1, 5, 8, 10. Covered, and no fourth parser dependency was added.
- Unicode font embedding (DejaVu, per-locale selectable): Task 1 (`fonts.py`, vendored TTFs, `font_family_for_locale`). Covered, and Task 5's manual check confirms Spanish accents.
- Per-kit pages (map + rules + narration + puzzles + glossary) and the character sheet: Tasks 5, 7, 8, 9, 10. Covered. Idea-bank is included as an extra grown-up page.
- Glossary, map labels, idea bank generated from canon and content: glossary from canon (Task 7). Map labels from canon are explicitly deferred (stated in "Decisions locked"); the map art still renders (Task 8).
- Rules page newcomer callout: the callout text lives in the authored `rules.md` (it is already present in the migrated content), so it renders through Task 5 with no extra code. Wiring the callout is Plan 5's remaining job for any new story.
- Standalone Guide for the Grown-Up PDF per locale: Task 11 renderer plus Task 12 `render-guide` CLI. The content is authored in Plan 5; the build is delivered here, as the spec requires.
- GitHub Action on release (optional): not included. It is marked optional in the spec and depends on having content for more than one story; it belongs in a later, separate change.

**Items intentionally NOT in this plan (and where they go):** the actual world, story, and guide *prose* (Plans 3 to 5); canon-driven map labels (deferred enhancement); the release automation (optional, later). The Sleeping Garden content already exists from the migration, so Task 10's manual step builds real kits as an end-to-end check.

**Placeholder scan:** every code step contains complete, runnable code. The only deferred item, canon-driven map labels, is called out in prose, not left as a TODO inside a task; the map still renders as authored art.

**Type and name consistency across tasks:** `fonts.register_fonts`, `fonts.BODY/BODY_BOLD/BODY_ITALIC/BODY_BOLD_ITALIC/FAMILY`, `fonts.font_family_for_locale`; `theme.Theme.from_world/default`, `theme.make_styles`, `theme.page_painter`; `markdown.parse_markdown`, `markdown.inline_to_rl`, and the blocks `Heading/Para/Bullets/Table`; `flowables.blocks_to_flowables` (signature `(blocks, styles, theme)`, used identically in Tasks 7 and 10); `pages.render_flowables` (keyword `landscape_page`), `pages.render_markdown_file`, `pages.render_guide`; `glossary.glossary_flowables(entries, locale, styles, theme)`; `map.render_svg_to_pdf`; `sheets.render_character_sheet(out_path, locale, tier, theme)`; `kit.build_kit(root, world_id, story_id, locale, reading_level, *, out_dir)` and `kit.NARRATION_BY_LEVEL`; `strings.ui(locale, key)` and `strings.UI`. The kit builder reads content through Plan 1's `content.load_world/load_story/load_canon`, matching their signatures, and selects the sheet tier from `story.age.recommended` (an `Age` field defined in Plan 1).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-wits-and-wonder-02-pdf-build-pipeline.md`.

Plans 3 to 5 (the two worlds and their stories, and the Guide content) build on this pipeline. The Sleeping Garden content already exists in the schema, so the moment Plan 2 lands, real kits render end to end.

Two execution options:

1. **Subagent-Driven (recommended):** a fresh subagent per task, with two-stage review between tasks and fast iteration.
2. **Inline Execution:** execute the tasks in this session with checkpoints for review.

Which approach?
