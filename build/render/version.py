"""Automatic, git-derived versioning for each generated PDF.

A version is two parts, ``vMAJOR.MINOR``, both read from git history with nothing
bumped by hand:

- MAJOR is the content edition: how many commits have touched the artifact's own
  source files (its YAML, prose, map, art). Scoped per artifact so one language
  being behind does not move another's, and a story edit does not move a sibling.
- MINOR is the layout revision: how many commits have touched the shared
  render/layout source files (`render_sources`) since that last content commit. So
  a template or layout change reflows the actual PDF and bumps MINOR, and a fresh
  content edition (a MAJOR bump) resets MINOR to 0, the way `major.minor` reads.

`updated` is the date of the most recent commit over either set.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

# The shared render/layout source files that determine how every PDF looks. A
# commit to any of them is a layout revision (the MINOR part), so a template change
# re-versions the library even when no content changed. Excludes version.py itself,
# library.py (orchestration and the README), and the image-generation modules, none
# of which change a rendered page.
_RENDER_SOURCES = (
    "build/render/pages.py",
    "build/render/kit.py",
    "build/render/playbook.py",
    "build/render/world_pdf.py",
    "build/render/examples.py",
    "build/render/flowables.py",
    "build/render/theme.py",
    "build/render/images.py",
    "build/render/markdown.py",
    "build/render/sheets.py",
    "build/render/glossary.py",
    "build/render/map.py",
    "build/render/mapgen.py",
    "build/render/footer.py",
    "build/render/colophon.py",
    "build/render/fonts.py",
    "build/render/strings.py",
)


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    updated: str  # ISO YYYY-MM-DD, or "unreleased" when there is no history
    dirty: bool = False

    @property
    def label(self) -> str:
        return f"v{self.major}.{self.minor}{'+' if self.dirty else ''}"


def render_sources(root: Path) -> list[Path]:
    """The shared layout source files folded into every artifact's MINOR version."""
    return [root / rel for rel in _RENDER_SOURCES]


def _git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


def version_info(
    root: Path, content_paths: list[Path], render_paths: list[Path] | None = None
) -> VersionInfo:
    """Version for an artifact: MAJOR from its content, MINOR from layout source.

    MAJOR counts commits over `content_paths` (the artifact's own sources). MINOR
    counts commits over `render_paths` (typically `render_sources(root)`) made since
    the most recent content commit, so a content edition resets the layout counter.
    Missing paths contribute nothing, so a caller may list assets that may not exist
    yet.
    """
    content = [str(p) for p in content_paths]
    render = [str(p) for p in (render_paths or [])]

    content_commits = [
        line for line in _git(root, ["log", "--format=%H", "--", *content]).splitlines()
        if line.strip()
    ]
    major = len(content_commits)
    latest_content = content_commits[0] if content_commits else ""

    minor = 0
    if render and latest_content:
        count = _git(
            root, ["rev-list", "--count", f"{latest_content}..HEAD", "--", *render]
        ).strip()
        minor = int(count) if count.isdigit() else 0

    all_paths = content + render
    if major == 0 and minor == 0:
        return VersionInfo(0, 0, "unreleased", False)
    date = _git(root, ["log", "-1", "--format=%cs", "--", *all_paths]).strip()
    dirty = bool(_git(root, ["status", "--porcelain", "--", *all_paths]).strip())
    return VersionInfo(major, minor, date or "unreleased", dirty)


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
    elif level != "simple":
        # The generated trail map always reads the simple narration, so a rich pack's
        # version must move when that map source changes too.
        paths.append(story_dir / "content" / locale / "narration.simple.md")
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
