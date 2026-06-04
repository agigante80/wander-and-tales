from pypdf import PdfReader
from reportlab.lib.pagesizes import A4, landscape
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


def _mixed_orientation_pdf(path):
    c = rl_canvas.Canvas(str(path), pagesize=A4)
    c.drawString(100, 100, "portrait")
    c.showPage()
    c.setPageSize(landscape(A4))
    c.drawString(100, 100, "landscape")
    c.showPage()
    c.save()


def test_stamp_footers_draws_page_x_of_y_on_every_page(tmp_path):
    # A weak "page count preserved" check would pass even if the footer drew nothing;
    # assert the footer text and the correct running count are actually on each page.
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.stamp_footers(
        p, identity="Wits and Wonder · Story Pack · The Sleeping Garden",
        locale="en-GB", version_info=VersionInfo(7, 0, "2026-06-03"),
    )
    for index, page in enumerate(PdfReader(str(p)).pages, start=1):
        text = page.extract_text()
        assert "Wits and Wonder" in text
        assert f"page {index} of 2" in text


def test_stamp_footers_handles_landscape_pages(tmp_path):
    p = tmp_path / "mixed.pdf"
    _mixed_orientation_pdf(p)
    footer.stamp_footers(
        p, identity="Wits and Wonder · World Book · The Floating Isles",
        locale="en-GB", version_info=VersionInfo(4, 0, "2026-06-03"),
    )
    pages = PdfReader(str(p)).pages
    assert "page 2 of 2" in pages[1].extract_text()  # the landscape page got it too


def test_stamp_footers_keeps_page_count(tmp_path):
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.stamp_footers(
        p, identity="Wits and Wonder . Story Pack . The Sleeping Garden",
        locale="en-GB", version_info=VersionInfo(7, 0, "2026-06-03"),
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
