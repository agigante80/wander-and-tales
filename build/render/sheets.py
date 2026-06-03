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
    c.setFillColor(PAGE_FILL)
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
