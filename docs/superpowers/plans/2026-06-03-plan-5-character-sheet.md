# Plan 5: The Full-Page A4 Character Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the `young` and `older` character sheets to fill the whole A4 page with clearly bordered, colour-coded sections: a portrait box and identity (name, "I am a hero of", energy stars) at the top, a three-slot "My magics" box (each slot a draw-symbol square plus two lines), and a six-slot "What I carry" box at the bottom. `early` stays a big draw box plus a name.

**Architecture:** A single rewrite of `build/render/sheets.py`'s `render_character_sheet`, drawing on the white page background (Plan 1) with the world theme colours for the section borders, plus five new localized strings. No new modules. The existing sheet tests (one page per tier, unknown tier raises, Spanish renders) keep guarding it.

**Tech Stack:** Python 3.11, reportlab canvas, pytest.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Part 5). Depends on Plan 1 (the `PAGE_FILL` white background).

---

## File Structure

- `build/render/strings.py` (modify): add `sheet_hero_type`, `sheet_magics`, `sheet_magic_is`, `sheet_magic_does`, `sheet_magic_symbol`; update `sheet_inventory` to "What I carry"; drop `sheet_magic`. en-GB and es-ES in lock-step (the strings test asserts key parity).
- `build/render/sheets.py` (rewrite): the new full-page layout for `young`/`older`, `early` unchanged in spirit.
- `tests/test_render_sheets.py` (modify): add an `older` Spanish render assertion.

---

### Task 1: The new sheet strings

**Files:**
- Modify: `build/render/strings.py`
- Test: `tests/test_render_strings.py` (existing parity test guards this)

- [ ] **Step 1: Update the strings**

In `build/render/strings.py`, in the `"en-GB"` dict: replace the `sheet_magic` line and the `sheet_inventory` line, and add the five new keys, so the sheet block reads:

```python
        "sheet_title": "My Adventure Sheet",
        "sheet_name": "My name",
        "sheet_hero_type": "I am a hero of",
        "sheet_magics": "My magics",
        "sheet_magic_is": "My magic is",
        "sheet_magic_does": "It can",
        "sheet_magic_symbol": "draw it",
        "sheet_energy": "My energy stars (colour one in when you spend it)",
        "sheet_draw": "Draw your hero",
        "sheet_inventory": "What I carry",
        "sheet_notes": "Notes",
        "sheet_footer": "Here nobody loses. If a try does not work, find another way.",
```

In the `"es-ES"` dict, the matching block:

```python
        "sheet_title": "Mi Ficha de Aventura",
        "sheet_name": "Mi nombre",
        "sheet_hero_type": "Soy un héroe de",
        "sheet_magics": "Mis magias",
        "sheet_magic_is": "Mi magia es",
        "sheet_magic_does": "Puede",
        "sheet_magic_symbol": "dibújala",
        "sheet_energy": "Mis estrellas de energía (colorea una al gastarla)",
        "sheet_draw": "Dibuja a tu héroe o heroína",
        "sheet_inventory": "Lo que llevo",
        "sheet_notes": "Notas",
        "sheet_footer": "Aquí nadie pierde. Si algo no sale, se busca otra manera.",
```

(There is no longer a `sheet_magic` key in either locale.)

- [ ] **Step 2: Run the strings parity test**

Run: `.venv/bin/python -m pytest tests/test_render_strings.py -v`
Expected: PASS (en-GB and es-ES still have identical key sets).

- [ ] **Step 3: Confirm nothing else references the dropped key**

Run: `grep -rn "sheet_magic\"" build/ tests/`
Expected: only `sheet_magics`, `sheet_magic_is`, `sheet_magic_does`, `sheet_magic_symbol` appear; no bare `"sheet_magic"`. (If the old `sheets.py` still references `"sheet_magic"`, that is fixed in Task 2.)

- [ ] **Step 4: Commit**

```bash
git add build/render/strings.py
git commit -m "feat(render): sheet strings for three magics, hero type, and carry"
git push origin main
```

---

### Task 2: Rewrite the character sheet layout

**Files:**
- Rewrite: `build/render/sheets.py`
- Test: `tests/test_render_sheets.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_sheets.py`:

```python
def test_older_spanish_sheet_renders_one_page(tmp_path):
    out = tmp_path / "sheet_older_es.pdf"
    sheets.render_character_sheet(out, "es-ES", "older", theme.Theme.default(), _faces())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_sheets.py::test_older_spanish_sheet_renders_one_page -v`
Expected: At this point it may PASS against the old layout (older already rendered). It will exercise the NEW strings only after Step 3. Run it again after Step 3; the purpose here is to lock in that `older`/es-ES renders one page through the rewrite.

- [ ] **Step 3: Rewrite `sheets.py`**

Replace the entire contents of `build/render/sheets.py` with:

```python
"""The three age-tiered character sheets: early, young, older.

Generic across worlds (no specific magic list baked in), localised through
strings.py and drawn in the resolved font faces on the white page background. 'early'
is a big draw space and a name. 'young' and 'older' fill the whole A4 page: a
portrait box and identity at the top, a three-slot magics box, and a six-slot
'What I carry' box; 'older' adds a couple of notes lines.
"""

import math
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import strings
from build.render.fonts import FontFaces
from build.render.theme import Theme, PAGE_FILL
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
    """Render a one-page A4 character sheet for an age tier. Raises on unknown tier."""
    if tier not in AGE_TIERS:
        raise ValueError(f"unknown age tier {tier!r}, expected one of {AGE_TIERS}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)

    def label(x: float, y: float, text: str, size: float = 12, color=None) -> None:
        c.setFillColor(color or theme.primary)
        c.setFont(faces.bold, size)
        c.drawString(x, y, text)

    def line(x: float, y: float, width: float) -> None:
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.2)
        c.line(x, y, x + width, y)

    def box(x: float, y: float, w: float, h: float, color) -> None:
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        c.roundRect(x, y, w, h, 8, fill=0, stroke=1)

    # page background (white) and the dashed border
    c.setFillColor(PAGE_FILL)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(theme.border)
    c.setLineWidth(3)
    c.setDash(2, 10)
    c.roundRect(8 * mm, 8 * mm, W - 16 * mm, H - 16 * mm, 10, fill=0, stroke=1)
    c.setDash()

    # title banner
    c.setFillColor(theme.primary)
    c.roundRect(16 * mm, H - 30 * mm, W - 32 * mm, 16 * mm, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(faces.bold, 20)
    c.drawCentredString(W / 2, H - 24 * mm, strings.ui(locale, "sheet_title"))

    if tier == "early":
        label(20 * mm, H - 44 * mm, strings.ui(locale, "sheet_name"))
        line(56 * mm, H - 45 * mm, W - 76 * mm)
        label(20 * mm, H - 58 * mm, strings.ui(locale, "sheet_draw"))
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.5)
        c.setDash(4, 4)
        c.roundRect(20 * mm, 24 * mm, W - 40 * mm, H - 90 * mm, 8, fill=0, stroke=1)
        c.setDash()
        c.setFillColor(theme.text)
        c.setFont(faces.italic, 9)
        c.drawCentredString(W / 2, 14 * mm, strings.ui(locale, "sheet_footer"))
        c.showPage()
        c.save()
        return out_path

    # young + older: full-page form
    top = H - 38 * mm

    # identity row: portrait box (left) + name / hero type / energy stars (right)
    pbox_w, pbox_h = 66 * mm, 52 * mm
    box(18 * mm, top - pbox_h, pbox_w, pbox_h, theme.teal)
    label(22 * mm, top - 6 * mm, strings.ui(locale, "sheet_draw"), size=10, color=theme.teal)

    rx = 18 * mm + pbox_w + 8 * mm
    rw = W - 18 * mm - rx
    label(rx, top - 6 * mm, strings.ui(locale, "sheet_name"))
    line(rx, top - 12 * mm, rw)
    label(rx, top - 24 * mm, strings.ui(locale, "sheet_hero_type"))
    line(rx, top - 30 * mm, rw)
    label(rx, top - 42 * mm, strings.ui(locale, "sheet_energy"), size=9)
    for i in range(5):
        _star(c, rx + 6 * mm + i * 12 * mm, top - 50 * mm, 5 * mm, theme.gold)

    # magics box: three slots, each a draw-symbol square plus two lines
    mbox_top = top - pbox_h - 8 * mm
    mbox_h = 74 * mm
    mbox_y = mbox_top - mbox_h
    box(18 * mm, mbox_y, W - 36 * mm, mbox_h, theme.primary)
    label(22 * mm, mbox_top - 7 * mm, strings.ui(locale, "sheet_magics"))
    slot_h = 21 * mm
    square = 14 * mm
    for s in range(3):
        sy = mbox_top - 14 * mm - s * slot_h
        c.setStrokeColor(theme.rose)
        c.setLineWidth(1.2)
        c.roundRect(22 * mm, sy - square, square, square, 4, fill=0, stroke=1)
        c.setFillColor(theme.rose)
        c.setFont(faces.italic, 7)
        c.drawCentredString(
            22 * mm + square / 2, sy - square + 5, strings.ui(locale, "sheet_magic_symbol")
        )
        tx = 22 * mm + square + 6 * mm
        tw = W - 22 * mm - tx
        label(tx, sy - 4 * mm, strings.ui(locale, "sheet_magic_is"), size=10)
        line(tx + 34 * mm, sy - 5 * mm, tw - 34 * mm)
        label(tx, sy - 15 * mm, strings.ui(locale, "sheet_magic_does"), size=10)
        line(tx + 20 * mm, sy - 16 * mm, tw - 20 * mm)

    # what I carry box: six slots in a 2 by 3 grid
    cbox_top = mbox_y - 8 * mm
    cbox_h = 46 * mm if tier == "young" else 40 * mm
    cbox_y = cbox_top - cbox_h
    box(18 * mm, cbox_y, W - 36 * mm, cbox_h, theme.gold)
    label(22 * mm, cbox_top - 7 * mm, strings.ui(locale, "sheet_inventory"))
    col_w = (W - 36 * mm - 8 * mm) / 2
    for r in range(3):
        for col in range(2):
            ix = 22 * mm + col * (col_w + 4 * mm)
            iy = cbox_top - 16 * mm - r * 10 * mm
            line(ix, iy, col_w - 6 * mm)

    if tier == "older":
        ny = cbox_y - 8 * mm
        label(20 * mm, ny, strings.ui(locale, "sheet_notes"))
        for k in range(2):
            line(20 * mm, ny - 7 * mm - k * 8 * mm, W - 40 * mm)

    c.setFillColor(theme.text)
    c.setFont(faces.italic, 9)
    c.drawCentredString(W / 2, 14 * mm, strings.ui(locale, "sheet_footer"))
    c.showPage()
    c.save()
    return out_path
```

- [ ] **Step 4: Run the sheet tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_sheets.py -v`
Expected: PASS (each tier renders one page, unknown tier raises, Spanish `young` and `older` render).

- [ ] **Step 5: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS.

- [ ] **Step 6: Manually verify the sheet layout**

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from build.render import fonts, sheets, theme
faces = fonts.register_family("dejavu-sans")
for tier in ("early", "young", "older"):
    sheets.render_character_sheet(Path(f"/tmp/sheet_{tier}.pdf"), "en-GB", tier, theme.Theme.default(), faces)
PY
pdftoppm -png -r 110 /tmp/sheet_young.pdf /tmp/sy
pdftoppm -png -r 110 /tmp/sheet_older.pdf /tmp/so
```
Open `/tmp/sy-1.png` and `/tmp/so-1.png`: confirm the portrait box and identity row at the top, three magic slots each with a draw square and two lines, the six-slot "What I carry" grid, the energy stars under "I am a hero of", a white background, and (for older) the notes lines. Adjust spacing constants if any box overlaps.

- [ ] **Step 7: Commit**

```bash
git add build/render/sheets.py tests/test_render_sheets.py
git commit -m "feat(render): full-page A4 character sheet with three magics and carry grid"
git push origin main
```

---

## Self-Review

- **Spec coverage (Part 5):** title banner, identity row (portrait box plus name, "I am a hero of", energy stars under it), the three-slot magics box (draw square plus "My magic is" and "It can"), the six-slot "What I carry" grid for both `young` and `older`, notes for `older`, and the footer; `early` stays a big draw box and name. The white background comes from `PAGE_FILL`.
- **Placeholder scan:** none; the full canvas code is given.
- **Type consistency:** `render_character_sheet(out_path, locale, tier, theme, faces)` keeps its existing signature, so `kit.build_story_pack` (Plan 3) calls it unchanged. All five new string keys are added in Task 1 before Task 2 uses them; `sheet_inventory` and `sheet_draw`/`sheet_energy`/`sheet_notes`/`sheet_footer`/`sheet_name`/`sheet_title` are reused; `sheet_magic` is gone and unreferenced.
- **Note:** exact spacing is a manual-eyeball refinement (Step 6); the automated tests assert one A4 page per tier, which is the invariant that matters for the pipeline.
