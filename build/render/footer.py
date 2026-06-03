"""Final passes over a finished, merged PDF: stamp a per-page footer, set metadata.

Each artifact is several sub-PDFs merged with pypdf, so the total page count and a
uniform footer are only knowable on the merged file. The footer is a reportlab
overlay sized to each page, so portrait and landscape pages both get it.
"""

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render.version import VersionInfo

_FOOTER_GREY = HexColor("#8a8a8a")
_FOOTER_FONT = "Helvetica"  # a standard PDF font, no embedding, covers Latin accents
_FOOTER_SIZE = 7


def _overlay_page(width: float, height: float, left: str, right: str):
    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=(width, height))
    c.setFillColor(_FOOTER_GREY)
    c.setFont(_FOOTER_FONT, _FOOTER_SIZE)
    c.drawString(12 * mm, 6 * mm, left)
    c.drawRightString(width - 12 * mm, 6 * mm, right)
    c.showPage()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def stamp_footers(
    pdf_path: Path, *, identity: str, locale: str, version_info: VersionInfo
) -> Path:
    """Draw a discreet footer on every page of the merged PDF, in place."""
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    # Clone into the writer first, then merge overlays onto the writer's own pages:
    # merging onto reader pages not attached to a writer is deprecated in pypdf.
    writer = PdfWriter(clone_from=reader)
    for index, page in enumerate(writer.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        right = f"{locale} · {version_info.label} · page {index} of {total}"
        page.merge_page(_overlay_page(width, height, identity, right))
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    return pdf_path


def set_metadata(
    pdf_path: Path, *, title: str, subject: str, keywords: str,
    author: str = "Wits and Wonder",
) -> Path:
    """Set the PDF document metadata, in place. Separators are commas, never dashes."""
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.add_metadata(
        {"/Title": title, "/Author": author, "/Subject": subject, "/Keywords": keywords}
    )
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    return pdf_path
