"""Shared, palette-driven page chrome: header bands, beat chips, prompt callouts,
and rounded illustrations, so the whole kit speaks one visual vocabulary.

Everything here is print-cheap (flat fills, light tints via theme.tint, rounded
rects, dotted rules, simple shapes) and world-agnostic: every colour comes from the
world Theme, so all six worlds keep their own palette. Canvas-draw helpers are reused
by the canvas-drawn character sheet; the Flowable classes are used by the
flowable-based booklets (front pages, narration, world book, guide).
"""

import math
import re

from reportlab.lib.colors import white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable

from build.render import fonts, images
from build.render.theme import tint

CONTENT_WIDTH = images.CONTENT_WIDTH


def star(c, cx: float, cy: float, r: float, stroke, fill=None) -> None:
    """A small five-pointed star outline (filled when `fill` is given)."""
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
    c.setFillColor(fill or white)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.0)
    c.drawPath(p, fill=1, stroke=1)


def _wrap(text: str, font: str, size: float, max_w: float) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or pdfmetrics.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out or [""]


def _motif(c, cx: float, cy: float, theme) -> None:
    """A small world-neutral flourish: a soft dotted arc with a few stars over it."""
    c.saveState()
    c.setStrokeColor(tint(theme.teal, 0.25))
    c.setLineWidth(1.6)
    c.setDash(1.2, 2.2)
    p = c.beginPath()
    p.moveTo(cx - 9 * mm, cy - 1 * mm)
    p.curveTo(cx - 3 * mm, cy + 4.5 * mm, cx + 3 * mm, cy + 4.5 * mm, cx + 9 * mm, cy - 1 * mm)
    c.drawPath(p, stroke=1, fill=0)
    c.setDash()
    star(c, cx - 4 * mm, cy + 4 * mm, 1.5 * mm, theme.gold, theme.gold)
    star(c, cx + 2 * mm, cy + 6 * mm, 2.0 * mm, theme.gold, theme.gold)
    star(c, cx + 7 * mm, cy + 3.5 * mm, 1.4 * mm, theme.gold, tint(theme.gold, 0.35))
    c.restoreState()


def _band_height(title: str, title_size: float, max_w: float) -> float:
    f = fonts.sheet_faces()
    lines = _wrap(title, f.display, title_size, max_w)
    return 9 * mm + len(lines) * (title_size * 1.18) + 4.5 * mm


def draw_header_band(
    c, x: float, y_top: float, w: float, kicker: str, title: str, theme,
    *, title_size: float = 18, motif: bool = True,
) -> float:
    """Draw a rounded header band (kicker + title + motif) from y_top downward, in a
    light tint of the world primary. Returns the band height drawn (no rule)."""
    f = fonts.sheet_faces()
    motif_w = 26 * mm if motif else 0
    max_w = w - 12 * mm - motif_w
    lines = _wrap(title, f.display, title_size, max_w)
    band_h = 9 * mm + len(lines) * (title_size * 1.18) + 4.5 * mm
    c.saveState()
    c.setDash()
    c.setFillColor(tint(theme.primary, 0.88))
    c.setStrokeColor(tint(theme.primary, 0.62))
    c.setLineWidth(1.0)
    c.roundRect(x, y_top - band_h, w, band_h, 7, fill=1, stroke=1)
    if kicker:
        c.setFillColor(theme.teal)
        c.setFont(f.body_bold, 7)
        c.drawString(x + 5 * mm, y_top - 7 * mm, kicker.upper())
    ly = y_top - 7 * mm - title_size * 0.92
    c.setFillColor(theme.primary)
    c.setFont(f.display, title_size)
    for ln in lines:
        c.drawString(x + 5 * mm, ly, ln)
        ly -= title_size * 1.18
    if motif:
        _motif(c, x + w - 13 * mm, y_top - band_h / 2, theme)
    c.restoreState()
    return band_h


class HeaderBand(Flowable):
    """The header band as a flowable: the band, then a dotted accent rule below."""

    def __init__(self, kicker: str, title: str, theme, *, width=CONTENT_WIDTH,
                 title_size: float = 22, motif: bool = True):
        super().__init__()
        self.kicker, self.title, self.theme = kicker, title, theme
        self.width = width
        self.title_size = title_size
        self.motif = motif
        max_w = width - 12 * mm - (26 * mm if motif else 0)
        self.band_h = _band_height(title, title_size, max_w)
        self.height = self.band_h + 7 * mm

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        draw_header_band(c, 0, self.height, self.width, self.kicker, self.title,
                         self.theme, title_size=self.title_size, motif=self.motif)
        c.setStrokeColor(self.theme.gold)
        c.setLineWidth(2.2)
        c.setDash(1.3, 4.5)
        c.line(0, 3.5 * mm, self.width, 3.5 * mm)
        c.setDash()


_BEAT_RE = re.compile(r"^(.+?\s*\d+)\s*[:.]\s*(.+)$")


def _parse_beat(label: str):
    m = _BEAT_RE.match(label.strip())
    if m and any(ch.isdigit() for ch in m.group(1)):
        return m.group(1).strip(), m.group(2).strip()
    return None, label.strip()


class BeatChip(Flowable):
    """A beat heading as a filled rounded pill (an optional number tag + the title)."""

    def __init__(self, label: str, theme, *, width=CONTENT_WIDTH):
        super().__init__()
        self.number, self.title = _parse_beat(label)
        self.theme = theme
        self.width = width
        self.height = 8 * mm + 8 * mm  # pill + a little air above so it reads fresh

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        f = fonts.sheet_faces()
        pill_h = 8 * mm
        pad = 3.5 * mm
        ntw = (pdfmetrics.stringWidth(self.number, f.display, 9) + 5 * mm) if self.number else 0
        title_w = pdfmetrics.stringWidth(self.title, f.display, 11)
        pill_w = pad + ntw + (3 * mm if self.number else 0) + title_w + pad
        c.setFillColor(self.theme.primary)
        c.roundRect(0, 0, pill_w, pill_h, pill_h / 2, fill=1, stroke=0)
        tx = pad
        if self.number:
            c.setFillColor(tint(self.theme.primary, 0.28))
            c.roundRect(tx, 1.4 * mm, ntw, pill_h - 2.8 * mm, 2.5, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(f.display, 9)
            c.drawCentredString(tx + ntw / 2, pill_h / 2 - 1.1 * mm, self.number)
            tx += ntw + 3 * mm
        c.setFillColor(white)
        c.setFont(f.display, 11)
        c.drawString(tx, pill_h / 2 - 1.4 * mm, self.title)


class PromptCallout(Flowable):
    """A read-aloud / kind-question aside: a soft tinted box with a coloured left
    border and a star bullet, the italic text wrapped to the right."""

    def __init__(self, text: str, theme, body_italic: str, *, width=CONTENT_WIDTH,
                 size: float = 10.5):
        super().__init__()
        self.text = text.strip().strip("*").strip()
        self.theme = theme
        self.font = body_italic
        self.size = size
        self.width = width
        self.pad = 4 * mm
        self.bullet_col = 11 * mm
        self.leading = size * 1.32
        self.lines = _wrap(self.text, self.font, size, width - self.bullet_col - self.pad)
        self.box_h = self.pad + len(self.lines) * self.leading + self.pad - 1 * mm
        self.height = self.box_h + 4 * mm

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        top = self.box_h
        c.setDash()
        c.setFillColor(tint(self.theme.purple, 0.9))
        c.setStrokeColor(tint(self.theme.purple, 0.78))
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.width, self.box_h, 5, fill=1, stroke=1)
        c.setFillColor(self.theme.purple)
        c.roundRect(0, 0, 1.4 * mm, self.box_h, 0, fill=1, stroke=0)
        cy = self.box_h - 5.5 * mm
        c.circle(self.bullet_col / 2 + 1 * mm, cy, 2.6 * mm, fill=1, stroke=0)
        star(c, self.bullet_col / 2 + 1 * mm, cy, 1.7 * mm, white, white)
        c.setFillColor(tint(self.theme.text, 0.1))
        c.setFont(self.font, self.size)
        ty = top - self.pad - self.size
        for ln in self.lines:
            c.drawString(self.bullet_col, ty, ln)
            ty -= self.leading


class RoundedImage(Flowable):
    """An illustration with rounded corners (whitened in the JPEG) and a thin keyline,
    plus an optional italic caption beneath it."""

    def __init__(self, path, theme, *, max_w=CONTENT_WIDTH, max_h=115 * mm,
                 caption="", caption_font=None):
        super().__init__()
        self.theme = theme
        self.reader, iw, ih = images.rounded_reader(path)
        scale = min(max_w / iw, max_h / ih)
        self.iw, self.ih = iw * scale, ih * scale
        self.caption = caption
        self.caption_font = caption_font
        self.cap_h = 6 * mm if caption else 0
        self.width = max_w
        self.height = self.ih + self.cap_h

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        x = (self.width - self.iw) / 2
        y = self.cap_h
        c.drawImage(self.reader, x, y, width=self.iw, height=self.ih, mask="auto")
        c.setStrokeColor(tint(self.theme.primary, 0.6))
        c.setLineWidth(1.4)
        c.setDash()
        c.roundRect(x, y, self.iw, self.ih, 9, fill=0, stroke=1)
        if self.caption and self.caption_font:
            c.setFillColor(tint(self.theme.text, 0.3))
            c.setFont(self.caption_font, 9)
            c.drawCentredString(self.width / 2, 1 * mm, self.caption)
