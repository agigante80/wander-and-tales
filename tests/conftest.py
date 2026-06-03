import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    world_dir = tmp_path / "worlds" / "floating-isles"
    canon_dir = world_dir / "canon"
    story_dir = world_dir / "stories" / "sleeping-garden"
    content_en = story_dir / "content" / "en-GB"
    content_es = story_dir / "content" / "es-ES"
    for directory in (canon_dir, content_en, content_es):
        directory.mkdir(parents=True)

    (world_dir / "world.yaml").write_text(textwrap.dedent("""
        id: floating-isles
        name:
          en-GB: The Floating Isles
          es-ES: Las Islas Flotantes
        tone: gentle wonder
    """).lstrip(), encoding="utf-8")

    (canon_dir / "creatures.yaml").write_text(textwrap.dedent("""
        - id: mist-cat
          names:
            en-GB: Mist Cat
            es-ES: Gato de Niebla
          kind: creature
          disposition: friendly
          description:
            en-GB: A gentle cat made of fog who gives hints.
            es-ES: Un gato amable hecho de niebla que da pistas.
          first_seen: sleeping-garden
    """).lstrip(), encoding="utf-8")

    (story_dir / "story.yaml").write_text(textwrap.dedent("""
        world: floating-isles
        id: sleeping-garden
        title:
          en-GB: The Sleeping Garden
          es-ES: El Jardin Dormido
        age:
          recommended: young
          also_works_for: [early, older]
        skills: [vocabulary, logic, social-emotional]
        peril: gentle
        adult_gm: true
        dice:
          minimum: 1d6
          recommended: d20-set
        players:
          min: 2
          max: 2
        play_time_minutes: 30
    """).lstrip(), encoding="utf-8")

    for content_dir in (content_en, content_es):
        for name in ("narration.simple.md", "narration.rich.md", "rules.md",
                     "puzzles.md"):
            (content_dir / name).write_text("placeholder\n", encoding="utf-8")

    for code in ("en-GB", "es-ES"):
        world_content = world_dir / "content" / code
        world_content.mkdir(parents=True)
        (world_content / "idea-bank.md").write_text(
            "# Idea bank\n\nImprov fuel for this world.\n", encoding="utf-8"
        )

    lexicon_dir = tmp_path / "lexicon"
    lexicon_dir.mkdir()
    (lexicon_dir / "terms.yaml").write_text(textwrap.dedent("""
        - id: game-master
          names:
            en-GB: Game Master
            es-ES: Guia del Juego
    """).lstrip(), encoding="utf-8")

    return tmp_path


@pytest.fixture
def repo_with_images(tmp_path: Path) -> Path:
    world_dir = tmp_path / "worlds" / "w"
    canon_dir = world_dir / "canon"
    story_dir = world_dir / "stories" / "s"
    for directory in (canon_dir, story_dir):
        directory.mkdir(parents=True)

    (world_dir / "world.yaml").write_text(textwrap.dedent("""
        id: w
        name:
          en-GB: World
          es-ES: Mundo
        visual_style: Soft test storybook art in cream and green.
        images:
          - id: cover
            role: cover
            orientation: portrait
            prompt: A wide calm island in a gentle sky.
            alt:
              en-GB: A calm island.
              es-ES: Una isla tranquila.
          - id: beast
            role: portrait
            orientation: square
            canon_ref: creature1
            prompt: The friendly creature, curled and calm.
            alt:
              en-GB: A friendly creature.
              es-ES: Una criatura amable.
    """).lstrip(), encoding="utf-8")

    (canon_dir / "creatures.yaml").write_text(textwrap.dedent("""
        - id: creature1
          names:
            en-GB: Test Beast
            es-ES: Bestia de Prueba
          kind: creature
          description:
            en-GB: A gentle test creature.
            es-ES: Una criatura amable de prueba.
    """).lstrip(), encoding="utf-8")

    (story_dir / "story.yaml").write_text(textwrap.dedent("""
        world: w
        id: s
        title:
          en-GB: Story
          es-ES: Cuento
        age:
          recommended: young
        skills: [logic]
        peril: gentle
        adult_gm: true
        dice:
          minimum: 1d6
        players:
          min: 2
          max: 2
        play_time_minutes: 30
        images:
          - id: cover
            role: cover
            orientation: portrait
            prompt: The story scene at dawn.
            alt:
              en-GB: The story at dawn.
              es-ES: El cuento al amanecer.
          - id: scene-1
            role: scene
            orientation: landscape
            prompt: A wide gentle moment in the tale.
            alt:
              en-GB: A gentle moment.
              es-ES: Un momento tranquilo.
    """).lstrip(), encoding="utf-8")

    return tmp_path
