"""The one-page "How to Play" quick start: a schematic sheet that explains the game and
the files at a glance, for a grown-up who has never played a game like this.

Plain words, fun first. It shows what you do (a turn in four steps), what to print, what
you need, the one rule (nobody loses), and a "Did you know?" aside that keeps the child
note out of the way of the play. Canvas-drawn and palette-driven like the character
sheet, world-agnostic (it uses the default brand theme), localised through strings.py.
It is emitted on its own and also prepended as the first page of the Guide.
"""

from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render import chrome, fonts, strings
from build.render.theme import Theme, PAGE_FILL, tint

W, H = A4
M = 14 * mm


def render_quickstart(out_path: Path, locale: str, theme: Theme) -> Path:
    """Render the one-page How to Play sheet (no footer; the caller stamps it)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=A4)
    f = fonts.sheet_faces()

    def s(key: str) -> str:
        return strings.ui(locale, key)

    def wrap(text: str, font: str, size: float, maxw: float) -> list[str]:
        return chrome._wrap(text, font, size, maxw)

    def panel(x: float, top: float, w: float, h: float, hue, title: str,
              header_h: float = 8 * mm) -> float:
        """A white box with a hue keyline and a hue title tab. Returns the inner top."""
        c.setDash()
        c.setFillColor(white)
        c.setStrokeColor(hue)
        c.setLineWidth(1.0)
        c.roundRect(x, top - h, w, h, 6, fill=1, stroke=1)
        c.setFillColor(hue)
        c.roundRect(x, top - header_h, w, header_h, 6, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(f.display, 10.5)
        c.drawString(x + 4 * mm, top - header_h + 2.4 * mm, title)
        return top - header_h

    c.setFillColor(PAGE_FILL)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    band_h = chrome.draw_header_band(
        c, M, H - M, W - 2 * M, s("colophon_project"), s("quickstart_title"), theme,
        title_size=20, motif=True,
    )
    y = H - M - band_h - 5 * mm
    c.setFillColor(tint(theme.text, 0.2))
    c.setFont(f.hand, 13)
    c.drawCentredString(W / 2, y, s("tagline"))
    y -= 7 * mm

    # The hook: what you do, the goal, the fun, in one friendly line.
    hook_lines = wrap(s("quickstart_hook"), f.display, 15, W - 2 * M - 14 * mm)
    hook_h = 8 * mm + len(hook_lines) * 8 * mm + 4 * mm
    c.setDash()
    c.setFillColor(tint(theme.primary, 0.86))
    c.setStrokeColor(tint(theme.primary, 0.58))
    c.setLineWidth(1.0)
    c.roundRect(M, y - hook_h, W - 2 * M, hook_h, 7, fill=1, stroke=1)
    c.setFillColor(theme.primary)
    c.setFont(f.display, 15)
    ly = y - 10 * mm
    for ln in hook_lines:
        c.drawCentredString(W / 2, ly, ln)
        ly -= 8 * mm
    y = y - hook_h - 7 * mm

    # A turn in four steps, with a handwritten loop note.
    steps = [s("quickstart_step1"), s("quickstart_step2"),
             s("quickstart_step3"), s("quickstart_step4")]
    turn_h = 8 * mm + len(steps) * 11 * mm + 11 * mm
    inner = panel(M, y, W - 2 * M, turn_h, theme.blue, s("quickstart_turn_title"))
    sy = inner - 9 * mm
    for i, st in enumerate(steps):
        cxn = M + 9 * mm
        c.setFillColor(theme.blue)
        c.circle(cxn, sy, 4.2 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(f.display, 12)
        c.drawCentredString(cxn, sy - 1.7 * mm, str(i + 1))
        c.setFillColor(theme.text)
        c.setFont(f.body, 11)
        c.drawString(cxn + 9 * mm, sy - 1.6 * mm, st)
        sy -= 11 * mm
    c.setFillColor(tint(theme.text, 0.25))
    c.setFont(f.hand, 12)
    c.drawString(M + 9 * mm, sy + 1.5 * mm, s("quickstart_loop_note"))
    y = y - turn_h - 7 * mm

    # Two columns: what to print, what you need.
    col_w = (W - 2 * M - 6 * mm) / 2
    cols_h = 8 * mm + 45 * mm
    inner = panel(M, y, col_w, cols_h, theme.gold, s("quickstart_print_title"))
    py = inner - 7 * mm
    files = [
        (s("quickstart_file_pack_name"), s("quickstart_file_pack_note")),
        (s("quickstart_file_playbook_name"), s("quickstart_file_playbook_note")),
    ]
    for name, note in files:
        chrome.star(c, M + 5.5 * mm, py - 1 * mm, 1.7 * mm, theme.gold, theme.gold)
        c.setFillColor(theme.text)
        c.setFont(f.body_bold, 9.5)
        c.drawString(M + 10 * mm, py - 2 * mm, name)
        py -= 5 * mm
        c.setFillColor(tint(theme.text, 0.25))
        c.setFont(f.body, 8.5)
        c.drawString(M + 10 * mm, py - 2 * mm, note)
        py -= 7 * mm
    c.setFillColor(tint(theme.text, 0.4))
    c.setFont(f.body, 8)
    for ln in wrap(s("quickstart_file_extra"), f.body, 8, col_w - 12 * mm):
        c.drawString(M + 10 * mm, py - 2 * mm, ln)
        py -= 4.6 * mm

    rx = M + col_w + 6 * mm
    inner = panel(rx, y, col_w, cols_h, theme.teal, s("quickstart_need_title"))
    ny = inner - 10 * mm
    for item in (s("quickstart_need_die"), s("quickstart_need_pencils"),
                 s("quickstart_need_tokens")):
        c.setFillColor(theme.teal)
        c.circle(rx + 6 * mm, ny - 1.2 * mm, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(theme.text)
        c.setFont(f.body, 10.5)
        c.drawString(rx + 10 * mm, ny - 2 * mm, item)
        ny -= 9 * mm
    y = y - cols_h - 7 * mm

    # The one rule, as a banner.
    rule_lines = wrap(s("quickstart_rule_body"), f.body, 11, W - 2 * M - 28 * mm)
    rule_h = 8 * mm + len(rule_lines) * 5.4 * mm + 3 * mm
    c.setDash()
    c.setFillColor(tint(theme.gold, 0.85))
    c.setStrokeColor(tint(theme.gold, 0.5))
    c.setLineWidth(1.0)
    c.roundRect(M, y - rule_h, W - 2 * M, rule_h, 6, fill=1, stroke=1)
    chrome.star(c, M + 9 * mm, y - rule_h / 2, 2.4 * mm, theme.gold, theme.gold)
    chrome.star(c, W - M - 9 * mm, y - rule_h / 2, 2.4 * mm, theme.gold, theme.gold)
    c.setFillColor(theme.primary)
    c.setFont(f.display, 12)
    c.drawCentredString(W / 2, y - 7.5 * mm, s("quickstart_rule_title"))
    c.setFillColor(theme.text)
    c.setFont(f.body, 11)
    ly = y - 13 * mm
    for ln in rule_lines:
        c.drawCentredString(W / 2, ly, ln)
        ly -= 5.4 * mm
    y = y - rule_h - 7 * mm

    # Did you know? The development note, kept as an opt-in curiosity.
    dyk_lines = wrap(s("quickstart_didyouknow_body"), f.body, 9.5, W - 2 * M - 18 * mm)
    dyk_h = 10 * mm + len(dyk_lines) * 5 * mm + 3 * mm
    c.setDash()
    c.setFillColor(tint(theme.purple, 0.9))
    c.setStrokeColor(tint(theme.purple, 0.7))
    c.setLineWidth(0.9)
    c.roundRect(M, y - dyk_h, W - 2 * M, dyk_h, 6, fill=1, stroke=1)
    c.setFillColor(theme.purple)
    c.roundRect(M, y - dyk_h, 1.6 * mm, dyk_h, 0, fill=1, stroke=0)
    chrome.star(c, M + 9 * mm, y - 6.5 * mm, 2.1 * mm, theme.purple, theme.purple)
    c.setFillColor(theme.purple)
    c.setFont(f.display, 11)
    c.drawString(M + 14 * mm, y - 8 * mm, s("quickstart_didyouknow_title"))
    c.setFillColor(tint(theme.text, 0.1))
    c.setFont(f.body, 9.5)
    ly = y - 14 * mm
    for ln in dyk_lines:
        c.drawString(M + 9 * mm, ly, ln)
        ly -= 5 * mm

    c.showPage()
    c.save()
    return out_path
