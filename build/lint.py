"""Deterministic structural lint over canon, lexicon, and stories.

What it guarantees: canon ids are unique within a world, every canon and lexicon
entry carries all required locales (enforced by the models, surfaced here as a
readable report), each story's `world` matches the directory it lives in,
every required content file exists for every required locale, and each world has a
world-level idea bank for every required locale.
It also warns when an image's canon_ref names no canon entry, when a declared
image has no generated file, and when an assets PNG has no image declaration.
"""

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from build import content, locales
from build.models import Image

_REQUIRED_CONTENT_FILES = (
    "narration.simple.md",
    "narration.rich.md",
    "rules.md",
    "puzzles.md",
)


@dataclass(frozen=True)
class LintIssue:
    level: str  # "error" or "warning"
    message: str
    location: str


def _error(message: str, location: str) -> LintIssue:
    return LintIssue("error", message, location)


def _warning(message: str, location: str) -> LintIssue:
    return LintIssue("warning", message, location)


def _lint_lexicon(root: Path) -> list[LintIssue]:
    """Check the repo-wide lexicon/terms.yaml if present (it is optional)."""
    issues: list[LintIssue] = []
    lexicon_path = root / "lexicon" / "terms.yaml"
    if not lexicon_path.is_file():
        return issues
    try:
        terms = content.load_lexicon(lexicon_path)
    except ValidationError as exc:
        issues.append(_error(f"lexicon failed validation: {exc}", str(lexicon_path)))
        return issues
    seen: set[str] = set()
    for term in terms:
        if term.id in seen:
            issues.append(
                _error(f"duplicate lexicon id {term.id!r}", str(lexicon_path))
            )
        else:
            seen.add(term.id)
    return issues


def lint_repo(root: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    issues.extend(_lint_lexicon(root))
    worlds_dir = root / "worlds"
    if not worlds_dir.is_dir():
        issues.append(_error("no worlds/ directory found", str(root)))
        return issues

    for world_dir in sorted(p for p in worlds_dir.iterdir() if p.is_dir()):
        issues.extend(_lint_world(world_dir))
    return issues


def _lint_world(world_dir: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    world_id = world_dir.name

    canon_ids: set[str] = set()
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
        canon_ids = set(seen)

    world_yaml = world_dir / "world.yaml"
    if world_yaml.is_file():
        try:
            world = content.load_world(world_yaml)
        except ValidationError as exc:
            issues.append(_error(f"world failed validation: {exc}", str(world_yaml)))
        else:
            issues.extend(_lint_image_refs(world.images, canon_ids, str(world_yaml)))
            issues.extend(
                _lint_image_files(world.images, world_dir / "assets", str(world_yaml))
            )

    for code in locales.REQUIRED_LOCALES:
        idea = world_dir / "content" / code / "idea-bank.md"
        if not idea.is_file():
            issues.append(_error(f"missing world idea bank for {code}", str(idea)))

    stories_dir = world_dir / "stories"
    if stories_dir.is_dir():
        for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
            issues.extend(_lint_story(world_id, story_dir, canon_ids))
    return issues


def _lint_image_refs(images: list[Image], canon_ids: set[str], location: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for image in images:
        if image.canon_ref and image.canon_ref not in canon_ids:
            issues.append(
                _warning(
                    f"image {image.id!r} canon_ref {image.canon_ref!r} "
                    f"names no canon entry",
                    location,
                )
            )
    return issues


def _lint_image_files(
    images: list[Image], assets_dir: Path, source_location: str
) -> list[LintIssue]:
    """Warn on declared images with no PNG, and on PNGs with no declaration.

    Each declared image `id` is expected at `<assets_dir>/<id>.png`. The orphan
    check only looks at PNG files, so non-image assets (the map SVG, for example)
    are ignored.
    """
    issues: list[LintIssue] = []
    declared: set[str] = set()
    for image in images:
        declared.add(image.id)
        target = assets_dir / f"{image.id}.png"
        if not target.is_file():
            issues.append(
                _warning(f"image {image.id!r} has no generated file at {target}",
                         source_location)
            )
    if assets_dir.is_dir():
        for png in sorted(assets_dir.glob("*.png")):
            if png.stem not in declared:
                issues.append(
                    _warning(
                        f"image file {png.name} has no matching image declaration",
                        str(png),
                    )
                )
    return issues


def _lint_story(world_id: str, story_dir: Path, canon_ids: set[str]) -> list[LintIssue]:
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

    issues.extend(_lint_image_refs(story.images, canon_ids, str(story_yaml)))
    issues.extend(
        _lint_image_files(story.images, story_dir / "assets", str(story_yaml))
    )

    for code in locales.REQUIRED_LOCALES:
        for filename in _REQUIRED_CONTENT_FILES:
            path = story_dir / "content" / code / filename
            if not path.is_file():
                issues.append(
                    _error(f"missing content file {filename} for {code}", str(path))
                )
    return issues
