"""Compose and export copy-paste-ready image prompts.

A full prompt is the world's shared visual_style, then the image subject, then a
technical line from role and orientation, then (if canon_ref resolves) the canon
name and description for consistency. The stored prompt is only the subject, so
editing visual_style once updates every prompt in the world.
"""

from dataclasses import dataclass
from pathlib import Path

from build import content, locales
from build.models import CanonEntry, Image, World

_ASPECT = {
    "portrait": "Portrait orientation, about 3 to 4.",
    "landscape": "Landscape orientation, about 4 to 3.",
    "square": "Square orientation, 1 to 1.",
}
_RULES = (
    "No text, letters, words, or numbers anywhere in the image. "
    "Soft children's storybook illustration. Gentle and friendly, nothing scary "
    "or violent."
)
_DEFAULT_STYLE = "Soft, warm children's storybook illustration."


@dataclass(frozen=True)
class PromptEntry:
    world_id: str
    story_id: str | None
    image: Image
    text: str


def compose_prompt(world: World, image: Image, canon_by_id: dict[str, CanonEntry]) -> str:
    """Compose the full, paste-ready prompt for one image."""
    parts = [
        world.visual_style or _DEFAULT_STYLE,
        image.prompt,
        f"{_ASPECT[image.orientation]} {_RULES}",
    ]
    entry = canon_by_id.get(image.canon_ref) if image.canon_ref else None
    if entry is not None:
        name = entry.names.get(locales.CANONICAL_LOCALE, image.canon_ref)
        desc = (entry.description or {}).get(locales.CANONICAL_LOCALE, "")
        parts.append(f"Depicts: {name}, {desc}".rstrip(", ").rstrip())
    return "\n\n".join(p for p in parts if p)


def _canon_for(world_dir: Path) -> dict[str, CanonEntry]:
    canon_dir = world_dir / "canon"
    if not canon_dir.is_dir():
        return {}
    return {entry.id: entry for entry in content.load_canon(canon_dir)}


def iter_image_prompts(
    root: Path, world: str | None = None, story: str | None = None
) -> list[PromptEntry]:
    """Compose prompts for every declared image, optionally filtered.

    When a story is named, world-level images are excluded so the output is just
    that story's images.
    """
    entries: list[PromptEntry] = []
    worlds_dir = root / "worlds"
    if not worlds_dir.is_dir():
        return entries
    for world_dir in sorted(p for p in worlds_dir.iterdir() if p.is_dir()):
        if world is not None and world_dir.name != world:
            continue
        w = content.load_world(world_dir / "world.yaml")
        canon_by_id = _canon_for(world_dir)
        if story is None:
            for image in w.images:
                entries.append(
                    PromptEntry(w.id, None, image, compose_prompt(w, image, canon_by_id))
                )
        stories_dir = world_dir / "stories"
        if stories_dir.is_dir():
            for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
                if story is not None and story_dir.name != story:
                    continue
                s = content.load_story(story_dir / "story.yaml")
                for image in s.images:
                    entries.append(
                        PromptEntry(w.id, s.id, image, compose_prompt(w, image, canon_by_id))
                    )
    return entries


def build_prompts_markdown(entries: list[PromptEntry]) -> str:
    """Render the prompts as copy-paste markdown, grouped by world then story."""
    lines = ["# Image prompts", ""]
    current: object = object()
    for entry in entries:
        key = (entry.world_id, entry.story_id)
        if key != current:
            current = key
            if entry.story_id is None:
                lines.append(f"## World: {entry.world_id}")
            else:
                lines.append(f"## Story: {entry.world_id} / {entry.story_id}")
            lines.append("")
        owner = entry.world_id if entry.story_id is None else entry.story_id
        lines.append(
            f"### {owner} / {entry.image.id}  [{entry.image.role}, {entry.image.orientation}]"
        )
        lines.append("")
        lines.append("```")
        lines.append(entry.text)
        lines.append("```")
        lines.append("")
        lines.append("Alt text:")
        for code in locales.REQUIRED_LOCALES:
            lines.append(f"- {code}: {entry.image.alt.get(code, '')}")
        lines.append("")
    return "\n".join(lines)


def write_prompts(entries: list[PromptEntry], out_path: Path) -> None:
    out_path.write_text(build_prompts_markdown(entries), encoding="utf-8")
