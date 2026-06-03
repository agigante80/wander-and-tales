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
PAGE_FILL = white  # printable page background: white prints cleanly and cheaply


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
        canvas.setFillColor(PAGE_FILL)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(theme.border)
        canvas.setLineWidth(3)
        canvas.setDash(2, 10)
        canvas.roundRect(8 * mm, 8 * mm, width - 16 * mm, height - 16 * mm, 10,
                         fill=0, stroke=1)
        canvas.restoreState()

    return paint
