"""Build the Atlas PDF per (world, story, locale).

The Atlas is the only player-facing piece, and the only thing you would normally print:
a cover, the map, one big scene picture per place (shown to the players as the story
reaches that place, to pull them into the scene), and the blank adventure sheet at the
back. It carries no words of the story and no answers, so there is nothing to spoil. It
does not depend on the reading level, so there is one Atlas per story and locale.
"""

import tempfile
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, Spacer

from build import content
from build.render import (
    chrome,
    colophon,
    fonts,
    footer,
    images,
    map as kit_map,
    mapgen,
    pages,
    sheets,
    strings,
    theme,
    version,
)
from build.render.kit import _image_file, _map_label, _merge


def build_atlas(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Atlas and return its nested, versioned path under out_dir."""
    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id

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
            version.atlas_inputs(root, world_id, story_id, locale),
            version.render_sources(root),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    world_paragraph = (world.lore_summary or {}).get(locale, "")
    label = strings.ui(locale, "colophon_artifact_atlas")
    picture_word = strings.ui(locale, "atlas_picture")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        front = images.frontpage_flowables(
            title, world_paragraph, cover_path, styles, kicker=label, theme=th
        )
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
        else:
            parts.append(
                mapgen.render_generated_map(
                    tmp_path / "05_map.pdf", locale, title,
                    story_dir / "content" / locale / "narration.simple.md", th,
                )
            )

        if scene_items:
            # Two pictures to a page (half height each) to save paper. Each picture and
            # its label stay together, and the page framework packs two per A4 page.
            picture_flows: list = []
            for number, (path, caption) in enumerate(scene_items, start=1):
                picture_flows.append(KeepTogether([
                    Paragraph(f"{picture_word} {number}", styles["h2"]),
                    Spacer(1, 3),
                    chrome.RoundedImage(
                        path, th, max_h=100 * mm, caption=caption,
                        caption_font=faces.italic,
                    ),
                    Spacer(1, 10),
                ]))
            parts.append(
                pages.render_flowables(picture_flows, tmp_path / "10_pictures.pdf", world)
            )

        sheet = tmp_path / "80_sheet.pdf"
        sheets.render_character_sheet(
            sheet, locale, story.age.recommended, th,
            world_name=world.name.get(locale, world_id),
            powers=world.hero_powers,
        )
        parts.append(sheet)

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"{world_id}-{story_id}-atlas-{locale}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Atlas, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, atlas, {version_info.label}",
    )
    return out_path
