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
    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    narration = {"simple": "narration.simple.md", "rich": "narration.rich.md"}[level]
    return [
        story_dir / "story.yaml",
        story_dir / "content" / locale / narration,
        world_dir / "world.yaml",
        story_dir / "assets",
        world_dir / "assets",
    ]


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
    world_dir = root / "worlds" / world_id
    return [
        world_dir / "world.yaml",
        world_dir / "canon",
        world_dir / "content" / locale / "idea-bank.md",
        world_dir / "stories",
        world_dir / "assets",
    ]


def guide_inputs(root: Path, locale: str) -> list[Path]:
    return [root / "guide" / locale / "guide.md"]
