"""Automatic, git-derived versioning for each generated PDF.

An artifact's version comes from git history over exactly the source files that
compose it: `number` is how many commits have touched those files, `updated` is the
date of the most recent such commit. Nothing is bumped by hand, so one language
being behind does not move another language's version.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VersionInfo:
    number: int
    updated: str  # ISO YYYY-MM-DD, or "unreleased" when there is no history
    dirty: bool = False

    @property
    def label(self) -> str:
        return f"v{self.number}{'+' if self.dirty else ''}"


def _git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


def version_info(root: Path, paths: list[Path]) -> VersionInfo:
    """Version for an artifact, from git history over its input paths.

    Missing paths contribute nothing (git simply reports no commits for them), so a
    caller may list candidate asset files that may not exist yet.
    """
    rels = [str(p) for p in paths]
    log = _git(root, ["log", "--format=%H", "--", *rels])
    number = sum(1 for line in log.splitlines() if line.strip())
    if number == 0:
        return VersionInfo(number=0, updated="unreleased", dirty=False)
    date = _git(root, ["log", "-1", "--format=%cs", "--", *rels]).strip()
    dirty = bool(_git(root, ["status", "--porcelain", "--", *rels]).strip())
    return VersionInfo(number=number, updated=date or "unreleased", dirty=dirty)


def story_pack_inputs(
    root: Path, world_id: str, story_id: str, locale: str, level: str
) -> list[Path]:
    """The source files this Story Pack reads, scoped so versions stay isolated.

    Only what this pack embeds for this locale and level: its narration, story.yaml
    and world.yaml, the map actually resolved for this locale, and the story cover.
    Other locales' content, the rules and puzzles, the idea bank, and World-Book-only
    portraits do not move this version. (Passing whole asset directories would
    over-couple, e.g. a world portrait change would bump every Story Pack.)
    """
    from build import content
    from build.render import map as kit_map

    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    narration = {"simple": "narration.simple.md", "rich": "narration.rich.md"}[level]
    paths = [
        story_dir / "story.yaml",
        story_dir / "content" / locale / narration,
        world_dir / "world.yaml",
    ]
    resolved_map = kit_map.find_map(world_dir, story_dir, locale)
    if resolved_map is not None:
        paths.append(resolved_map)
    story_yaml = story_dir / "story.yaml"
    if story_yaml.is_file():
        for image in content.load_story(story_yaml).images:
            if image.role == "cover":
                paths.append(story_dir / "assets" / f"{image.id}.png")
    return paths


def playbook_inputs(
    root: Path, world_id: str, story_id: str, locale: str
) -> list[Path]:
    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    return [
        story_dir / "story.yaml",
        story_dir / "content" / locale / "rules.md",
        story_dir / "content" / locale / "puzzles.md",
        world_dir / "world.yaml",
    ]


def world_book_inputs(root: Path, world_id: str, locale: str) -> list[Path]:
    """The source files this World Book reads, scoped so versions stay isolated.

    World.yaml, the canon, the world idea bank for this locale, the world cover, and
    per story its story.yaml and its simple narration for this locale (the hook
    source). Other locales' content and the rules and puzzles do not move this
    version. (Passing the whole stories/ directory would over-couple, e.g. an es-ES
    rules edit would bump the en-GB World Book.)
    """
    from build import content

    world_dir = root / "worlds" / world_id
    paths = [
        world_dir / "world.yaml",
        world_dir / "canon",
        world_dir / "content" / locale / "idea-bank.md",
    ]
    world_yaml = world_dir / "world.yaml"
    if world_yaml.is_file():
        for image in content.load_world(world_yaml).images:
            if image.role == "cover":
                paths.append(world_dir / "assets" / f"{image.id}.png")
    for story_yaml in sorted((world_dir / "stories").glob("*/story.yaml")):
        paths.append(story_yaml)
        paths.append(story_yaml.parent / "content" / locale / "narration.simple.md")
    return paths


def guide_inputs(root: Path, locale: str) -> list[Path]:
    return [root / "guide" / locale / "guide.md"]


def example_heroes_inputs(root: Path, world_id: str, locale: str) -> list[Path]:
    """The source files the example-heroes sheets read: the heroes data, the world
    (theme and palette), the canon (magic names and descriptions), and the hero
    portraits."""
    from build import content

    world_dir = root / "worlds" / world_id
    paths = [world_dir / "heroes.yaml", world_dir / "world.yaml", world_dir / "canon"]
    if (world_dir / "heroes.yaml").is_file():
        for hero in content.load_heroes(world_dir):
            paths.append(world_dir / "assets" / f"{hero.image.id}.png")
    return paths
