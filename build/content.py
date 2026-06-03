"""Load YAML content into typed models."""

from collections.abc import Iterator
from pathlib import Path

import yaml

from build.models import CanonEntry, ExampleHero, LexiconTerm, Story, World


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_world(path: Path) -> World:
    return World.model_validate(_load_yaml(path))


def load_story(path: Path) -> Story:
    return Story.model_validate(_load_yaml(path))


def load_canon(canon_dir: Path) -> list[CanonEntry]:
    entries: list[CanonEntry] = []
    for yaml_path in sorted(canon_dir.glob("*.yaml")):
        rows = _load_yaml(yaml_path) or []
        for row in rows:
            entries.append(CanonEntry.model_validate(row))
    return entries


def load_heroes(world_dir: Path) -> list[ExampleHero]:
    """Load a world's example heroes from heroes.yaml, or [] if there are none."""
    path = world_dir / "heroes.yaml"
    if not path.is_file():
        return []
    rows = _load_yaml(path) or []
    return [ExampleHero.model_validate(row) for row in rows]


def load_lexicon(path: Path) -> list[LexiconTerm]:
    rows = _load_yaml(path) or []
    return [LexiconTerm.model_validate(row) for row in rows]


def iter_stories(worlds_dir: Path) -> Iterator[Story]:
    for story_yaml in sorted(worlds_dir.glob("*/stories/*/story.yaml")):
        yield load_story(story_yaml)
