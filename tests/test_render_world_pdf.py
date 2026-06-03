from pypdf import PdfReader

from build.render import world_pdf


def test_world_book_writes_nested_versioned_pdf(sample_repo, tmp_path):
    out = world_pdf.build_world_pdf(
        sample_repo, "floating-isles", "en-GB", out_dir=tmp_path
    )
    assert out == tmp_path / "en-GB" / "floating-isles" / "world-book-v0.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    # cover + glossary + idea bank + stories list + colophon = 5 pages
    assert len(PdfReader(str(out)).pages) == 5


def test_world_book_renders_in_spanish(sample_repo, tmp_path):
    out = world_pdf.build_world_pdf(
        sample_repo, "floating-isles", "es-ES", out_dir=tmp_path
    )
    assert out.read_bytes().startswith(b"%PDF")
