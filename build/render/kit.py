"""Assemble one printable kit PDF per (world, story, locale, reading_level).

Loads content through Plan 1's loaders, resolves the world+locale typeface, then
renders each page to a temporary PDF in a fixed order and merges them with pypdf
into dist/. The map page is optional: if the world has no assets/map.svg, the kit
builds without it.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build import content
from build.render import fonts, glossary, map as kit_map, pages, sheets, theme

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}

# Grown-up-facing prose pages that follow the kid-facing narration.
_PROSE_PAGES = ("rules.md", "puzzles.md", "idea-bank.md")


def _merge(parts: list[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path


def build_kit(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    reading_level: str,
    *,
    out_dir: Path | None = None,
) -> Path:
    """Build the kit PDF and return its path under out_dir (default dist/)."""
    if reading_level not in NARRATION_BY_LEVEL:
        raise ValueError(f"unknown reading level {reading_level!r}")

    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    content_dir = story_dir / "content" / locale

    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")
    canon = content.load_canon(world_dir / "canon")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    out_dir = out_dir if out_dir is not None else root / "dist"
    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            parts.append(kit_map.render_svg_to_pdf(map_svg, tmp_path / "00_map.pdf"))

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_markdown_file(narration, tmp_path / "10_narration.pdf", world, locale)
        )

        for index, filename in enumerate(_PROSE_PAGES, start=2):
            src = content_dir / filename
            parts.append(
                pages.render_markdown_file(
                    src, tmp_path / f"{index}0_{filename}.pdf", world, locale
                )
            )

        gloss = glossary.glossary_flowables(canon, locale, styles, th)
        parts.append(pages.render_flowables(gloss, tmp_path / "80_glossary.pdf", world))

        sheet = tmp_path / "90_sheet.pdf"
        sheets.render_character_sheet(sheet, locale, story.age.recommended, th, faces)
        parts.append(sheet)

        out_path = out_dir / f"{world_id}_{story_id}_{locale}_{reading_level}.pdf"
        return _merge(parts, out_path)
