"""The three age-tiered character sheets: early, young, older.

Generic across worlds (no specific magic list baked in), localised through
strings.py and drawn on a plain white page. The design is a system: a warm header
band, a hero card, and colour section chips whose hues come from the world Theme, so
each world inherits its own palette while the type stays constant. 'early' is a big
draw space and a name; 'young' and 'older' are the full form (identity, magics,
what I carry); 'older' adds a notes panel.

A blank sheet is the play material. When an `example` (a pre-filled hero) and a
`hero_image` are passed, the same layout is filled in: printed labels in the body
face, the example's answers in the handwriting face (wrapped, so long answers flow to
a second line), and the portrait drawn in the hero card.
"""

import math
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import fonts, images, strings
from build.render.theme import Theme, PAGE_FILL, tint
from build.tags import AGE_TIERS

W, H = A4
M = 14 * mm  # page margin


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
    c.setLineWidth(1.2)
    c.drawPath(p, fill=1, stroke=1)


def render_character_sheet(
    out_path: Path,
    locale: str,
    tier: str,
    theme: Theme,
    *,
    world_name: str = "",
    example: dict | None = None,
    hero_image: Path | None = None,
) -> Path:
    """Render a one-page A4 character sheet for an age tier. Raises on unknown tier.

    When `example` is given (keys: name, hero_of, magics as (name, does) pairs,
    carry as a list of strings) the fields are filled in with the handwriting face,
    and `hero_image`, if given, is drawn in the hero card. `energy` is ignored: the
    stars are always drawn empty so a printed sheet starts fresh.
    """
    if tier not in AGE_TIERS:
        raise ValueError(f"unknown age tier {tier!r}, expected one of {AGE_TIERS}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)
    f = fonts.sheet_faces()
    muted = tint(theme.text, 0.45)

    def s(key: str) -> str:
        return strings.ui(locale, key)

    def text(x, y, t, font, size, color) -> None:
        if not t:
            return
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, t)

    def ctext(cx, y, t, font, size, color) -> None:
        if not t:
            return
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawCentredString(cx, y, t)

    def wrap_lines(t, font, size, max_w):
        out, cur = [], ""
        for word in t.split():
            trial = (cur + " " + word).strip()
            if not cur or c.stringWidth(trial, font, size) <= max_w:
                cur = trial
            else:
                out.append(cur)
                cur = word
        if cur:
            out.append(cur)
        return out or [""]

    def wrapped(x, y, t, font, size, max_w, leading, color) -> float:
        c.setFillColor(color)
        c.setFont(font, size)
        for ln in wrap_lines(t, font, size, max_w):
            c.drawString(x, y, ln)
            y -= leading
        return y

    def wline(x, y, w) -> None:
        c.setDash()
        c.setStrokeColor(tint(theme.teal, 0.25))
        c.setLineWidth(0.9)
        c.line(x, y, x + w, y)

    def kicker(x, y, t) -> None:
        # A plain uppercase label. Note: do NOT letter-space via a text object's
        # setCharSpace here, as the Tc text-state leaks into every later string and
        # silently widens them (it overflowed the magic descriptions before).
        if not t:
            return
        c.setFillColor(theme.teal)
        c.setFont(f.body_bold, 7)
        c.drawString(x, y, t.upper())

    def chip(x, top_y, w, label, hue, body_h, header_h=8 * mm) -> float:
        """Filled hue header tab over a white, hue-keylined body panel. Returns the
        body's bottom y so the caller can place the next section below it."""
        bottom = top_y - header_h - body_h
        c.setDash()
        c.setFillColor(white)
        c.setStrokeColor(hue)
        c.setLineWidth(1.0)
        c.roundRect(x, bottom, w, header_h + body_h, 6, fill=1, stroke=1)
        c.setFillColor(hue)
        c.roundRect(x, top_y - header_h, w, header_h, 6, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(f.display, 9.5)
        c.drawString(x + 4 * mm, top_y - header_h + 2.4 * mm, label)
        return bottom

    def header_band(y_top) -> float:
        band_h = 22 * mm
        c.setDash()
        c.setFillColor(tint(theme.gold, 0.85))
        c.setStrokeColor(tint(theme.gold, 0.5))
        c.setLineWidth(1.0)
        c.roundRect(M, y_top - band_h, W - 2 * M, band_h, 8, fill=1, stroke=1)
        kicker(M + 5 * mm, y_top - 8 * mm, world_name)
        text(M + 5 * mm, y_top - 17 * mm, s("sheet_title"), f.display, 20, theme.primary)
        # a small constellation ornament at the right (world-neutral, ties to the stars)
        ox, oy = W - M - 15 * mm, y_top - band_h / 2
        _star(c, ox, oy + 3 * mm, 3.0 * mm, theme.gold, fill_colour=theme.gold)
        _star(c, ox + 6.5 * mm, oy - 2 * mm, 2.0 * mm, theme.gold, fill_colour=tint(theme.gold, 0.35))
        _star(c, ox - 5 * mm, oy - 3 * mm, 1.7 * mm, theme.gold, fill_colour=tint(theme.gold, 0.35))
        # dotted golden path under the band
        c.setDash(1.3, 4.5)
        c.setStrokeColor(theme.gold)
        c.setLineWidth(1.4)
        c.line(M, y_top - band_h - 3 * mm, W - M, y_top - band_h - 3 * mm)
        c.setDash()
        return y_top - band_h - 8 * mm

    def footer_ribbon() -> None:
        rib_y, rib_h = 16 * mm, 9 * mm  # sits above the stamped version footer (~11mm)
        c.setDash()
        c.setFillColor(tint(theme.gold, 0.85))
        c.setStrokeColor(tint(theme.gold, 0.5))
        c.setLineWidth(0.8)
        c.roundRect(M + 6 * mm, rib_y, W - 2 * M - 12 * mm, rib_h, 4, fill=1, stroke=1)
        _star(c, M + 11 * mm, rib_y + rib_h / 2, 1.8 * mm, theme.gold, fill_colour=theme.gold)
        _star(c, W - M - 11 * mm, rib_y + rib_h / 2, 1.8 * mm, theme.gold, fill_colour=theme.gold)
        ctext(W / 2, rib_y + 3 * mm, s("sheet_footer"), f.body, 7.2, theme.text)

    # white page background (no border)
    c.setFillColor(PAGE_FILL)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    y = header_band(H - M)

    if tier == "early":
        # a name line, then a big draw card filling the page
        text(M + 2 * mm, y - 6 * mm, s("sheet_name").upper(), f.body_bold, 8, muted)
        wline(M + 2 * mm, y - 12 * mm, W - 2 * M - 4 * mm)
        if example:
            text(M + 4 * mm, y - 11 * mm, example.get("name", ""), f.hand, 14, theme.text)
        card_top = y - 18 * mm
        card_bottom = 30 * mm
        c.setFillColor(tint(theme.teal, 0.92))
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.4)
        c.roundRect(M, card_bottom, W - 2 * M, card_top - card_bottom, 8, fill=1, stroke=1)
        if hero_image is not None:
            _draw_hero(c, hero_image, M + 4 * mm, card_bottom + 4 * mm,
                       W - 2 * M - 8 * mm, card_top - card_bottom - 8 * mm)
        else:
            ctext(W / 2, (card_top + card_bottom) / 2, s("sheet_draw"), f.display, 14, theme.teal)
        footer_ribbon()
        c.showPage()
        c.save()
        return out_path

    # young + older
    # identity row: hero card (left) + identity fields and energy pill (right)
    row_h = 55 * mm
    card_w = 62 * mm
    cap_h = 11 * mm
    c.setFillColor(tint(theme.teal, 0.9))
    c.setStrokeColor(theme.teal)
    c.setLineWidth(1.4)
    c.roundRect(M, y - row_h, card_w, row_h, 7, fill=1, stroke=1)
    if hero_image is not None:
        _draw_hero(c, hero_image, M + 2.5 * mm, y - row_h + cap_h,
                   card_w - 5 * mm, row_h - cap_h - 3 * mm)
    else:
        c.setDash(3, 3)
        c.setStrokeColor(theme.teal)
        c.setLineWidth(1.0)
        c.roundRect(M + 3 * mm, y - row_h + cap_h + 1 * mm, card_w - 6 * mm,
                    row_h - cap_h - 4 * mm, 5, fill=0, stroke=1)
        c.setDash()
    if example:
        ctext(M + card_w / 2, y - row_h + cap_h - 6.5 * mm, example.get("name", ""),
              f.display, 13, theme.teal)
        ctext(M + card_w / 2, y - row_h + 3 * mm, example.get("hero_of", ""), f.body, 7, muted)
    else:
        ctext(M + card_w / 2, y - row_h + cap_h - 6 * mm, s("sheet_draw"), f.body_bold, 8.5, theme.teal)

    ix = M + card_w + 8 * mm
    iw = W - M - ix
    text(ix, y - 5 * mm, s("sheet_name").upper(), f.body_bold, 7.5, muted)
    wline(ix, y - 12 * mm, iw)
    if example:
        text(ix + 1 * mm, y - 11 * mm, example.get("name", ""), f.hand, 13, theme.text)
    text(ix, y - 20 * mm, s("sheet_hero_type").upper(), f.body_bold, 7.5, muted)
    wline(ix, y - 27 * mm, iw)
    if example:
        text(ix + 1 * mm, y - 26 * mm, example.get("hero_of", ""), f.hand, 12, theme.text)
    # energy pill at the bottom of the identity column: label, empty stars, hint
    pill_h = 20 * mm
    pbot = y - row_h
    c.setFillColor(tint(theme.gold, 0.86))
    c.setStrokeColor(theme.gold)
    c.setLineWidth(1.1)
    c.roundRect(ix, pbot, iw, pill_h, 6, fill=1, stroke=1)
    text(ix + 4 * mm, pbot + pill_h - 5 * mm, s("sheet_energy"), f.display, 9, theme.primary)
    for i in range(5):
        _star(c, ix + 8 * mm + i * 10 * mm, pbot + 9 * mm, 3 * mm, theme.gold)
    text(ix + 4 * mm, pbot + 3 * mm, s("sheet_energy_hint"), f.body, 6.3, muted)
    y -= row_h + 7 * mm

    # magics: chip + three rows (draw-square, "magic is" + name, "it can" + wrapped desc)
    magic_hue = theme.purple
    mh, mbody = 8 * mm, 60 * mm
    by = chip(M, y, W - 2 * M, s("sheet_magics"), magic_hue, mbody, header_h=mh)
    inner_top = y - mh
    magics = example.get("magics", []) if example else []
    row_h_m = mbody / 3
    sq = 13 * mm
    for i in range(3):
        rtop = inner_top - i * row_h_m
        rcy = rtop - row_h_m / 2
        sx = M + 4 * mm
        c.setDash(2.5, 2.5)
        c.setStrokeColor(tint(magic_hue, 0.3))
        c.setLineWidth(1.0)
        c.roundRect(sx, rcy - sq / 2, sq, sq, 3, fill=0, stroke=1)
        c.setDash()
        c.setFillColor(tint(magic_hue, 0.4))
        c.setFont(f.body, 6)
        c.drawCentredString(sx + sq / 2, rcy - 1 * mm, s("sheet_magic_symbol"))
        tx = sx + sq + 5 * mm
        tw = W - M - 6 * mm - tx
        text(tx, rtop - 6 * mm, s("sheet_magic_is"), f.body, 8, muted)
        lblw = c.stringWidth(s("sheet_magic_is"), f.body, 8)
        if i < len(magics):
            text(tx + lblw + 4.5 * mm, rtop - 6.3 * mm, magics[i][0], f.display, 12, magic_hue)
        else:
            wline(tx + lblw + 4 * mm, rtop - 7 * mm, tw - lblw - 4 * mm)
        text(tx, rtop - 12.5 * mm, s("sheet_magic_does"), f.body, 8, muted)
        dlw = c.stringWidth(s("sheet_magic_does"), f.body, 8)
        if i < len(magics):
            wrapped(tx + dlw + 3 * mm, rtop - 12.5 * mm, magics[i][1], f.hand, 10,
                    tw - dlw - 3 * mm, 4.7 * mm, theme.text)
        else:
            wline(tx + dlw + 3 * mm, rtop - 13.5 * mm, tw - dlw - 3 * mm)
        if i < 2:
            c.setDash(0.8, 3)
            c.setStrokeColor(tint(magic_hue, 0.45))
            c.setLineWidth(0.7)
            c.line(M + 4 * mm, rtop - row_h_m, W - M - 4 * mm, rtop - row_h_m)
            c.setDash()
    y = by - 7 * mm

    # what I carry: chip + 2 by 3 grid of ring-bullet writing lines
    carry_hue = theme.gold
    cbody = 28 * mm
    by = chip(M, y, W - 2 * M, s("sheet_inventory"), carry_hue, cbody, header_h=mh)
    inner_top = y - mh
    carry = example.get("carry", []) if example else []
    colw = (W - 2 * M - 8 * mm) / 2
    for r in range(3):
        for col in range(2):
            cx2 = M + 5 * mm + col * colw
            cy2 = inner_top - 6.5 * mm - r * 7.5 * mm
            c.setDash()
            c.setStrokeColor(tint(carry_hue, 0.2))
            c.setLineWidth(1.0)
            c.circle(cx2 + 1.4 * mm, cy2 + 0.9 * mm, 1.4 * mm, fill=0, stroke=1)
            wline(cx2 + 4 * mm, cy2, colw - 12 * mm)
            idx = r * 2 + col
            if idx < len(carry):
                text(cx2 + 5 * mm, cy2 + 1 * mm, carry[idx], f.hand, 10, theme.text)
    y = by - 7 * mm

    if tier == "older":
        note_hue = theme.blue
        nbody = 16 * mm
        by = chip(M, y, W - 2 * M, s("sheet_notes"), note_hue, nbody, header_h=mh)
        inner_top = y - mh
        for k in range(2):
            wline(M + 5 * mm, inner_top - 6 * mm - k * 7 * mm, W - 2 * M - 10 * mm)

    footer_ribbon()
    c.showPage()
    c.save()
    return out_path


def _draw_hero(c, path: Path, x: float, y: float, w: float, h: float) -> None:
    """Draw the hero image to fit inside the box, preserving aspect, centred.

    The art is recompressed to a small print-sized JPEG first, so a sheet of four
    heroes does not embed four multi-megabyte source PNGs (which made the
    example-heroes PDFs tens of megabytes)."""
    try:
        c.drawImage(
            images.image_reader(path), x, y, width=w, height=h,
            preserveAspectRatio=True, anchor="c",
        )
    except Exception:
        pass
