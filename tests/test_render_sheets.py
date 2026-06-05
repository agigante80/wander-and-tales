import pytest
from pypdf import PdfReader

from build.render import sheets, theme
from build.tags import AGE_TIERS


@pytest.mark.parametrize("tier", AGE_TIERS)
def test_each_tier_renders_one_page(tmp_path, tier):
    out = tmp_path / f"sheet_{tier}.pdf"
    sheets.render_character_sheet(out, "en-GB", tier, theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1


def test_strength_world_sheet_renders(tmp_path):
    # A non-magic world labels the three-slot panel "strengths", not "magics".
    out = tmp_path / "sheet_strength.pdf"
    sheets.render_character_sheet(
        out, "it-IT", "young", theme.Theme.default(), powers="strength"
    )
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1


def test_unknown_tier_raises(tmp_path):
    with pytest.raises(ValueError):
        sheets.render_character_sheet(
            tmp_path / "x.pdf", "en-GB", "tween", theme.Theme.default()
        )


def test_spanish_sheet_renders(tmp_path):
    out = tmp_path / "sheet_es.pdf"
    sheets.render_character_sheet(out, "es-ES", "young", theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")


def test_older_spanish_sheet_renders_one_page(tmp_path):
    out = tmp_path / "sheet_older_es.pdf"
    sheets.render_character_sheet(out, "es-ES", "older", theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1
