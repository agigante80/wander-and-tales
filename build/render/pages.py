"""Render flowables, and whole markdown files, into themed PDFs.

The font is resolved per (world, locale) so each page is drawn in the world's
typeface, honouring any per-locale override.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer

from build.models import World
from build.render import chrome, colophon, flowables, fonts, footer, images, theme
from build.render import markdown as md
from build.render import quickstart as quickstart_page
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

    italic = faces.italic

    def is_italic_para(b) -> bool:
        if not isinstance(b, md.Para):
            return False
        t = b.text.strip()
        return t.startswith("*") and not t.startswith("**") and t.endswith("*")

    def body_flows(items) -> list:
        out: list = []
        for b in items:
            if is_italic_para(b):
                # a read-aloud / kind-question aside becomes a prompt callout
                out.append(chrome.PromptCallout(b.text, th, italic))
            else:
                out.extend(flowables.blocks_to_flowables([b], styles, th))
        return out

    flows: list = []
    for block in preamble:
        # the story title is already the header band on the story-pack front page
        if isinstance(block, md.Heading) and block.level == 1:
            continue
        flows.extend(body_flows([block]))

    for i, section in enumerate(sections):
        chip = chrome.BeatChip(section[0].text, th)
        if i in image_at:
            # keep the beat chip and its picture together so the picture never drifts
            # onto the next page above the following beat.
            flows.append(
                KeepTogether(
                    [chip, Spacer(1, 6), chrome.RoundedImage(image_at[i], th, max_h=115 * mm)]
                )
            )
        else:
            flows.append(chip)
        flows.extend(body_flows(section[1:]))
    for path in leftover:
        flows.append(Spacer(1, 8))
        flows.append(chrome.RoundedImage(path, th, max_h=115 * mm))
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
    version = version or VersionInfo(0, 0, "unreleased")
    faces = fonts.resolve_faces(None, locale)
    th = theme.Theme.default()
    styles = theme.make_styles(th, faces)
    label = strings.ui(locale, "colophon_artifact_guide")
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    # the header band carries the title, so drop the markdown's own leading H1
    if blocks and isinstance(blocks[0], md.Heading) and blocks[0].level == 1:
        blocks = blocks[1:]
    flows = [chrome.HeaderBand(kicker="Wander and Tales", title=label, theme=th, motif=False)]
    flows += flowables.blocks_to_flowables(blocks, styles, th)
    flows.append(PageBreak())
    flows.extend(colophon.colophon_flowables(styles, locale, version, label, qr_url))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    paint = theme.page_painter(th)
    # The Guide opens with the one-page How to Play sheet, then the prose. Render each
    # part, then merge so the schema is page one (kept in sync with the standalone sheet).
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        qs = quickstart_page.render_quickstart(tmp_path / "qs.pdf", locale, th)
        prose = tmp_path / "prose.pdf"
        doc = _doc(prose, landscape_page=False)
        doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
        writer = PdfWriter()
        for part in (qs, prose):
            for page in PdfReader(str(part)).pages:
                writer.add_page(page)
        with out_path.open("wb") as handle:
            writer.write(handle)
    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {label}", locale=locale,
        version_info=version,
    )
    footer.set_metadata(
        out_path, title=f"{label}, {locale}, {version.label}",
        subject=f"Guide for the Grown-Up, {version.label}, {version.updated}",
        keywords=f"wander-and-tales, guide, {locale}",
    )
    return out_path


def build_quickstart(
    out_path: Path,
    locale: str = "en-GB",
    *,
    version: VersionInfo | None = None,
) -> Path:
    """Render the standalone one-page How to Play sheet, stamped with footer and
    metadata. Same page that opens the Guide, shareable and printable on its own."""
    version = version or VersionInfo(0, 0, "unreleased")
    th = theme.Theme.default()
    title = strings.ui(locale, "quickstart_title")
    quickstart_page.render_quickstart(out_path, locale, th)
    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {title}", locale=locale,
        version_info=version,
    )
    footer.set_metadata(
        out_path, title=f"{title}, {locale}, {version.label}",
        subject=f"How to Play, {version.label}, {version.updated}",
        keywords=f"wander-and-tales, how-to-play, quick-start, {locale}",
    )
    return out_path
