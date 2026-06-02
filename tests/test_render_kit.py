from pypdf import PdfReader

from build.render import kit

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def _add_world_map(sample_repo):
    assets = sample_repo / "worlds" / "floating-isles" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_TINY_SVG, encoding="utf-8")


def _add_map(sample_repo):  # backwards-compatible alias used below
    _add_world_map(sample_repo)


def _story_assets(sample_repo):
    assets = (
        sample_repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    return assets


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


def test_kit_uses_a_locale_specific_story_map(sample_repo, tmp_path):
    # Only an es-ES story map exists: es-ES gets it, en-GB omits the map.
    assets = _story_assets(sample_repo)
    (assets / "map.es-ES.svg").write_text(_TINY_SVG, encoding="utf-8")

    es = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "simple",
        out_dir=tmp_path,
    )
    en = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    # es-ES has the map page, en-GB does not, so the es-ES kit is one page longer.
    assert len(PdfReader(str(es)).pages) == len(PdfReader(str(en)).pages) + 1


def test_reading_level_selects_narration_file():
    assert kit.NARRATION_BY_LEVEL == {
        "simple": "narration.simple.md",
        "rich": "narration.rich.md",
    }


_NEUTRAL_MAP = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="20" text-anchor="middle"></text>'
    '<text data-label="subtitle" x="100" y="40" text-anchor="middle"></text>'
    '<text data-label="stop:start" x="40" y="100" text-anchor="middle"></text>'
    '<text data-label="stop:mist-cat" data-wrap="2" x="150" y="100" text-anchor="middle"></text>'
    "</svg>"
)


def test_neutral_map_serves_en_gb_and_es_es(sample_repo, tmp_path):
    # Baseline: en-GB with no map yet.
    en_nomap = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path / "a",
    )
    base = len(PdfReader(str(en_nomap)).pages)

    assets = (
        sample_repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_NEUTRAL_MAP, encoding="utf-8")

    en = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path / "b",
    )
    es = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "simple",
        out_dir=tmp_path / "c",
    )
    # The neutral template adds a map page for BOTH locales (en-GB no longer omitted).
    assert len(PdfReader(str(en)).pages) == base + 1
    assert len(PdfReader(str(es)).pages) == base + 1
