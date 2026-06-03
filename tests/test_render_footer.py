from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from build.render import footer
from build.render.version import VersionInfo


def _two_page_pdf(path):
    c = rl_canvas.Canvas(str(path), pagesize=A4)
    c.drawString(100, 100, "one")
    c.showPage()
    c.drawString(100, 100, "two")
    c.showPage()
    c.save()


def test_stamp_footers_keeps_page_count(tmp_path):
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.stamp_footers(
        p, identity="Wits and Wonder . Story Pack . The Sleeping Garden",
        locale="en-GB", version_info=VersionInfo(7, "2026-06-03"),
    )
    assert len(PdfReader(str(p)).pages) == 2


def test_set_metadata_writes_fields(tmp_path):
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.set_metadata(
        p, title="The Sleeping Garden, Story Pack, en-GB, v7",
        subject="Story Pack, v7, 2026-06-03", keywords="floating-isles, sleeping-garden",
    )
    meta = PdfReader(str(p)).metadata
    assert meta.title == "The Sleeping Garden, Story Pack, en-GB, v7"
    assert meta.author == "Wits and Wonder"
