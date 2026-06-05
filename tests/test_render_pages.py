from pypdf import PdfReader

from build.models import World
from build.render import pages


def _world(fonts_block=None):
    data = {
        "id": "floating-isles",
        "name": {"en-GB": "The Floating Isles", "es-ES": "Las Islas Flotantes",
                 "it-IT": "Le Isole Fluttuanti", "pt-PT": "Le Isole Fluttuanti"},
        "palette": ["#fef9ef", "#4ea24a", "#2bb3a3"],
    }
    if fonts_block is not None:
        data["fonts"] = fonts_block
    return World.model_validate(data)


def test_render_markdown_file_writes_a_valid_pdf(tmp_path):
    src = tmp_path / "narration.simple.md"
    src.write_text(
        "# The Sleeping Garden\n\nThis morning the island is quiet. Demasiado "
        "silencio: accents like ñ and á must render.\n\n## Stop 1\n\n- look\n- try\n",
        encoding="utf-8",
    )
    out = tmp_path / "narration.pdf"
    pages.render_markdown_file(src, out, _world({"default": "dejavu-serif"}), "en-GB")
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 1


def test_render_flowables_accepts_landscape(tmp_path):
    out = tmp_path / "land.pdf"
    pages.render_flowables([], out, _world(), landscape_page=True)
    assert out.read_bytes().startswith(b"%PDF")
