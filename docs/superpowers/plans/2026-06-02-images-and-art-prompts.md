# Images and Art Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let every world and story declare illustrations in its YAML, each with a generation prompt, then export those prompts as copy-paste-ready text and optionally generate the actual PNGs from them with the OpenAI Images API, all while keeping art locale-neutral and only the alt text localized.

**Architecture:** A new vocabulary `build/visuals.py` defines image roles and orientations. The `Image` model and new `World`/`Story` fields hold the declarations, validated against that vocabulary. `build/prompts.py` composes a world's shared `visual_style` plus each image's subject plus a technical line into one full prompt, and exports them. `build/generate.py` turns a composed prompt into a PNG via an injectable OpenAI client. Two new CLI subcommands (`prompts`, `generate-images`) wire it up. Generation and the API client are imported lazily so the core tooling needs no new dependencies to run.

**Tech Stack:** Python 3.11+, pydantic v2 (schema), PyYAML (already used), the OpenAI Python SDK and python-dotenv (new, optional `images` extra), pytest. The OpenAI client is injected in tests so nothing hits the network.

---

## File structure

```
build/visuals.py        # NEW vocabulary: IMAGE_ROLES, ORIENTATIONS (pure, like fontspec.py)
build/models.py         # MODIFIED: Image model; World.visual_style, World.images; Story.images
build/prompts.py        # NEW: compose a full prompt, iterate all images, export markdown
build/generate.py       # NEW: orientation->size, target path, generate one image, generate all
build/__main__.py       # MODIFIED: `prompts` and `generate-images` subcommands
build/lint.py           # MODIFIED: warn when a canon_ref names no canon entry
pyproject.toml          # MODIFIED: new optional `images` group (openai, python-dotenv)
worlds/floating-isles/world.yaml                            # MODIFIED: visual_style + 3 images
worlds/floating-isles/stories/sleeping-garden/story.yaml    # MODIFIED: 5 images
tests/conftest.py       # MODIFIED: add a repo_with_images fixture
tests/test_visuals.py            # NEW
tests/test_models_images.py      # NEW
tests/test_prompts.py            # NEW
tests/test_cli_prompts.py        # NEW
tests/test_generate.py           # NEW
tests/test_cli_generate.py       # NEW
docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md  # MODIFIED: images section
.claude/skills/authoring-story-content/SKILL.md             # MODIFIED: images authoring rules
CLAUDE.md               # MODIFIED: document the images feature
```

Layering: `visuals` is a pure vocabulary the model imports. `models` holds the schema. `prompts` reads models and composes text (no network). `generate` depends on `prompts` for the entries and on an injected client for the API. The CLI wires them, importing `openai`/`dotenv` lazily so `validate`/`lint`/`catalog`/`render`/`prompts` all run without the `images` extra.

---

## Task 1: Image vocabulary

**Files:**
- Create: `build/visuals.py`
- Test: `tests/test_visuals.py`

- [ ] **Step 1: Write the failing test**

`tests/test_visuals.py`:

```python
from build import visuals


def test_image_roles_and_orientations():
    assert visuals.IMAGE_ROLES == ("cover", "scene", "portrait", "motif")
    assert visuals.ORIENTATIONS == ("portrait", "landscape", "square")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_visuals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.visuals'`.

- [ ] **Step 3: Implement the vocabulary**

`build/visuals.py`:

```python
"""Image vocabulary: the single source of truth for image roles and orientations.

Pure data so the model can import it without any rendering or network dependency,
like fontspec.py, tags.py and dice.py.
"""

IMAGE_ROLES = ("cover", "scene", "portrait", "motif")
ORIENTATIONS = ("portrait", "landscape", "square")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_visuals.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/visuals.py tests/test_visuals.py
git commit -m "feat: image roles and orientations vocabulary"
```

---

## Task 2: Image model and world/story fields

**Files:**
- Modify: `build/models.py`
- Test: `tests/test_models_images.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models_images.py`:

```python
import pytest
from pydantic import ValidationError

from build.models import Image, Story, World


def _image(**over):
    data = {
        "id": "cover",
        "role": "cover",
        "orientation": "portrait",
        "prompt": "A sleeping garden on a floating island.",
        "alt": {"en-GB": "A sleeping garden.", "es-ES": "Un jardin dormido."},
    }
    data.update(over)
    return data


def _story(images=None):
    data = {
        "world": "floating-isles",
        "id": "sleeping-garden",
        "title": {"en-GB": "The Sleeping Garden", "es-ES": "El Jardin Dormido"},
        "age": {"recommended": "young"},
        "skills": ["logic"],
        "peril": "gentle",
        "adult_gm": True,
        "dice": {"minimum": "1d6"},
        "players": {"min": 2, "max": 2},
        "play_time_minutes": 30,
    }
    if images is not None:
        data["images"] = images
    return data


def test_valid_image_parses():
    img = Image.model_validate(_image(canon_ref="mist-cat"))
    assert img.role == "cover"
    assert img.canon_ref == "mist-cat"


def test_image_defaults_canon_ref_to_none():
    assert Image.model_validate(_image()).canon_ref is None


def test_unknown_role_fails():
    with pytest.raises(ValidationError):
        Image.model_validate(_image(role="banner"))


def test_unknown_orientation_fails():
    with pytest.raises(ValidationError):
        Image.model_validate(_image(orientation="tall"))


def test_missing_alt_locale_fails():
    with pytest.raises(ValidationError) as err:
        Image.model_validate(_image(alt={"en-GB": "only english"}))
    assert "es-ES" in str(err.value)


def test_world_without_images_defaults_empty_and_no_style():
    world = World.model_validate({"id": "w", "name": {"en-GB": "W", "es-ES": "W"}})
    assert world.images == []
    assert world.visual_style is None


def test_world_collects_visual_style_and_images():
    world = World.model_validate(
        {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
         "visual_style": "Soft storybook art.", "images": [_image()]}
    )
    assert world.visual_style == "Soft storybook art."
    assert world.images[0].id == "cover"


def test_story_collects_images():
    story = Story.model_validate(_story(images=[_image()]))
    assert story.images[0].id == "cover"


def test_duplicate_image_ids_in_a_world_fail():
    with pytest.raises(ValidationError) as err:
        World.model_validate(
            {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
             "images": [_image(id="dup"), _image(id="dup")]}
        )
    assert "dup" in str(err.value)


def test_duplicate_image_ids_in_a_story_fail():
    with pytest.raises(ValidationError):
        Story.model_validate(_story(images=[_image(id="dup"), _image(id="dup")]))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_models_images.py -v`
Expected: FAIL with `ImportError: cannot import name 'Image' from 'build.models'`.

- [ ] **Step 3: Add the visuals import**

In `build/models.py`, change the imports line:

```python
from build import dice, fontspec, locales, tags, visuals
```

- [ ] **Step 4: Add the Image model and a shared id-uniqueness helper**

In `build/models.py`, add this just above `class World` (after `class LexiconTerm`):

```python
class Image(_Strict):
    """A declared illustration plus its generation prompt.

    The prompt is the locale-neutral subject; the world's visual_style preamble
    and a technical line are added at export time (see build/prompts.py). Art is
    text-free and language-neutral; only alt is localized.
    """

    id: str
    role: str
    orientation: str
    prompt: str
    alt: dict[str, str]
    canon_ref: str | None = None

    @field_validator("role")
    @classmethod
    def _known_role(cls, value: str) -> str:
        if value not in visuals.IMAGE_ROLES:
            raise ValueError(f"image role {value!r} not in {visuals.IMAGE_ROLES}")
        return value

    @field_validator("orientation")
    @classmethod
    def _known_orientation(cls, value: str) -> str:
        if value not in visuals.ORIENTATIONS:
            raise ValueError(
                f"image orientation {value!r} not in {visuals.ORIENTATIONS}"
            )
        return value

    @field_validator("alt")
    @classmethod
    def _alt_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "alt")
        return value

    @field_validator("canon_ref")
    @classmethod
    def _canon_ref_nonempty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("canon_ref, when given, must be a non-empty id")
        return value


def _unique_image_ids(images: list[Image]) -> list[Image]:
    seen: set[str] = set()
    for image in images:
        if image.id in seen:
            raise ValueError(f"duplicate image id {image.id!r}")
        seen.add(image.id)
    return images
```

- [ ] **Step 5: Add the fields to World and Story**

In `build/models.py`, update `class World` to add the two fields and a validator (keep the existing `name` validator):

```python
class World(_Strict):
    id: str
    name: dict[str, str]
    tone: str | None = None
    palette: list[str] = []
    lore_summary: dict[str, str] | None = None
    fonts: WorldFonts | None = None
    visual_style: str | None = None
    images: list[Image] = []

    @field_validator("name")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "name")
        return value

    @field_validator("images")
    @classmethod
    def _unique_images(cls, value: list[Image]) -> list[Image]:
        return _unique_image_ids(value)
```

In `class Story`, add the `images` field (after `play_time_minutes`) and its validator (keep the existing validators):

```python
    images: list[Image] = []

    @field_validator("images")
    @classmethod
    def _unique_images(cls, value: list[Image]) -> list[Image]:
        return _unique_image_ids(value)
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_models_images.py -v`
Expected: PASS.

- [ ] **Step 7: Confirm no regression in the existing model and content suites**

Run: `.venv/bin/python -m pytest tests/test_models.py tests/test_models_fonts.py tests/test_content.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add build/models.py tests/test_models_images.py
git commit -m "feat: Image model and world/story image declarations"
```

---

## Task 3: Prompt composition and export

**Files:**
- Create: `build/prompts.py`
- Modify: `tests/conftest.py` (add the `repo_with_images` fixture)
- Test: `tests/test_prompts.py`

- [ ] **Step 1: Add the shared fixture**

Append this fixture to `tests/conftest.py` (it builds a tiny worlds tree with images; it does not need content prose because prompt export reads only the YAML):

```python
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
```

(`textwrap` and `Path` are already imported at the top of `tests/conftest.py` from Plan 1.)

- [ ] **Step 2: Write the failing test**

`tests/test_prompts.py`:

```python
from build import prompts
from build.models import Image, World


def _world():
    return World.model_validate(
        {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
         "visual_style": "Soft storybook art."}
    )


def _image(**over):
    data = {"id": "cover", "role": "cover", "orientation": "portrait",
            "prompt": "A sleeping garden.",
            "alt": {"en-GB": "x", "es-ES": "y"}}
    data.update(over)
    return Image.model_validate(data)


def test_compose_includes_style_subject_and_no_text_rule():
    text = prompts.compose_prompt(_world(), _image(), {})
    assert "Soft storybook art." in text
    assert "A sleeping garden." in text
    assert "No text" in text


def test_compose_aspect_hint_matches_orientation():
    assert "3 to 4" in prompts.compose_prompt(_world(), _image(orientation="portrait"), {})
    assert "4 to 3" in prompts.compose_prompt(_world(), _image(orientation="landscape"), {})
    assert "1 to 1" in prompts.compose_prompt(_world(), _image(orientation="square"), {})


def test_compose_appends_canon_description_when_ref_resolves():
    from build.models import CanonEntry

    canon = {"mist-cat": CanonEntry.model_validate(
        {"id": "mist-cat", "kind": "creature",
         "names": {"en-GB": "Mist Cat", "es-ES": "Gato de Niebla"},
         "description": {"en-GB": "A gentle cat of fog.", "es-ES": "Un gato de niebla."}}
    )}
    text = prompts.compose_prompt(_world(), _image(canon_ref="mist-cat"), canon)
    assert "Mist Cat" in text and "gentle cat of fog" in text


def test_iter_image_prompts_covers_world_and_story(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    ids = {(e.world_id, e.story_id, e.image.id) for e in entries}
    assert ("w", None, "cover") in ids
    assert ("w", None, "beast") in ids
    assert ("w", "s", "cover") in ids
    assert ("w", "s", "scene-1") in ids
    beast = next(e for e in entries if e.image.id == "beast")
    assert "Test Beast" in beast.text  # canon_ref pulled the canon name


def test_filters_narrow_to_a_story(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images, world="w", story="s")
    owners = {(e.world_id, e.story_id) for e in entries}
    assert owners == {("w", "s")}  # world-level images excluded when a story is named


def test_markdown_has_fenced_prompt_and_alt(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    md = prompts.build_prompts_markdown(entries)
    assert "```" in md
    assert "Alt text:" in md
    assert "- en-GB:" in md
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_prompts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.prompts'`.

- [ ] **Step 4: Implement the module**

`build/prompts.py`:

```python
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_prompts.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add build/prompts.py tests/conftest.py tests/test_prompts.py
git commit -m "feat: compose and export image prompts from world and story YAML"
```

---

## Task 4: The `prompts` CLI subcommand

**Files:**
- Modify: `build/__main__.py`
- Test: `tests/test_cli_prompts.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli_prompts.py`:

```python
from build.__main__ import main


def test_prompts_prints_all(repo_with_images, capsys):
    code = main(["prompts", "--root", str(repo_with_images)])
    assert code == 0
    out = capsys.readouterr().out
    assert "# Image prompts" in out
    assert "w / cover" in out and "s / scene-1" in out


def test_prompts_writes_a_file(repo_with_images, tmp_path):
    out = tmp_path / "prompts.md"
    code = main(["prompts", "--root", str(repo_with_images), "--out", str(out)])
    assert code == 0
    assert out.read_text(encoding="utf-8").startswith("# Image prompts")


def test_prompts_filters_to_a_story(repo_with_images, capsys):
    code = main([
        "prompts", "--root", str(repo_with_images), "--world", "w", "--story", "s",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "s / cover" in out
    assert "## World: w" not in out  # world-level images excluded
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_prompts.py -v`
Expected: FAIL (argparse rejects the unknown `prompts` subcommand, raising SystemExit).

- [ ] **Step 3: Add the subparser**

In `build/__main__.py`, after the `render-guide` subparser block and before `args = parser.parse_args(argv)`, add:

```python
    prompts_parser = sub.add_parser("prompts", help="export image generation prompts")
    _add_root(prompts_parser)
    prompts_parser.add_argument("--world", default=None)
    prompts_parser.add_argument("--story", default=None)
    prompts_parser.add_argument("--out", type=Path, default=None)
```

- [ ] **Step 4: Add the command branch**

In `build/__main__.py`, add this before the final `return 2`:

```python
    if args.command == "prompts":
        from build import prompts as prompts_mod

        entries = prompts_mod.iter_image_prompts(
            args.root, world=args.world, story=args.story
        )
        if args.out is not None:
            prompts_mod.write_prompts(entries, args.out)
            print(f"wrote {args.out}")
        else:
            print(prompts_mod.build_prompts_markdown(entries))
        return 0
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cli_prompts.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add build/__main__.py tests/test_cli_prompts.py
git commit -m "feat: prompts CLI subcommand to export image prompts"
```

---

## Task 5: Image generation module

**Files:**
- Create: `build/generate.py`
- Test: `tests/test_generate.py`

- [ ] **Step 1: Write the failing test**

`tests/test_generate.py`:

```python
import base64
import types
from pathlib import Path

import pytest

from build import generate, prompts


class _FakeImages:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return types.SimpleNamespace(
            data=[types.SimpleNamespace(b64_json=self._payload)]
        )


class _FakeClient:
    def __init__(self, raw: bytes):
        self.images = _FakeImages(base64.b64encode(raw).decode())


def test_image_size_for_each_orientation():
    assert generate.image_size_for("portrait") == "1024x1536"
    assert generate.image_size_for("landscape") == "1536x1024"
    assert generate.image_size_for("square") == "1024x1024"


def test_target_path_for_world_and_story_images(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    world_cover = next(e for e in entries if e.story_id is None and e.image.id == "cover")
    story_scene = next(e for e in entries if e.story_id == "s" and e.image.id == "scene-1")
    assert generate.target_path(repo_with_images, world_cover) == (
        repo_with_images / "worlds" / "w" / "assets" / "cover.png"
    )
    assert generate.target_path(repo_with_images, story_scene) == (
        repo_with_images / "worlds" / "w" / "stories" / "s" / "assets" / "scene-1.png"
    )


def test_generate_image_writes_decoded_bytes(tmp_path):
    client = _FakeClient(b"PNGDATA")
    out = tmp_path / "a" / "cover.png"
    result = generate.generate_image("a prompt", "portrait", out, client=client)
    assert result == out
    assert out.read_bytes() == b"PNGDATA"
    assert client.images.calls[0]["size"] == "1024x1536"


def test_generate_all_skips_existing_unless_forced(repo_with_images):
    client = _FakeClient(b"PNGDATA")
    first = generate.generate_all(repo_with_images, client=client)
    assert len(first) == 4  # 2 world images + 2 story images
    again = generate.generate_all(repo_with_images, client=client)
    assert again == []  # all exist now, skipped
    forced = generate.generate_all(repo_with_images, force=True, client=client)
    assert len(forced) == 4
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_generate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.generate'`.

- [ ] **Step 3: Implement the module**

`build/generate.py`:

```python
"""Generate image files from composed prompts via an injectable OpenAI client.

The client is passed in so tests use a fake and nothing touches the network. The
CLI builds the real client only after confirming the API key is present. A
different image backend can replace make_client and generate_image later without
touching the schema or the prompts.
"""

import base64
from pathlib import Path

from build import prompts
from build.prompts import PromptEntry

_SIZES = {
    "portrait": "1024x1536",
    "landscape": "1536x1024",
    "square": "1024x1024",
}


def image_size_for(orientation: str) -> str:
    """Map an orientation to an OpenAI image size."""
    return _SIZES[orientation]


def target_path(root: Path, entry: PromptEntry) -> Path:
    """The assets path where an entry's PNG is written."""
    world_dir = root / "worlds" / entry.world_id
    if entry.story_id is None:
        return world_dir / "assets" / f"{entry.image.id}.png"
    return world_dir / "stories" / entry.story_id / "assets" / f"{entry.image.id}.png"


def make_client(api_key: str):
    """Construct a real OpenAI client. Imported lazily so the core needs no openai."""
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def generate_image(prompt: str, orientation: str, out_path: Path, *, client) -> Path:
    """Generate one image and write the PNG to out_path. Returns out_path."""
    response = client.images.generate(
        model="gpt-image-1", prompt=prompt, size=image_size_for(orientation), n=1
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return out_path


def generate_all(
    root: Path,
    *,
    world: str | None = None,
    story: str | None = None,
    force: bool = False,
    client,
) -> list[Path]:
    """Generate every declared image (filtered), skipping existing unless force."""
    written: list[Path] = []
    for entry in prompts.iter_image_prompts(root, world=world, story=story):
        out = target_path(root, entry)
        if out.exists() and not force:
            continue
        generate_image(entry.text, entry.image.orientation, out, client=client)
        written.append(out)
    return written
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_generate.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/generate.py tests/test_generate.py
git commit -m "feat: generate image files from prompts via an injectable client"
```

---

## Task 6: The `generate-images` CLI and the `images` extra

**Files:**
- Modify: `pyproject.toml`
- Modify: `build/__main__.py`
- Test: `tests/test_cli_generate.py`

- [ ] **Step 1: Add the optional dependency group**

In `pyproject.toml`, add an `images` group under `[project.optional-dependencies]` (beside `dev` and `render`):

```toml
images = [
    "openai>=1.0",
    "python-dotenv>=1.0",
]
```

- [ ] **Step 2: Install it**

Run:
```bash
.venv/bin/pip install -e ".[dev,render,images]"
```
Expected: install succeeds; `.venv/bin/python -c "import openai, dotenv"` exits 0.

- [ ] **Step 3: Write the failing test**

`tests/test_cli_generate.py`:

```python
import base64
import types

from build import generate
from build.__main__ import main


class _FakeImages:
    def generate(self, **kwargs):
        return types.SimpleNamespace(
            data=[types.SimpleNamespace(b64_json=base64.b64encode(b"PNG").decode())]
        )


class _FakeClient:
    images = _FakeImages()


def test_generate_images_writes_files(repo_with_images, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(generate, "make_client", lambda api_key: _FakeClient())
    code = main(["generate-images", "--root", str(repo_with_images)])
    assert code == 0
    assert (repo_with_images / "worlds" / "w" / "assets" / "cover.png").is_file()
    assert "4 image(s) written" in capsys.readouterr().out


def test_generate_images_skips_then_forces(repo_with_images, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(generate, "make_client", lambda api_key: _FakeClient())
    main(["generate-images", "--root", str(repo_with_images)])
    cover = repo_with_images / "worlds" / "w" / "assets" / "cover.png"
    mtime = cover.stat().st_mtime_ns
    # second run skips (file already exists), so the bytes are not rewritten
    main(["generate-images", "--root", str(repo_with_images)])
    assert cover.stat().st_mtime_ns == mtime
    # force regenerates
    main(["generate-images", "--root", str(repo_with_images), "--force"])
    assert cover.is_file()


def test_generate_images_missing_key_returns_one(repo_with_images, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code = main(["generate-images", "--root", str(repo_with_images)])
    assert code == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_generate.py -v`
Expected: FAIL (argparse rejects the unknown `generate-images` subcommand, raising SystemExit).

- [ ] **Step 5: Add the subparser**

In `build/__main__.py`, after the `prompts` subparser block and before `args = parser.parse_args(argv)`, add:

```python
    generate_parser = sub.add_parser("generate-images", help="generate image files")
    _add_root(generate_parser)
    generate_parser.add_argument("--world", default=None)
    generate_parser.add_argument("--story", default=None)
    generate_parser.add_argument("--force", action="store_true")
```

- [ ] **Step 6: Add the command branch**

In `build/__main__.py`, add this before the final `return 2`. The key is checked before any OpenAI import, and `.env` is loaded best-effort so python-dotenv is optional at runtime:

```python
    if args.command == "generate-images":
        import os

        try:
            from dotenv import load_dotenv

            load_dotenv(args.root / ".env")
        except ImportError:
            pass

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "OPENAI_API_KEY is not set. Put it in .env (see .env.example) "
                "or export it, then retry."
            )
            return 1

        from build import generate

        client = generate.make_client(api_key)
        written = generate.generate_all(
            args.root, world=args.world, story=args.story,
            force=args.force, client=client,
        )
        for path in written:
            print(f"wrote {path}")
        print(f"{len(written)} image(s) written")
        return 0
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cli_generate.py -v`
Expected: PASS.

- [ ] **Step 8: Run the whole suite**

Run: `.venv/bin/python -m pytest -q`
Expected: every test passes.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml build/__main__.py tests/test_cli_generate.py
git commit -m "feat: generate-images CLI and the images optional extra"
```

---

## Task 7: Lint warning for an unknown canon_ref

**Files:**
- Modify: `build/lint.py`
- Test: `tests/test_lint_images.py`

- [ ] **Step 1: Write the failing test**

`tests/test_lint_images.py`:

```python
from build import lint


def _set_story_image(sample_repo, canon_ref):
    story_yaml = (
        sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    )
    story_yaml.write_text(
        story_yaml.read_text(encoding="utf-8")
        + (
            "images:\n"
            "  - id: cover\n"
            "    role: cover\n"
            "    orientation: portrait\n"
            f"    canon_ref: {canon_ref}\n"
            "    prompt: A scene.\n"
            "    alt:\n"
            "      en-GB: A scene.\n"
            "      es-ES: Una escena.\n"
        ),
        encoding="utf-8",
    )


def test_unknown_canon_ref_is_a_warning(sample_repo):
    _set_story_image(sample_repo, "no-such-id")
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "warning" and "no-such-id" in i.message for i in issues
    )


def test_known_canon_ref_is_clean(sample_repo):
    _set_story_image(sample_repo, "mist-cat")
    issues = lint.lint_repo(sample_repo)
    assert not any(
        i.level == "warning" and "canon_ref" in i.message for i in issues
    )
```

(The `sample_repo` fixture from Plan 1 already includes a `mist-cat` canon entry, so the known-ref case is clean.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_lint_images.py -v`
Expected: FAIL: the unknown `canon_ref` raises no warning yet.

- [ ] **Step 3: Add a warning helper and thread canon ids through the story lint**

In `build/lint.py`, add the import of `content` is already present. Add the `_warning` helper after `_error`:

```python
def _warning(message: str, location: str) -> LintIssue:
    return LintIssue("warning", message, location)
```

Replace `_lint_world` so it loads the world, collects canon ids, checks world image refs, and passes the canon id set to `_lint_story`:

```python
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

    stories_dir = world_dir / "stories"
    if stories_dir.is_dir():
        for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
            issues.extend(_lint_story(world_id, story_dir, canon_ids))
    return issues
```

Add the shared image-ref check just above `_lint_story`:

```python
def _lint_image_refs(images, canon_ids: set[str], location: str) -> list[LintIssue]:
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
```

Update `_lint_story` to accept and use the canon ids (change its signature and add the image-ref check before the final return):

```python
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

    for code in locales.REQUIRED_LOCALES:
        for filename in _REQUIRED_CONTENT_FILES:
            path = story_dir / "content" / code / filename
            if not path.is_file():
                issues.append(
                    _error(f"missing content file {filename} for {code}", str(path))
                )
    return issues
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_lint_images.py tests/test_lint.py -v`
Expected: PASS (the new tests and the existing lint tests).

- [ ] **Step 5: Commit**

```bash
git add build/lint.py tests/test_lint_images.py
git commit -m "feat: lint warning when an image canon_ref names no canon entry"
```

---

## Task 8: Author the worked content (Floating Isles and Sleeping Garden)

This task adds real `visual_style` and image declarations to the existing world and story. It follows the content rules: prompts are the locale-neutral subject only, describe text-free art, and stay gentle and on-palette; alt text is written in en-GB then es-ES.

**Files:**
- Modify: `worlds/floating-isles/world.yaml`
- Modify: `worlds/floating-isles/stories/sleeping-garden/story.yaml`

- [ ] **Step 1: Add the world visual_style and images**

Append to `worlds/floating-isles/world.yaml` (after the existing `fonts:` block):

```yaml
visual_style: >
  Soft, warm children's storybook illustration in gentle watercolour and
  coloured-pencil texture, with a cosy, hopeful mood of quiet wonder. Use a
  palette of cream (#fef9ef), leaf green (#4ea24a), teal (#2bb3a3), rose
  (#d36fb0), sky blue (#3f8fd6), a golden path (#f2a93b) and soft purple
  (#8a6fd6). Rounded, friendly shapes, soft light, and plenty of calm space. A
  peaceful world of islands floating in a gentle sky, where magic only ever helps
  and nothing is ever frightening.
images:
  - id: cover
    role: cover
    orientation: portrait
    prompt: >
      A wide establishing view of the Floating Isles at golden hour: green
      islands drifting in a calm sky, the tallest crowned by a friendly little
      school tower beside a great walled garden, soft clouds passing below the
      islands, a few tiny birds. Welcoming and serene.
    alt:
      en-GB: The Floating Isles at golden hour, green islands in a calm sky with a little school tower and a walled garden on the tallest.
      es-ES: Las Islas Flotantes al atardecer dorado, islas verdes en un cielo tranquilo con una pequena torre de escuela y un jardin amurallado en la mas alta.
  - id: mist-cat
    role: portrait
    orientation: square
    canon_ref: mist-cat
    prompt: >
      A gentle cat made of soft grey mist, curled and friendly, with kind eyes
      and a faint sparkle of fog around it, sitting on a mossy stone. Cosy and
      reassuring.
    alt:
      en-GB: A gentle cat made of soft grey mist, sitting on a mossy stone.
      es-ES: Un gato amable hecho de niebla gris suave, sentado en una piedra con musgo.
  - id: lonely-sprite
    role: portrait
    orientation: square
    canon_ref: lonely-sprite
    prompt: >
      A small, shy sprite glowing with a soft warm light, sitting with its knees
      hugged, looking hopeful rather than sad, surrounded by gently waking
      flowers. Tender and kind, not scary at all.
    alt:
      en-GB: A small shy sprite glowing softly, hugging its knees among waking flowers.
      es-ES: Un pequeno duende timido que brilla con suavidad, abrazandose las rodillas entre flores que despiertan.
```

- [ ] **Step 2: Add the story images**

Append to `worlds/floating-isles/stories/sleeping-garden/story.yaml`:

```yaml
images:
  - id: cover
    role: cover
    orientation: portrait
    prompt: >
      A great walled garden on a floating island at dawn, gently asleep: flowers
      with closed petals, a still grey fountain, and a soft golden path winding
      from a little gate toward the garden's heart, under a calm pale sky with
      clouds drifting below the island's edge. Leave calm space near the top.
    alt:
      en-GB: A sleeping walled garden on a floating island at dawn, with closed flowers, a still fountain and a winding golden path.
      es-ES: Un jardin amurallado dormido en una isla flotante al amanecer, con flores cerradas, una fuente quieta y un camino dorado serpenteante.
  - id: scene-vine-gate
    role: scene
    orientation: landscape
    canon_ref: vine-gate
    prompt: >
      A tall garden gate woven shut by a big soft knot of green leaves and vines,
      with the gentle grey Mist Cat watching nearby, and the first sleepy flower
      beginning to open one petal. Inviting, not threatening.
    alt:
      en-GB: A tall gate tied shut with a knot of green vines, the Mist Cat watching nearby.
      es-ES: Una puerta alta cerrada con un nudo de enredaderas verdes, con el Gato de Niebla observando cerca.
  - id: scene-flower-bed
    role: scene
    orientation: landscape
    canon_ref: flower-bed
    prompt: >
      A flower bed with four large friendly flowers in yellow, blue, red and
      white, a little out of order, with a tiny humming voice suggested by soft
      musical sparkles in the air. Bright and playful.
    alt:
      en-GB: A flower bed of four big flowers in yellow, blue, red and white, slightly out of order.
      es-ES: Un cantero con cuatro flores grandes amarilla, azul, roja y blanca, un poco desordenadas.
  - id: scene-talking-fountain
    role: scene
    orientation: landscape
    canon_ref: talking-fountain
    prompt: >
      A stone fountain that has gone quiet and a little sad, its water sitting
      still, beginning to sparkle and rise again as if cheered up. Warm and
      hopeful.
    alt:
      en-GB: A quiet stone fountain beginning to sparkle and flow again.
      es-ES: Una fuente de piedra callada que empieza a brillar y a manar de nuevo.
  - id: scene-garden-heart
    role: scene
    orientation: landscape
    canon_ref: garden-heart
    prompt: >
      The heart of the garden waking all at once: a small shy sprite smiling as
      two little mages offer friendship, flowers opening, the fountain singing,
      and warm golden light spreading across the whole garden. Joyful and gentle.
    alt:
      en-GB: The garden's heart waking, the shy sprite smiling as two little mages offer friendship, flowers opening in golden light.
      es-ES: El corazon del jardin despertando, el duende timido sonrie mientras dos pequenos magos le ofrecen amistad, las flores se abren bajo una luz dorada.
```

- [ ] **Step 3: Validate and lint the content**

Run:
```bash
.venv/bin/python -m build validate --root .
.venv/bin/python -m build lint --root .
```
Expected: `OK: validated 1 story file(s)` and `lint clean` (every `canon_ref` above names a real canon entry).

- [ ] **Step 4: Preview the composed prompts**

Run:
```bash
.venv/bin/python -m build prompts --root . --world floating-isles
```
Expected: the eight composed prompts (world cover, mist-cat, lonely-sprite, story cover, four scenes), each in a fenced block with the world style preamble, the subject, the no-text rule, and (for the portraits and scenes) the canon name and description. Skim one to confirm it reads well.

- [ ] **Step 5: Commit**

```bash
git add worlds/floating-isles/world.yaml \
        worlds/floating-isles/stories/sleeping-garden/story.yaml
git commit -m "content: art prompts for the Floating Isles and the Sleeping Garden"
```

- [ ] **Step 6 (OPTIONAL, costs OpenAI credit): generate the real art**

Only if you want the PNGs now. With your key in `.env`:
```bash
.venv/bin/python -m build generate-images --root . --world floating-isles
```
Expected: eight PNGs written under the world `assets/` and the story `assets/`. Eyeball a couple, then commit the chosen art:
```bash
git add worlds/floating-isles/assets/*.png \
        worlds/floating-isles/stories/sleeping-garden/assets/*.png
git commit -m "art: generated illustrations for the Floating Isles and the Sleeping Garden"
```

---

## Task 9: Documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`
- Modify: `.claude/skills/authoring-story-content/SKILL.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add an Images section to the main spec**

In `docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`, add a new section after section 9 (Canon registry and shared lexicon):

```markdown
## 9a. Images and art prompts

Worlds and stories may declare illustrations in their YAML. Each image has an `id`
(unique within its owner), a `role` (cover, scene, portrait, motif), an
`orientation` (portrait, landscape, square), a `prompt` (the locale-neutral
subject), localized `alt` text, and an optional `canon_ref`. The world carries one
`visual_style` preamble shared by all its images.

Art is locale-neutral and free of any in-image text, so one image serves every
language (the same rule the maps follow); only `alt` is localized. `python -m build
prompts` exports copy-paste-ready prompts (style preamble plus subject plus a
technical line plus any canon description). `python -m build generate-images` turns
those prompts into PNGs via the OpenAI Images API. Generated art lives beside the
map under `assets/` and is committed as a build input. Embedding images into the
kit PDFs is a later step. The full design is at
`docs/superpowers/specs/2026-06-02-images-and-art-prompts-design.md`.
```

- [ ] **Step 2: Add image authoring rules to the authoring skill**

In `.claude/skills/authoring-story-content/SKILL.md`, add a section (near the end, before any closing notes):

```markdown
## Images and art prompts

When authoring a world, write its `visual_style` (one paragraph of art direction:
medium, mood, the world palette hexes, "nothing scary") and any world-level images
(a cover, key portraits). When authoring a story, write its `images`: a cover and a
scene per major beat or stop.

Rules for every image:

- The `prompt` is the subject only, in English, locale-neutral. The world's
  `visual_style` and a technical line are added automatically at export, so do not
  repeat the style in each prompt.
- The art must contain no text, letters, words, or numbers (so one image serves
  every language, like the maps). Never ask for captions or titles in the image.
- Keep it gentle and on-palette, in the no-lose, clever-and-kind spirit: nothing
  frightening, no real violence, friendly faces.
- Set `canon_ref` to the canon id when an image depicts a named place, character,
  or creature, so the export adds that entry's description and the art stays
  consistent with the bible.
- Write `alt` text in en-GB first, then es-ES, like all other prose, following the
  en-GB and es-ES conventions (British spelling, peninsular Spanish with accents).
```

- [ ] **Step 3: Document the feature in CLAUDE.md**

In `CLAUDE.md`, under the Commands section, add the two commands beside the others:

```bash
.venv/bin/python -m build prompts --root .            # export image generation prompts
.venv/bin/python -m build generate-images --root .    # generate PNGs (needs OPENAI_API_KEY in .env)
```

And add a short architecture bullet after the fonts/visuals notes:

```markdown
- **`visuals.py` is the image vocabulary** (roles, orientations). Worlds and
  stories declare illustrations in YAML (`images:`, plus a world `visual_style`).
  `prompts.py` composes copy-paste prompts (locale-neutral, text-free art; only
  `alt` is localized) and `generate.py` turns them into PNGs in `assets/` via the
  OpenAI Images API (the optional `images` extra: `pip install -e ".[images]"`, key
  from `.env`). Embedding images into PDFs is a later step.
```

- [ ] **Step 4: Run the whole suite as a final check**

Run: `.venv/bin/python -m pytest -q`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md \
        .claude/skills/authoring-story-content/SKILL.md CLAUDE.md
git commit -m "docs: document images and art prompts in spec, skill, and CLAUDE.md"
```

---

## Self-review

**Spec coverage (against `2026-06-02-images-and-art-prompts-design.md`):**
- Vocabulary (`visuals.py`): Task 1. Covered.
- `Image` model, `World.visual_style`, `World.images`, `Story.images`, role and
  orientation validation, alt locale coverage, id uniqueness: Task 2. Covered.
  `canon_ref` non-empty check is in Task 2; its existence check is the Task 7 lint
  warning, as the spec specifies.
- Prompt composition and export (`compose_prompt`, `iter_image_prompts`,
  `PromptEntry`, `build_prompts_markdown`, `write_prompts`): Task 3. Covered.
- `prompts` CLI with `--world`/`--story`/`--out`: Task 4. Covered.
- Generation (`image_size_for`, `target_path`, `generate_image`, `generate_all`,
  `make_client`): Task 5. Covered.
- `generate-images` CLI, `OPENAI_API_KEY` check before any API import, `.env`
  load, `--force`, the `images` extra: Task 6. Covered.
- canon_ref lint warning: Task 7. Covered.
- Worked content for Floating Isles and Sleeping Garden: Task 8. Covered, and it
  doubles as the end-to-end check (validate, lint, prompts preview, optional real
  generation). Generated PNGs committed as build assets: Task 8 Step 6.
- Authoring workflow integration (spec section, authoring skill): Task 9. Covered.

**Items intentionally NOT in this plan (deferred per the spec):** embedding images
into the kit PDFs, a lint that every declared image has a file on disk, and image
backends other than OpenAI. Each is named in the spec's Future work.

**Placeholder scan:** every code step contains complete, runnable code. Task 8
Step 6 is labelled OPTIONAL because it spends API credit; everything else is
deterministic and offline (the generator is tested with an injected fake client).

**Type and name consistency across tasks:** `visuals.IMAGE_ROLES/ORIENTATIONS`;
`models.Image` (fields `id/role/orientation/prompt/alt/canon_ref`),
`World.visual_style/images`, `Story.images`, `_unique_image_ids`;
`prompts.PromptEntry` (`world_id/story_id/image/text`), `prompts.compose_prompt`,
`prompts.iter_image_prompts(root, world, story)`, `prompts.build_prompts_markdown`,
`prompts.write_prompts`; `generate.image_size_for`, `generate.target_path`,
`generate.generate_image(..., *, client)`, `generate.generate_all(..., *, client)`,
`generate.make_client`. The CLI calls these exact names, and `generate_all` reuses
`prompts.iter_image_prompts`, so what `generate-images` produces matches what
`prompts` previews.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-images-and-art-prompts.md`.

Two execution options:

1. **Subagent-Driven (recommended):** a fresh subagent per task, with two-stage review between tasks and fast iteration.
2. **Inline Execution:** execute the tasks in this session with checkpoints for review.

Which approach?
