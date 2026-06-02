"""Render flowables, and whole markdown files, into themed PDFs.

The font is resolved per (world, locale) so each page is drawn in the world's
typeface, honouring any per-locale override.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from build.models import World
from build.render import flowables, fonts, theme
from build.render import markdown as md


def _doc(out_path: Path, *, landscape_page: bool) -> SimpleDocTemplate:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return SimpleDocTemplate(
        str(out_path), pagesize=landscape(A4) if landscape_page else A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )


def render_flowables(
    flows: list, out_path: Path, world: World, *, landscape_page: bool = False
) -> Path:
    """Build a themed PDF from ready-made flowables (already styled)."""
    th = theme.Theme.from_world(world)
    doc = _doc(out_path, landscape_page=landscape_page)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path


def render_markdown_file(src: Path, out_path: Path, world: World, locale: str) -> Path:
    """Parse a markdown content file and render it in the world+locale typeface."""
    faces = fonts.resolve_faces(world, locale)
    th = theme.Theme.from_world(world)
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    return render_flowables(flows, out_path, world)


def render_guide(src: Path, out_path: Path, locale: str = "en-GB") -> Path:
    """Render the world-agnostic Guide for the Grown-Up to a themed PDF.

    The guide is shared across worlds, so it uses the default theme and the
    default family (DejaVu covers en-GB and es-ES today). Per-locale guide
    typography is deferred until a locale needs a different script.
    """
    faces = fonts.resolve_faces(None, locale)
    th = theme.Theme.default()
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = _doc(out_path, landscape_page=False)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    return out_path
