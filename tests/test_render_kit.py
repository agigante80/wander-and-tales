from pypdf import PdfReader

from build.render import kit

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def _add_map(sample_repo):
    assets = sample_repo / "worlds" / "floating-isles" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_TINY_SVG, encoding="utf-8")


def test_build_kit_writes_one_merged_pdf(sample_repo, tmp_path):
    _add_map(sample_repo)
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    assert out.name == "floating-isles_sleeping-garden_en-GB_simple.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    # map + narration + rules + puzzles + idea-bank + glossary + sheet = at least 7
    assert len(PdfReader(str(out)).pages) >= 7


def test_build_kit_skips_missing_map(sample_repo, tmp_path):
    out = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "rich",
        out_dir=tmp_path,
    )
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) >= 6


def test_reading_level_selects_narration_file():
    assert kit.NARRATION_BY_LEVEL == {
        "simple": "narration.simple.md",
        "rich": "narration.rich.md",
    }
