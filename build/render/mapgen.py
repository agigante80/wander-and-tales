"""Generate a simple per-story adventure-trail map from the narration beats.

Every Atlas carries a map page. When a story (or its world) ships a hand-drawn
map SVG, that wins (see ``map.find_map``); otherwise this module draws one. It reads
the story's own narration headings (``## Before you begin``, ``## Stop 1: ...``, the
ending) and lays out a winding golden trail from START, through the numbered stops, to
the ending place. It is canvas-drawn like the character sheet, so it shares the kit's
type and palette, needs no art, and scales to every story and language for free: the
labels come straight from the locale's headings, so one generator serves all three.
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import chrome, fonts, strings
from build.render.theme import Theme, PAGE_FILL, tint

W, H = A4
M = 16 * mm  # page margin

_H2 = re.compile(r"^##\s+(.+?)\s*$")
_DIGITS = re.compile(r"\d+")


@dataclass(frozen=True)
class Node:
    kind: str  # "start" | "stop" | "finish"
    tag: str   # the marker word or number (START, 1, GOAL)
    label: str  # the place name drawn beside the marker (may be empty)


def _headings(narration_path: Path) -> list[str]:
    """Every level-2 heading in the narration, in order (the story's beats)."""
    if not narration_path.is_file():
        return []
    out = []
    for line in narration_path.read_text(encoding="utf-8").splitlines():
        match = _H2.match(line)
        if match:
            out.append(match.group(1).strip())
    return out


def trail_nodes(narration_path: Path, locale: str) -> list[Node]:
    """A START, one node per numbered stop, and a GOAL, read from the narration.

    The numbered ``## Stop N: Name`` headings become the waypoints; the last
    non-numbered heading (the ending) names the goal. A narration with no stops still
    yields START and GOAL, so the page is always valid.
    """
    headings = _headings(narration_path)
    stops: list[Node] = []
    non_numbered: list[str] = []
    for heading in headings:
        number, title = chrome._parse_beat(heading)
        if number is None:
            non_numbered.append(title)
            continue
        digits = _DIGITS.search(number)
        stops.append(Node("stop", digits.group(0) if digits else str(len(stops) + 1), title))
    # The first non-numbered heading is the "before you begin" intro (the START itself);
    # the last is the ending that names the goal. With only one, the goal stays generic.
    finish_label = non_numbered[-1] if len(non_numbered) >= 2 else ""
    start = Node("start", strings.ui(locale, "map_start"), "")
    finish = Node("finish", strings.ui(locale, "map_goal"), finish_label)
    return [start, *stops, finish]


def _scenery(c, top: float, bottom: float, theme: Theme) -> None:
    """Soft, very light land shapes and a few stars behind the trail (low ink)."""
    band = top - bottom
    blobs = (
        (W * 0.30, bottom + band * 0.74, 52 * mm, 30 * mm, tint(theme.teal, 0.88)),
        (W * 0.72, bottom + band * 0.50, 56 * mm, 34 * mm, tint(theme.gold, 0.90)),
        (W * 0.32, bottom + band * 0.24, 50 * mm, 30 * mm, tint(theme.blue, 0.90)),
    )
    c.setDash()
    for cx, cy, rw, rh, col in blobs:
        c.setFillColor(col)
        c.roundRect(cx - rw / 2, cy - rh / 2, rw, rh, min(rw, rh) / 2, fill=1, stroke=0)
    for sx, sy in ((0.18, 0.86), (0.84, 0.80), (0.20, 0.40), (0.80, 0.30), (0.50, 0.62)):
        chrome.star(c, W * sx, bottom + band * sy, 1.3 * mm,
                    tint(theme.gold, 0.5), tint(theme.gold, 0.5))


def _compass(c, cx: float, cy: float, theme: Theme) -> None:
    """A small compass rose, for map flavour, drawn in light palette colours."""
    r = 7 * mm
    c.setDash()
    c.setFillColor(white)
    c.setStrokeColor(tint(theme.border, 0.2))
    c.setLineWidth(0.8)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setStrokeColor(tint(theme.text, 0.4))
    c.setLineWidth(0.7)
    for ang in (0, 90, 180, 270):
        a = math.radians(ang)
        c.line(cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5,
               cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85)
    p = c.beginPath()
    p.moveTo(cx, cy + r * 0.7)
    p.lineTo(cx - r * 0.22, cy)
    p.lineTo(cx + r * 0.22, cy)
    p.close()
    c.setFillColor(theme.rose)
    c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(theme.text)
    c.setFont(fonts.sheet_faces().body_bold, 6)
    c.drawCentredString(cx, cy + r + 1.2 * mm, "N")


def _trail(c, points: list[tuple[float, float]], theme: Theme) -> None:
    """A thick dotted golden path winding through the waypoint centres."""
    if len(points) < 2:
        return
    c.setStrokeColor(theme.gold)
    c.setLineWidth(2.6)
    c.setDash(1.4, 3.6)
    path = c.beginPath()
    path.moveTo(*points[0])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        midy = (y0 + y1) / 2
        path.curveTo(x0, midy, x1, midy, x1, y1)
    c.drawPath(path, stroke=1, fill=0)
    c.setDash()


def _label_outside(c, node: Node, x: float, y: float, side: int, theme: Theme,
                   *, r: float, title_size: float) -> None:
    """Draw a node's label on its outer side (for the vertical trail), wrapped to two
    lines. `side` is -1 (label to the left) or +1 (to the right)."""
    f = fonts.sheet_faces()
    gap = r + 3 * mm
    draw = c.drawRightString if side < 0 else c.drawString
    tx = x - gap if side < 0 else x + gap
    max_w = (tx - M) if side < 0 else (W - M - tx)
    if node.kind == "start":
        c.setFillColor(theme.teal)
        c.setFont(f.body_bold, 8.5)
        draw(tx, y - 1 * mm, node.tag)
        return
    title = node.label or node.tag
    colour = theme.primary if node.kind == "finish" else theme.text
    lh = title_size * 1.32
    lines = chrome._wrap(title, f.display, title_size, max(max_w, 24 * mm))[:2]
    ty = y + (len(lines) - 1) * lh / 2 + 0.4 * mm
    if node.kind == "finish":
        c.setFillColor(theme.gold)
        c.setFont(f.body_bold, 7)
        draw(tx, ty + lh * 0.95, node.tag.upper())
    c.setFillColor(colour)
    c.setFont(f.display, title_size)
    for line in lines:
        draw(tx, ty, line)
        ty -= lh


def _label_below(c, node: Node, x: float, y: float, theme: Theme,
                 *, r: float, title_size: float, max_w: float) -> None:
    """Draw a node's label centred below the marker (for the serpentine grid)."""
    f = fonts.sheet_faces()
    top = y - r - title_size * 1.1
    if node.kind == "start":
        c.setFillColor(theme.teal)
        c.setFont(f.body_bold, title_size * 0.82)
        c.drawCentredString(x, top, node.tag)
        return
    title = node.label or node.tag
    colour = theme.primary if node.kind == "finish" else theme.text
    lh = title_size * 1.2
    ty = top
    if node.kind == "finish":
        c.setFillColor(theme.gold)
        c.setFont(f.body_bold, title_size * 0.66)
        c.drawCentredString(x, ty, node.tag.upper())
        ty -= lh
    c.setFillColor(colour)
    c.setFont(f.display, title_size)
    for line in chrome._wrap(title, f.display, title_size, max_w)[:2]:
        c.drawCentredString(x, ty, line)
        ty -= lh


def _marker(c, node: Node, x: float, y: float, idx: int, theme: Theme,
            *, r: float = 6.5 * mm, num_size: float = 13) -> None:
    f = fonts.sheet_faces()
    c.setDash()
    if node.kind == "finish":
        chrome.star(c, x, y, r * 1.3, white, theme.gold)
        return
    if node.kind == "start":
        c.setFillColor(theme.teal)
        c.circle(x, y, r, fill=1, stroke=0)
        chrome.star(c, x, y, r * 0.46, theme.teal, white)
        return
    hue = (theme.primary, theme.rose, theme.blue)[idx % 3]
    c.setFillColor(hue)
    c.circle(x, y, r, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(f.display, num_size)
    c.drawCentredString(x, y - num_size * 0.43, node.tag)


def render_generated_map(
    out_path: Path, locale: str, title: str, narration_path: Path, theme: Theme
) -> Path:
    """Render the one-page A4 adventure-trail map for a story and locale."""
    nodes = trail_nodes(narration_path, locale)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)
    f = fonts.sheet_faces()

    c.setFillColor(PAGE_FILL)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    band_h = chrome.draw_header_band(
        c, M, H - M, W - 2 * M, strings.ui(locale, "map_subtitle"), title, theme,
        title_size=18, motif=True,
    )
    rule_y = H - M - band_h - 3 * mm
    c.setStrokeColor(theme.gold)
    c.setLineWidth(1.4)
    c.setDash(1.3, 4.5)
    c.line(M, rule_y, W - M, rule_y)
    c.setDash()

    area_top = rule_y - 10 * mm
    area_bottom = 34 * mm  # clear of the footer ribbon and the stamped version line
    _scenery(c, area_top, area_bottom, theme)

    n = len(nodes)
    if n <= 7:
        # The common case (up to 5 stops): a winding vertical trail, alternating sides,
        # labels on the outer edge. Shrinks the title a touch as the trail lengthens.
        cx = W / 2
        amp = 20 * mm
        r = 6.5 * mm
        title_size = 11.5 if n <= 5 else (10.5 if n == 6 else 9.5)
        placed: list[tuple[Node, float, float, int]] = []
        for i, node in enumerate(nodes):
            t = i / (n - 1) if n > 1 else 0.0
            y = area_top - t * (area_top - area_bottom)
            side = -1 if i % 2 == 0 else 1
            placed.append((node, cx + side * amp, y, side))
        _trail(c, [(x, y) for _, x, y, _ in placed], theme)
        stop_idx = 0
        for node, x, y, side in placed:
            _marker(c, node, x, y, stop_idx, theme, r=r)
            _label_outside(c, node, x, y, side, theme, r=r, title_size=title_size)
            if node.kind == "stop":
                stop_idx += 1
    else:
        # Long stories (6+ stops): a serpentine grid that uses the page width, labels
        # centred below each marker, so it stays one readable A4 page however long.
        cols = 3 if n <= 9 else 4
        rows = math.ceil(n / cols)
        cell_w = (W - 2 * M) / cols
        cell_h = (area_top - area_bottom) / rows
        r = max(4.2 * mm, min(6.0 * mm, min(cell_w, cell_h) * 0.15))
        title_size = 9 if cols == 3 else 8
        centres: list[tuple[float, float]] = []
        for i in range(n):
            row, col_in_row = divmod(i, cols)
            col = col_in_row if row % 2 == 0 else (cols - 1 - col_in_row)
            centres.append((
                M + (col + 0.5) * cell_w,
                area_top - (row + 0.5) * cell_h,
            ))
        _trail(c, centres, theme)
        stop_idx = 0
        for node, (x, y) in zip(nodes, centres):
            _marker(c, node, x, y, stop_idx, theme, r=r, num_size=11)
            _label_below(c, node, x, y, theme, r=r, title_size=title_size,
                         max_w=cell_w - 4 * mm)
            if node.kind == "stop":
                stop_idx += 1

    _compass(c, M + 11 * mm, area_bottom + 4 * mm, theme)

    rib_y, rib_h = 16 * mm, 9 * mm
    c.setDash()
    c.setFillColor(tint(theme.gold, 0.85))
    c.setStrokeColor(tint(theme.gold, 0.5))
    c.setLineWidth(0.8)
    c.roundRect(M + 6 * mm, rib_y, W - 2 * M - 12 * mm, rib_h, 4, fill=1, stroke=1)
    chrome.star(c, M + 11 * mm, rib_y + rib_h / 2, 1.8 * mm, theme.gold, theme.gold)
    chrome.star(c, W - M - 11 * mm, rib_y + rib_h / 2, 1.8 * mm, theme.gold, theme.gold)
    c.setFillColor(theme.text)
    c.setFont(f.body, 7.2)
    c.drawCentredString(W / 2, rib_y + 3 * mm, strings.ui(locale, "map_trail_hint"))

    c.showPage()
    c.save()
    return out_path
