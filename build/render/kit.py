"""Assemble one printable Story Pack PDF per (world, story, locale, reading_level).

The Story Pack is the child-safe play material: a front page (title, a short world
paragraph, the cover art when it exists), the map, the narration for the reading
level, the story-in-pictures gallery, the character sheet, and the colophon. The
rules, puzzles, idea bank, and glossary live in the Grown-up's Playbook and the World
Book, not here. Pages are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build import content
from build.render import (
    colophon,
    fonts,
    footer,
    images,
    map as kit_map,
    pages,
    sheets,
    strings,
    theme,
    version,
)

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}


def _image_file(assets_dir: Path, image_id: str) -> Path | None:
    path = assets_dir / f"{image_id}.png"
    return path if path.is_file() else None


def _map_label(key: str, story, canon_by_id: dict, locale: str) -> str:
    if key == "title":
        return story.title.get(locale, story.id)
    if key.startswith("stop:"):
        canon_id = key[len("stop:"):]
        entry = canon_by_id.get(canon_id)
        if entry is not None:
            return entry.names.get(locale, canon_id)
        return strings.ui(locale, "map_" + canon_id)
    return strings.ui(locale, "map_" + key.replace(":", "_").replace("-", "_"))


def _merge(parts: list[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path


def build_story_pack(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    reading_level: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Story Pack and return its nested, versioned path under out_dir."""
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

    story_assets = story_dir / "assets"
    cover_path = next(
        (
            f
            for image in story.images
            if image.role == "cover"
            and (f := _image_file(story_assets, image.id)) is not None
        ),
        None,
    )
    scene_items = [
        (f, image.alt.get(locale, ""))
        for image in story.images
        if image.role == "scene"
        and (f := _image_file(story_assets, image.id)) is not None
    ]

    if version_info is None:
        version_info = version.version_info(
            root,
            version.story_pack_inputs(root, world_id, story_id, locale, reading_level),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    world_paragraph = (world.lore_summary or {}).get(locale, "")
    label = strings.ui(locale, "colophon_artifact_storypack")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        front = images.frontpage_flowables(title, world_paragraph, cover_path, styles)
        parts.append(pages.render_flowables(front, tmp_path / "00_front.pdf", world))

        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            canon_by_id = {entry.id: entry for entry in canon}
            labels = {
                key: _map_label(key, story, canon_by_id, locale)
                for key in kit_map.template_keys(map_svg)
            }
            parts.append(
                kit_map.render_map_template(map_svg, tmp_path / "05_map.pdf", labels)
            )

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_story_narration(
                narration, tmp_path / "10_narration.pdf", world, locale, scene_items
            )
        )

        sheet = tmp_path / "80_sheet.pdf"
        sheets.render_character_sheet(sheet, locale, story.age.recommended, th, faces)
        parts.append(sheet)

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"story-pack-{reading_level}-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Story Pack, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, {reading_level}, {version_info.label}",
    )
    return out_path
