"""Build the Tale Book PDF per (world, story, locale, reading_level).

The Tale Book is the one thing the grown-up runs the game from, screen-first and
print-optional: a short title page, the read-aloud story for the reading level (text
only, with no embedded pictures, so it stays light on a phone), then how to run this
story (rules), the puzzles with their answers, and the colophon. The pictures live in
the Atlas and are shown to the players as each place is reached. The Tale Book holds the
answers, so it is the grown-up's; players never hold it, which keeps the surprises a
surprise. It replaces the old Story Pack narration plus the Grown-up's Playbook.
"""

import tempfile
from pathlib import Path

from reportlab.platypus import PageBreak, Paragraph, Spacer

from build import content
from build.render import (
    chrome,
    colophon,
    fonts,
    footer,
    pages,
    strings,
    theme,
    version,
)
from build.render import markdown as md
from build.render.kit import _merge

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}


def build_tale_book(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    reading_level: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Tale Book and return its nested, versioned path under out_dir."""
    if reading_level not in NARRATION_BY_LEVEL:
        raise ValueError(f"unknown reading level {reading_level!r}")

    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    content_dir = story_dir / "content" / locale

    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    if version_info is None:
        version_info = version.version_info(
            root,
            version.tale_book_inputs(root, world_id, story_id, locale, reading_level),
            version.render_sources(root),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    world_paragraph = (world.lore_summary or {}).get(locale, "")
    label = strings.ui(locale, "colophon_artifact_talebook")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        head: list = [
            chrome.HeaderBand(kicker=label, title=title, theme=th, motif=False),
        ]
        if world_paragraph:
            head.append(Paragraph(md.inline_to_rl(world_paragraph), styles["body"]))
        head.append(Spacer(1, 4))
        head.append(
            Paragraph(md.inline_to_rl(strings.ui(locale, "playbook_secret_note")),
                      styles["body"])
        )
        head.append(
            Paragraph(md.inline_to_rl(strings.ui(locale, "talebook_show_picture")),
                      styles["body"])
        )
        head.append(PageBreak())
        parts.append(pages.render_flowables(head, tmp_path / "00_title.pdf", world))

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_story_narration(
                narration, tmp_path / "10_narration.pdf", world, locale, []
            )
        )

        parts.append(
            pages.render_markdown_file(
                content_dir / "rules.md", tmp_path / "20_rules.pdf", world, locale
            )
        )
        parts.append(
            pages.render_markdown_file(
                content_dir / "puzzles.md", tmp_path / "30_puzzles.pdf", world, locale
            )
        )

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"{world_id}-{story_id}-tale-book-{reading_level}-{locale}-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Tale Book, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, {reading_level}, tale-book, {version_info.label}",
    )
    return out_path
