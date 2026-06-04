"""Render flowables, and whole markdown files, into themed PDFs.

The font is resolved per (world, locale) so each page is drawn in the world's
typeface, honouring any per-locale override.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer

from build.models import World
from build.render import colophon, flowables, fonts, footer, images, theme
from build.render import markdown as md
from build.render import strings
from build.render.version import VersionInfo


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


def render_story_narration(
    src: Path, out_path: Path, world: World, locale: str, scene_items: list
) -> Path:
    """Render the narration with each scene illustration placed inline at its beat.

    The narration's level-2 headings are its beats (the opening, each Stop, the
    ending). Scene images, in story order, fill the LAST ``len(scene_items)`` beats,
    so the opening beat pairs with the front-page cover and every later beat gets its
    own picture in place rather than in a separate gallery at the back. Any extra
    pictures (more images than beats) follow at the end so none are lost.
    """
    faces = fonts.resolve_faces(world, locale)
    th = theme.Theme.from_world(world)
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))

    preamble: list = []
    sections: list[list] = []
    for block in blocks:
        if isinstance(block, md.Heading) and block.level == 2:
            sections.append([block])
        elif sections:
            sections[-1].append(block)
        else:
            preamble.append(block)

    scene_paths = [path for path, _caption in scene_items]
    start = max(0, len(sections) - len(scene_paths))
    image_at: dict = {}
    leftover: list = []
    for offset, path in enumerate(scene_paths):
        index = start + offset
        if index < len(sections):
            image_at[index] = path
        else:
            leftover.append(path)

    flows = flowables.blocks_to_flowables(preamble, styles, th)
    for i, section in enumerate(sections):
        heading_flows = flowables.blocks_to_flowables(section[:1], styles, th)
        body_flows = flowables.blocks_to_flowables(section[1:], styles, th)
        if i in image_at:
            # keep the picture directly under its beat heading so it never drifts
            # onto the next page above the following heading.
            flows.append(
                KeepTogether(
                    [*heading_flows, Spacer(1, 8), images.scene_flowable(image_at[i])]
                )
            )
        else:
            flows.extend(heading_flows)
        flows.extend(body_flows)
    for path in leftover:
        flows.append(Spacer(1, 10))
        flows.append(images.scene_flowable(path))
    return render_flowables(flows, out_path, world)


def render_guide(
    src: Path,
    out_path: Path,
    locale: str = "en-GB",
    *,
    version: VersionInfo | None = None,
    qr_url: str = colophon.PROJECT_URL,
) -> Path:
    """Render the world-agnostic Guide for the Grown-Up to a themed PDF.

    The guide is shared across worlds, so it uses the default theme and family
    (DejaVu covers en-GB and es-ES). It ends with the colophon page and is stamped
    with the per-page footer and PDF metadata.
    """
    version = version or VersionInfo(0, "unreleased")
    faces = fonts.resolve_faces(None, locale)
    th = theme.Theme.default()
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    label = strings.ui(locale, "colophon_artifact_guide")
    flows.append(PageBreak())
    flows.extend(colophon.colophon_flowables(styles, locale, version, label, qr_url))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = _doc(out_path, landscape_page=False)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label}", locale=locale,
        version_info=version,
    )
    footer.set_metadata(
        out_path, title=f"{label}, {locale}, {version.label}",
        subject=f"Guide for the Grown-Up, {version.label}, {version.updated}",
        keywords=f"wits-and-wonder, guide, {locale}",
    )
    return out_path
