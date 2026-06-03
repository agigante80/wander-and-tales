# Plan 1: Print Presentation (A4 hard rule and white background) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every generated page A4 (content portrait, map landscape) and paint the printable page background white instead of cream, so kits print cleanly at home.

**Architecture:** Two small, independent renderer changes plus a guard test. The map renderer (`build/render/map.py`) places the native SVG-derived PDF onto an A4 landscape page with pypdf, preserving aspect and centring. The page background becomes a white module constant in `build/render/theme.py`, reused by the character sheet. A new test asserts every page of a built kit is A4 in one of the two orientations.

**Tech Stack:** Python 3.11, reportlab, cairosvg, pypdf, pytest.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Part 1).

---

## File Structure

- `build/render/map.py` (modify): route both map renderers through a new private `_place_on_a4_landscape` helper so the map page is always A4 landscape.
- `build/render/theme.py` (modify): add a `PAGE_FILL = white` constant and use it in `page_painter`.
- `build/render/sheets.py` (modify): fill the sheet page with `PAGE_FILL` instead of `theme.background`.
- `tests/test_render_map.py` (modify): assert the map page is A4 landscape.
- `tests/test_render_theme.py` (modify): assert `PAGE_FILL` is white.
- `tests/test_render_kit.py` (modify): assert every page of a built kit is A4.

---

### Task 1: Map page is always A4 landscape

**Files:**
- Modify: `build/render/map.py`
- Test: `tests/test_render_map.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_map.py`:

```python
from pypdf import PdfReader

from build.render import map as kit_map

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)

_A4_LANDSCAPE = (841.89, 595.28)


def test_map_page_is_a4_landscape(tmp_path):
    svg = tmp_path / "m.svg"
    svg.write_text(_TINY_SVG, encoding="utf-8")
    out = kit_map.render_svg_to_pdf(svg, tmp_path / "m.pdf")
    page = PdfReader(str(out)).pages[0]
    assert abs(float(page.mediabox.width) - _A4_LANDSCAPE[0]) < 2
    assert abs(float(page.mediabox.height) - _A4_LANDSCAPE[1]) < 2


def test_template_map_page_is_a4_landscape(tmp_path):
    svg = tmp_path / "m.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="100">'
        '<text data-label="title" x="10" y="20"></text></svg>',
        encoding="utf-8",
    )
    out = kit_map.render_map_template(svg, tmp_path / "t.pdf", {"title": "Hi"})
    page = PdfReader(str(out)).pages[0]
    assert abs(float(page.mediabox.width) - _A4_LANDSCAPE[0]) < 2
    assert abs(float(page.mediabox.height) - _A4_LANDSCAPE[1]) < 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_map.py::test_map_page_is_a4_landscape -v`
Expected: FAIL (the page is currently 200x120 pt, not A4 landscape).

- [ ] **Step 3: Implement the A4 landscape placement**

In `build/render/map.py`, add these imports near the top (after the existing imports):

```python
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from pypdf import PdfReader, PdfWriter, Transformation
```

Add this module constant and helper (place it above `render_svg_to_pdf`):

```python
_A4_LANDSCAPE = landscape(A4)  # (841.89, 595.27) points
_MAP_MARGIN_PT = 18  # keep the board clear of the page edge


def _place_on_a4_landscape(native_pdf: bytes, out_path: Path) -> Path:
    """Centre a native-size one-page PDF on an A4 landscape page, preserving aspect.

    cairosvg renders the SVG at its own size; this fits that page onto A4 landscape
    so every map, whatever its source dimensions, becomes one A4 landscape page that
    merges cleanly with the portrait content pages.
    """
    target_w, target_h = _A4_LANDSCAPE
    src = PdfReader(BytesIO(native_pdf)).pages[0]
    src_w = float(src.mediabox.width)
    src_h = float(src.mediabox.height)
    scale = min(
        (target_w - 2 * _MAP_MARGIN_PT) / src_w,
        (target_h - 2 * _MAP_MARGIN_PT) / src_h,
    )
    tx = (target_w - src_w * scale) / 2
    ty = (target_h - src_h * scale) / 2
    writer = PdfWriter()
    page = writer.add_blank_page(width=target_w, height=target_h)
    page.merge_transformed_page(src, Transformation().scale(scale).translate(tx, ty))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path
```

Replace the body of `render_svg_to_pdf`:

```python
def render_svg_to_pdf(svg_path: Path, out_path: Path) -> Path:
    """Convert an SVG file to a one-page A4 landscape PDF at out_path."""
    native = cairosvg.svg2pdf(url=str(svg_path))
    return _place_on_a4_landscape(native, out_path)
```

Replace the body of `render_map_template`:

```python
def render_map_template(svg_path: Path, out_path: Path, labels: dict[str, str]) -> Path:
    """Fill a template SVG with localized labels, render to one A4 landscape PDF."""
    filled = fill_template(svg_path.read_text(encoding="utf-8"), labels)
    native = cairosvg.svg2pdf(bytestring=filled.encode("utf-8"))
    return _place_on_a4_landscape(native, out_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -v`
Expected: PASS (both new tests and the existing map tests).

- [ ] **Step 5: Commit**

```bash
git add build/render/map.py tests/test_render_map.py
git commit -m "feat(render): always place the map on an A4 landscape page"
git push origin main
```

---

### Task 2: White printable page background

**Files:**
- Modify: `build/render/theme.py`
- Modify: `build/render/sheets.py`
- Test: `tests/test_render_theme.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_theme.py`:

```python
from reportlab.lib.colors import white

from build.render import theme


def test_page_fill_is_white():
    assert theme.PAGE_FILL == white
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_theme.py::test_page_fill_is_white -v`
Expected: FAIL with `AttributeError: module 'build.render.theme' has no attribute 'PAGE_FILL'`.

- [ ] **Step 3: Add the constant and use it**

In `build/render/theme.py`, add this constant just below the existing `_BORDER` definition:

```python
PAGE_FILL = white  # printable page background: white prints cleanly and cheaply
```

In the same file, change the fill colour inside `page_painter`'s `paint` from `theme.background` to `PAGE_FILL`:

```python
        canvas.setFillColor(PAGE_FILL)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
```

In `build/render/sheets.py`, change the import line:

```python
from build.render.theme import Theme, PAGE_FILL
```

and change the page-fill line (currently `c.setFillColor(theme.background)` near "background and border") to:

```python
    # background and border
    c.setFillColor(PAGE_FILL)
    c.rect(0, 0, W, H, fill=1, stroke=0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_theme.py tests/test_render_sheets.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/theme.py build/render/sheets.py tests/test_render_theme.py
git commit -m "feat(render): paint the printable page background white"
git push origin main
```

---

### Task 3: Guard test, every kit page is A4

**Files:**
- Test: `tests/test_render_kit.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_kit.py` (the `_NEUTRAL_MAP` constant already exists in this file):

```python
def _is_a4(width: float, height: float) -> bool:
    portrait = (595.276, 841.890)
    return (
        (abs(width - portrait[0]) < 2 and abs(height - portrait[1]) < 2)
        or (abs(width - portrait[1]) < 2 and abs(height - portrait[0]) < 2)
    )


def test_every_kit_page_is_a4(sample_repo, tmp_path):
    assets = (
        sample_repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_NEUTRAL_MAP, encoding="utf-8")
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    for page in PdfReader(str(out)).pages:
        assert _is_a4(float(page.mediabox.width), float(page.mediabox.height))
```

- [ ] **Step 2: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py::test_every_kit_page_is_a4 -v`
Expected: PASS (content pages are A4 portrait from `SimpleDocTemplate(A4)`; the map page is now A4 landscape from Task 1; the sheet is A4). If it FAILS, a page is the wrong size and the offending builder must be fixed before proceeding.

- [ ] **Step 3: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS (full suite green).

- [ ] **Step 4: Manually verify the white background**

Run:
```bash
.venv/bin/python -m build render --root . \
  --world floating-isles --story sleeping-garden --locale en-GB --reading-level simple
pdftoppm -png -r 110 dist/floating-isles_sleeping-garden_en-GB_simple.pdf /tmp/kit
```
Open `/tmp/kit-1.png` and confirm the page background is white, the dashed green border and coloured banners remain, and the map page is landscape.

- [ ] **Step 5: Commit**

```bash
git add tests/test_render_kit.py
git commit -m "test(render): assert every kit page is A4 (portrait or landscape)"
git push origin main
```

---

## Self-Review

- **Spec coverage (Part 1):** A4 everywhere is enforced by Task 1 (map to A4 landscape) plus Task 3 (the per-page invariant test); white background is Task 2 (painter and sheet fill). The `theme.Theme.background` field is intentionally left on the model (worlds still declare a palette); only the printable fill stops using it.
- **Placeholder scan:** none; every step shows the exact code or command.
- **Type consistency:** `_place_on_a4_landscape(native_pdf: bytes, out_path: Path)` is used by both `render_svg_to_pdf` and `render_map_template`; `PAGE_FILL` is defined in `theme.py` and imported by `sheets.py`.
