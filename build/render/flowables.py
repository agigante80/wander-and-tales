"""Turn markdown blocks into reportlab flowables using the themed styles.

Table fonts are taken from the style dict (body and a bold heading style), so a
world's typeface flows through tables as well as prose.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from build.render import markdown as md
from build.render.theme import Theme

CONTENT_WIDTH = 210 * mm - 36 * mm  # A4 width minus the page margins
_BULLET = "•"


def _table_style(theme: Theme, body_font: str, head_font: str) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), theme.primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), head_font),
            ("FONTNAME", (0, 1), (-1, -1), body_font),
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
    body_font = styles["body"].fontName
    head_font = styles["h2"].fontName
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
            table.setStyle(_table_style(theme, body_font, head_font))
            flows.append(Spacer(1, 4))
            flows.append(table)
            flows.append(Spacer(1, 6))
    return flows
