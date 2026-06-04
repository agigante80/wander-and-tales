"""The three age-tiered character sheets: early, young, older.

Generic across worlds (no specific magic list baked in), localised through
strings.py and drawn in the resolved font faces on the white page background. 'early'
is a big draw space and a name. 'young' and 'older' fill the whole A4 page: a
portrait box and identity at the top, a three-slot magics box, and a six-slot
'What I carry' box; 'older' adds a couple of notes lines.

A blank sheet is the play material. When an `example` (a pre-filled hero) and a
`hero_image` are passed, the same layout is filled in and the hero drawing is placed
in the draw box, producing a ready-to-use or inspiration example sheet.
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


def _star(c, cx: float, cy: float, r: float, stroke, *, fill_colour=None) -> None:
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
    c.setFillColor(fill_colour or white)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.5)
    c.drawPath(p, fill=1, stroke=1)


def render_character_sheet(
    out_path: Path,
    locale: str,
    tier: str,
    theme: Theme,
    faces: FontFaces,
    *,
    example: dict | None = None,
    hero_image: Path | None = None,
) -> Path:
    """Render a one-page A4 character sheet for an age tier. Raises on unknown tier.

    When `example` is given (keys: name, hero_of, magics as (name, does) pairs,
    energy, carry as a list of strings) the fields are filled in, and `hero_image`,
    if given, is drawn in the portrait box.
    """
    if tier not in AGE_TIERS:
        raise ValueError(f"unknown age tier {tier!r}, expected one of {AGE_TIERS}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)

    def label(x: float, y: float, text: str, size: float = 12, color=None) -> None:
        c.setFillColor(color or theme.primary)
        c.setFont(faces.bold, size)
        c.drawString(x, y, text)

    def value(x: float, y: float, text: str, size: float = 10) -> None:
        if not text:
            return
        c.setFillColor(theme.text)
        c.setFont(faces.normal, size)
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
        if example:
            value(60 * mm, H - 44 * mm, example.get("name", ""))
        label(20 * mm, H - 58 * mm, strings.ui(locale, "sheet_draw"))
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.5)
        c.setDash(4, 4)
        c.roundRect(20 * mm, 24 * mm, W - 40 * mm, H - 90 * mm, 8, fill=0, stroke=1)
        c.setDash()
        if hero_image is not None:
            _draw_hero(c, hero_image, 22 * mm, 26 * mm, W - 44 * mm, H - 94 * mm)
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
    if hero_image is not None:
        _draw_hero(c, hero_image, 20 * mm, top - pbox_h + 2 * mm, pbox_w - 4 * mm, pbox_h - 11 * mm)

    rx = 18 * mm + pbox_w + 8 * mm
    rw = W - 18 * mm - rx
    label(rx, top - 6 * mm, strings.ui(locale, "sheet_name"))
    line(rx, top - 12 * mm, rw)
    label(rx, top - 24 * mm, strings.ui(locale, "sheet_hero_type"))
    line(rx, top - 30 * mm, rw)
    if example:
        value(rx + 2 * mm, top - 10 * mm, example.get("name", ""))
        value(rx + 2 * mm, top - 28 * mm, example.get("hero_of", ""))
    label(rx, top - 42 * mm, strings.ui(locale, "sheet_energy"), size=9)
    # Always leave the five energy stars empty, even on an example hero, so a printed
    # sheet starts fresh: a star is coloured in only when the player spends energy.
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
    magics = example.get("magics", []) if example else []
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
        if s < len(magics):
            mname, mdoes = magics[s]
            value(tx + 36 * mm, sy - 4 * mm, mname)
            value(tx + 22 * mm, sy - 15 * mm, mdoes, size=8)

    # what I carry box: six slots in a 2 by 3 grid
    cbox_top = mbox_y - 8 * mm
    cbox_h = 46 * mm if tier == "young" else 40 * mm
    cbox_y = cbox_top - cbox_h
    box(18 * mm, cbox_y, W - 36 * mm, cbox_h, theme.gold)
    label(22 * mm, cbox_top - 7 * mm, strings.ui(locale, "sheet_inventory"))
    col_w = (W - 36 * mm - 8 * mm) / 2
    carry = example.get("carry", []) if example else []
    for r in range(3):
        for col in range(2):
            ix = 22 * mm + col * (col_w + 4 * mm)
            iy = cbox_top - 16 * mm - r * 10 * mm
            line(ix, iy, col_w - 6 * mm)
            idx = r * 2 + col
            if idx < len(carry):
                value(ix + 1 * mm, iy + 1.5 * mm, carry[idx], size=9)

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


def _draw_hero(c, path: Path, x: float, y: float, w: float, h: float) -> None:
    """Draw the hero image to fit inside the box, preserving aspect, centred."""
    try:
        c.drawImage(
            str(path), x, y, width=w, height=h,
            preserveAspectRatio=True, anchor="c", mask="auto",
        )
    except Exception:
        pass
