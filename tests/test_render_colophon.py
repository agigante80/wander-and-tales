from pypdf import PdfReader
from reportlab.platypus import Image as RLImage

from build.models import World
from build.render import colophon, fonts, pages, theme
from build.render.version import VersionInfo


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def _world():
    return World.model_validate(
        {"id": "_", "name": {"en-GB": "_", "es-ES": "_"}}
    )


def test_colophon_includes_a_qr_and_text():
    flows = colophon.colophon_flowables(
        _styles(), "en-GB", VersionInfo(3, "2026-06-03"), "Story Pack",
        "https://example.com/x",
    )
    assert any(isinstance(f, RLImage) for f in flows)
    assert len(flows) >= 6


def test_colophon_renders_one_page_in_spanish(tmp_path):
    flows = colophon.colophon_flowables(
        _styles(), "es-ES", VersionInfo(1, "2026-06-03"), "Libro del Mundo",
        "https://example.com/x",
    )
    out = pages.render_flowables(flows, tmp_path / "c.pdf", _world())
    assert len(PdfReader(str(out)).pages) == 1
