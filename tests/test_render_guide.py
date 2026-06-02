from pypdf import PdfReader

from build.render import pages


def test_render_guide_builds_a_pdf_from_markdown(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(
        "# Guide for the Grown-Up\n\nYou have three jobs: narrator, gentle "
        "referee, and biggest fan.\n\n## Yes, and\n\nNever just say no.\n",
        encoding="utf-8",
    )
    out = tmp_path / "guide.pdf"
    pages.render_guide(guide, out)
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 1


def test_render_guide_accepts_spanish(tmp_path):
    guide = tmp_path / "guia.md"
    guide.write_text("# Guia\n\nTienes tres trabajos.\n", encoding="utf-8")
    out = tmp_path / "guia.pdf"
    pages.render_guide(guide, out, "es-ES")
    assert out.read_bytes().startswith(b"%PDF")
