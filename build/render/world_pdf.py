"""Build the World Book PDF per (world, locale).

The World Book is the world reference shared by every story: the world cover and
lore, the full who's-who glossary from canon (with portraits when art exists), the
world-level idea bank, and a list of the stories in the world. One per locale. Pages
are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from reportlab.platypus import Paragraph

from build import content
from build.render import (
    colophon,
    fonts,
    footer,
    glossary,
    images,
    pages,
    strings,
    theme,
    version,
)
from build.render import markdown as md
from build.render.kit import _image_file, _merge


def _first_sentence(path: Path) -> str:
    """The first prose sentence of a narration file, skipping headings and blanks."""
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for end in (". ", "! ", "? "):
            if end in stripped:
                return stripped.split(end)[0] + end.strip()
        return stripped
    return ""


def _portrait_paths(root: Path, world_id: str, world) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    world_dir = root / "worlds" / world_id
    for image in world.images:
        if image.role == "portrait" and image.canon_ref:
            found = _image_file(world_dir / "assets", image.id)
            if found is not None:
                paths[image.canon_ref] = found
    for story_yaml in sorted((world_dir / "stories").glob("*/story.yaml")):
        story = content.load_story(story_yaml)
        for image in story.images:
            if image.role == "portrait" and image.canon_ref:
                found = _image_file(story_yaml.parent / "assets", image.id)
                if found is not None:
                    paths[image.canon_ref] = found
    return paths


def _stories_flowables(root: Path, world_id: str, locale: str, styles: dict) -> list:
    flows = [
        Paragraph(
            md.inline_to_rl(strings.ui(locale, "worldbook_stories_title")), styles["h1"]
        )
    ]
    stories_dir = root / "worlds" / world_id / "stories"
    for story_yaml in sorted(stories_dir.glob("*/story.yaml")):
        story = content.load_story(story_yaml)
        title = story.title.get(locale, story.id)
        hook = _first_sentence(story_yaml.parent / "content" / locale / "narration.simple.md")
        line = f"**{title}** ({story.age.recommended}). {hook}".strip()
        flows.append(Paragraph(md.inline_to_rl(line), styles["body"]))
    return flows


def build_world_pdf(
    root: Path,
    world_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the World Book and return its nested, versioned path."""
    world_dir = root / "worlds" / world_id
    world = content.load_world(world_dir / "world.yaml")
    canon = content.load_canon(world_dir / "canon")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    if version_info is None:
        version_info = version.version_info(
            root, version.world_book_inputs(root, world_id, locale)
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    label = strings.ui(locale, "colophon_artifact_worldbook")
    world_name = world.name.get(locale, world_id)
    lore = (world.lore_summary or {}).get(locale, "")
    cover_path = next(
        (
            f
            for image in world.images
            if image.role == "cover"
            and (f := _image_file(world_dir / "assets", image.id)) is not None
        ),
        None,
    )

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        cover = images.frontpage_flowables(world_name, lore, cover_path, styles)
        parts.append(pages.render_flowables(cover, tmp_path / "00_cover.pdf", world))

        gloss = glossary.glossary_flowables(
            canon, locale, styles, th, _portrait_paths(root, world_id, world)
        )
        parts.append(pages.render_flowables(gloss, tmp_path / "10_glossary.pdf", world))

        idea = world_dir / "content" / locale / "idea-bank.md"
        parts.append(
            pages.render_markdown_file(idea, tmp_path / "20_idea.pdf", world, locale)
        )

        stories = _stories_flowables(root, world_id, locale, styles)
        parts.append(pages.render_flowables(stories, tmp_path / "30_stories.pdf", world))

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = out_dir / locale / world_id / f"world-book-{version_info.label}.pdf"
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label} · {world_name}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{world_name}, {label}, {locale}, {version_info.label}",
        subject=f"World Book, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {locale}, world-book, {version_info.label}",
    )
    return out_path
