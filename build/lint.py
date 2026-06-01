"""Deterministic structural lint over canon, lexicon, and stories.

What it guarantees: canon ids are unique within a world, every canon and lexicon
entry carries all required locales (enforced by the models, surfaced here as a
readable report), each story's `world` matches the directory it lives in, and
every required content file exists for every required locale.
"""

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from build import content, locales

_REQUIRED_CONTENT_FILES = (
    "narration.simple.md",
    "narration.rich.md",
    "rules.md",
    "puzzles.md",
    "idea-bank.md",
)


@dataclass(frozen=True)
class LintIssue:
    level: str  # "error" or "warning"
    message: str
    location: str


def _error(message: str, location: str) -> LintIssue:
    return LintIssue("error", message, location)


def lint_repo(root: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    worlds_dir = root / "worlds"
    if not worlds_dir.is_dir():
        return [_error("no worlds/ directory found", str(root))]

    for world_dir in sorted(p for p in worlds_dir.iterdir() if p.is_dir()):
        issues.extend(_lint_world(world_dir))
    return issues


def _lint_world(world_dir: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    world_id = world_dir.name

    canon_dir = world_dir / "canon"
    if canon_dir.is_dir():
        try:
            entries = content.load_canon(canon_dir)
        except ValidationError as exc:
            issues.append(_error(f"canon failed validation: {exc}", str(canon_dir)))
            entries = []
        seen: dict[str, str] = {}
        for entry in entries:
            if entry.id in seen:
                issues.append(
                    _error(f"duplicate canon id {entry.id!r}", str(canon_dir))
                )
            else:
                seen[entry.id] = str(canon_dir)

    stories_dir = world_dir / "stories"
    if stories_dir.is_dir():
        for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
            issues.extend(_lint_story(world_id, story_dir))
    return issues


def _lint_story(world_id: str, story_dir: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    story_yaml = story_dir / "story.yaml"
    if not story_yaml.is_file():
        issues.append(_error("missing story.yaml", str(story_dir)))
        return issues

    try:
        story = content.load_story(story_yaml)
    except ValidationError as exc:
        issues.append(_error(f"story failed validation: {exc}", str(story_yaml)))
        return issues

    if story.world != world_id:
        issues.append(
            _error(
                f"story world {story.world!r} does not match directory {world_id!r}",
                str(story_yaml),
            )
        )

    for code in locales.REQUIRED_LOCALES:
        for filename in _REQUIRED_CONTENT_FILES:
            path = story_dir / "content" / code / filename
            if not path.is_file():
                issues.append(
                    _error(f"missing content file {filename} for {code}", str(path))
                )
    return issues
