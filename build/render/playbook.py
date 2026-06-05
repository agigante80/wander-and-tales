"""Build the Grown-up's Playbook PDF per (world, story, locale).

The Playbook is the grown-up's private prep: how to run this story (its rules) and
the puzzles together with their solutions. It is the only artifact that holds the
answers, so a child reading the Story Pack never meets one. One adult level per story
per locale. Pages are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from reportlab.platypus import Paragraph

from build import content
from build.render import chrome, colophon, fonts, footer, pages, strings, theme, version
from build.render import markdown as md
from build.render.kit import _merge


def build_playbook(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Grown-up's Playbook and return its nested, versioned path."""
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
            version.playbook_inputs(root, world_id, story_id, locale),
            version.render_sources(root),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    label = strings.ui(locale, "colophon_artifact_playbook")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        head = [
            chrome.HeaderBand(kicker=label, title=title, theme=th, motif=False),
            Paragraph(
                md.inline_to_rl(strings.ui(locale, "playbook_secret_note")),
                styles["body"],
            ),
        ]
        parts.append(pages.render_flowables(head, tmp_path / "00_title.pdf", world))
        parts.append(
            pages.render_markdown_file(
                content_dir / "rules.md", tmp_path / "10_rules.pdf", world, locale
            )
        )
        parts.append(
            pages.render_markdown_file(
                content_dir / "puzzles.md", tmp_path / "20_puzzles.pdf", world, locale
            )
        )
        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"playbook-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Grown-ups Playbook, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, playbook, {version_info.label}",
    )
    return out_path
