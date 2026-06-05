from pypdf import PdfReader

from build.render import kit

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)

_NEUTRAL_MAP = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="20" text-anchor="middle"></text>'
    '<text data-label="stop:start" x="40" y="100" text-anchor="middle"></text>'
    "</svg>"
)


def _story_assets(repo):
    assets = (
        repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    return assets


def _is_a4(width: float, height: float) -> bool:
    portrait = (595.276, 841.890)
    return (
        (abs(width - portrait[0]) < 2 and abs(height - portrait[1]) < 2)
        or (abs(width - portrait[1]) < 2 and abs(height - portrait[0]) < 2)
    )


def test_reading_level_selects_narration_file():
    assert kit.NARRATION_BY_LEVEL == {
        "simple": "narration.simple.md",
        "rich": "narration.rich.md",
    }


def test_story_pack_writes_nested_versioned_pdf(sample_repo, tmp_path):
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    assert out == tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.0.pdf"
    assert out.read_bytes().startswith(b"%PDF")


def test_story_pack_has_front_map_narration_sheet_colophon(sample_repo, tmp_path):
    # No hand-drawn map, no cover, no scenes: the map is generated, so the pack is
    # front + map + narration + sheet + colophon = 5 pages.
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "rich",
        out_dir=tmp_path,
    )
    assert len(PdfReader(str(out)).pages) == 5


def test_story_pack_adds_a_landscape_map_page(sample_repo, tmp_path):
    (_story_assets(sample_repo) / "map.svg").write_text(_NEUTRAL_MAP, encoding="utf-8")
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    pages = PdfReader(str(out)).pages
    assert len(pages) == 5  # the four above plus the map
    assert all(_is_a4(float(p.mediabox.width), float(p.mediabox.height)) for p in pages)


def test_cover_image_stays_on_the_front_page(sample_repo, tmp_path):
    from PIL import Image as PILImage

    story_dir = sample_repo / "worlds/floating-isles/stories/sleeping-garden"
    assets = story_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    PILImage.new("RGB", (400, 600), "white").save(assets / "cover.png")
    sy = story_dir / "story.yaml"
    sy.write_text(
        sy.read_text(encoding="utf-8")
        + (
            "images:\n  - id: cover\n    role: cover\n    orientation: portrait\n"
            "    prompt: A cover.\n    alt:\n      en-GB: A cover.\n      es-ES: Una portada.\n      it-IT: Una copertina.\n"
        ),
        encoding="utf-8",
    )
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    # The cover is embedded on the front page (not a new page); with the generated map
    # the pack is front + map + narration + sheet + colophon = 5 pages.
    assert len(PdfReader(str(out)).pages) == 5


def test_story_pack_every_page_is_a4_without_a_hand_map(sample_repo, tmp_path):
    # With no hand-drawn map the pack still ships a generated trail map, and every page
    # (including that A4-portrait map) must be A4. The landscape hand-map case is above.
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    for page in PdfReader(str(out)).pages:
        assert _is_a4(float(page.mediabox.width), float(page.mediabox.height))


def test_story_pack_omits_the_glossary(sample_repo, tmp_path):
    # The who's-who glossary belongs in the World Book, never in the child-safe pack.
    from build.render import strings

    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(out)).pages)
    assert strings.ui("en-GB", "glossary_title") not in text
