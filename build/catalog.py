"""Generate catalog.md from every story.yaml (spec section 6).

The catalog is generated, never hand-written, so it cannot drift from the tags.
Titles use the canonical locale.
"""

from pathlib import Path

from build import locales
from build.models import Story

_HEADER = "| World | Title | Age | Skills | Peril | Dice | Players | Time |"
_DIVIDER = "|---|---|---|---|---|---|---|---|"


def _row(story: Story) -> str:
    title = story.title.get(locales.CANONICAL_LOCALE, story.id)
    skills = ", ".join(story.skills)
    players = (
        str(story.players.min)
        if story.players.min == story.players.max
        else f"{story.players.min} to {story.players.max}"
    )
    return (
        f"| {story.world} | {title} | {story.age.recommended} | {skills} "
        f"| {story.peril} | {story.dice.minimum} | {players} "
        f"| {story.play_time_minutes} min |"
    )


def build_catalog_markdown(stories: list[Story]) -> str:
    lines = ["# Catalog", "", _HEADER, _DIVIDER]
    for story in sorted(stories, key=lambda s: (s.world, s.id)):
        lines.append(_row(story))
    lines.append("")
    return "\n".join(lines)


def write_catalog(stories: list[Story], out_path: Path) -> None:
    out_path.write_text(build_catalog_markdown(stories), encoding="utf-8")
