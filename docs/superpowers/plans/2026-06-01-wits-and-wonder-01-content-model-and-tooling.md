# Wits & Wonder, Plan 1: Content model and tooling

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pure-Python foundation of Wits & Wonder: the content schema, locale and tag vocabularies, dice bands, content loaders, the lint checks, and catalog generation, all driven by YAML content and fully testable without rendering a single PDF.

**Architecture:** Content lives as YAML and Markdown on disk (worlds, stories, canon, lexicon). A small Python package named `build` loads and validates that content into typed models (pydantic v2), runs lint checks over it, and generates `catalog.md`. Layout and PDF rendering are deliberately out of scope for this plan; they arrive in Plan 2 and import these same models. This keeps the data layer correct and well tested before any pixel is drawn.

**Tech Stack:** Python 3.11+, pydantic v2 (schema validation), PyYAML (parsing), pytest (tests). Rendering dependencies (reportlab, cairosvg, pypdf) are added in Plan 2, not here.

---

## The plan set and sequencing

This spec covers independent subsystems, so it is split into a sequence of plans. Each one produces working, testable software on its own. This document is **Plan 1**. The others will be written as their own documents once the interfaces they depend on are real.

1. **Plan 1: Content model and tooling** (this document). The data layer: schema, vocabularies, dice bands, loaders, lint, catalog. Delivers three working CLI commands (`validate`, `lint`, `catalog`) over real content, no PDFs. Depends on nothing.
2. **Plan 2: PDF build pipeline.** Templates, Unicode font embedding, the layout-only builders that take `(world, story, locale, reading_level)`, page merge, and the standalone Guide build. Delivers built kit PDFs in `dist/`. Depends on Plan 1's models.
3. **Plan 3: The Floating Isles and The Sleeping Garden content.** World lore, canon population, the migrated story in en-GB then es-ES, simple and rich narration, three character sheets wired through the templates. Depends on Plans 1 and 2, and uses the `authoring-story-content` skill for every prose and YAML file.
4. **Plan 4: Greek-myth world and one story.** A second world that stress-tests heroic peril, an older audience, and a non-magic ruleset. Depends on Plans 1 and 2, uses the authoring skill.
5. **Plan 5: Guide for the Grown-Up.** The generic newcomer guide content (en-GB then es-ES) and the rules-page callout wiring. Content depends on the authoring skill; its standalone PDF build is delivered in Plan 2, so Plan 5 is mostly authoring plus a callout check.

**Deferred (not scheduled into a plan yet): a path-scoped spelling lint.** A check that flags American spellings inside `**/en-GB/**` and Latin-American turns of phrase inside `**/es-ES/**`. It is deferred on purpose: it is only meaningful once locale content folders exist (Plans 3 to 5), and it must be path-scoped so it never fires on a future `en-US` folder. A stub interface for it is included as the final task of this plan so the seam exists, but the rule set is not implemented here.

---

## File structure (Plan 1)

```
pyproject.toml                 # package metadata, deps, pytest config
build/                         # the Python package (source, not build artifacts; output goes to dist/)
  __init__.py
  locales.py                   # canonical/synced locale codes and helpers
  tags.py                      # age tiers, skills, peril, reading levels and their tier mapping
  dice.py                      # difficulty bands and the band-to-dice threshold tables
  models.py                    # pydantic models: World, Story, CanonEntry, LexiconTerm
  content.py                   # YAML loaders that return typed models
  lint.py                      # lint checks over canon, lexicon, stories
  catalog.py                   # generate catalog.md from every story.yaml
  spelling.py                  # DEFERRED stub: path-scoped en-GB/es-ES spelling lint seam
  __main__.py                  # CLI: python -m build {validate,lint,catalog}
tests/
  __init__.py
  conftest.py                  # shared fixture: a tiny valid world on tmp_path
  test_locales.py
  test_tags.py
  test_dice.py
  test_models.py
  test_content.py
  test_lint.py
  test_catalog.py
  test_cli.py
  test_spelling.py
```

A note on the package name: the spec's `build/` directory is the natural home for the toolchain. We use it as an importable package (`from build.models import Story`). Build output still goes to `dist/` (per the spec and the existing `.gitignore`), so there is no clash with artifacts. If a future `pip install build` (the PEP 517 frontend) is ever needed in the same environment, revisit this; it is not needed by this project.

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `build/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_scaffold.py`
- Modify: `.gitignore` (add the egg-info and build-tool caches)

- [ ] **Step 1: Write the failing test**

`tests/test_scaffold.py`:

```python
def test_package_imports_and_has_version():
    import build

    assert hasattr(build, "__version__")
    assert isinstance(build.__version__, str)
    assert build.__version__
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_scaffold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build'` (or a collection error), because the package does not exist yet.

- [ ] **Step 3: Create the package and project metadata**

`build/__init__.py`:

```python
"""Wits & Wonder content toolchain (layout-only build comes in Plan 2)."""

__version__ = "0.1.0"
```

`tests/__init__.py`: leave it empty (a single newline).

`pyproject.toml`:

```toml
[project]
name = "wits-and-wonder"
version = "0.1.0"
description = "Printable cooperative story-kit library: content model and build toolchain"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.6",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.setuptools.packages.find]
include = ["build*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 4: Install the package in editable mode with dev extras**

Run:
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```
Expected: install succeeds and `pip show wits-and-wonder` lists the package.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest tests/test_scaffold.py -v`
Expected: PASS.

- [ ] **Step 6: Extend `.gitignore`**

Append these lines to `.gitignore` (the file already ignores `dist/`, `__pycache__/`, and `.venv/`):

```
# Packaging metadata
*.egg-info/
.eggs/
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml build/__init__.py tests/__init__.py tests/test_scaffold.py .gitignore
git commit -m "chore: scaffold content toolchain package and pytest"
```

---

## Task 2: Locale vocabulary

**Files:**
- Create: `build/locales.py`
- Test: `tests/test_locales.py`

- [ ] **Step 1: Write the failing test**

`tests/test_locales.py`:

```python
from build import locales


def test_canonical_and_required_locales():
    assert locales.CANONICAL_LOCALE == "en-GB"
    assert locales.REQUIRED_LOCALES == ("en-GB", "es-ES")


def test_missing_locales_reports_absent_required_codes():
    mapping = {"en-GB": "The Sleeping Garden"}
    assert locales.missing_locales(mapping) == ("es-ES",)


def test_missing_locales_empty_when_all_present():
    mapping = {"en-GB": "x", "es-ES": "y"}
    assert locales.missing_locales(mapping) == ()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_locales.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.locales'`.

- [ ] **Step 3: Implement the module**

`build/locales.py`:

```python
"""Locale codes. British English is canonical; Spanish from Spain is synced.

US English, Latin American Spanish, and other locales are separate languages
added later, each keyed by its own explicit code (like pt-PT versus pt-BR).
"""

from collections.abc import Mapping

CANONICAL_LOCALE = "en-GB"
SYNCED_LOCALES = ("es-ES",)
REQUIRED_LOCALES = (CANONICAL_LOCALE, *SYNCED_LOCALES)


def missing_locales(mapping: Mapping[str, object]) -> tuple[str, ...]:
    """Return the required locale codes absent (or blank) in a per-locale map."""
    return tuple(
        code
        for code in REQUIRED_LOCALES
        if not str(mapping.get(code, "")).strip()
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_locales.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/locales.py tests/test_locales.py
git commit -m "feat: locale vocabulary (en-GB canonical, es-ES synced)"
```

---

## Task 3: Tag vocabularies and reading levels

**Files:**
- Create: `build/tags.py`
- Test: `tests/test_tags.py`

- [ ] **Step 1: Write the failing test**

`tests/test_tags.py`:

```python
from build import tags


def test_vocabularies_match_spec():
    assert tags.AGE_TIERS == ("early", "young", "older")
    assert tags.PERILS == ("gentle", "mild", "heroic")
    assert tags.READING_LEVELS == ("simple", "rich")
    assert set(tags.SKILLS) == {
        "vocabulary", "logic", "maths", "memory",
        "spatial", "observation", "social-emotional",
    }


def test_reading_level_covers_expected_tiers():
    assert tags.tiers_for_reading_level("simple") == ("early", "young")
    assert tags.tiers_for_reading_level("rich") == ("older",)


def test_reading_level_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        tags.tiers_for_reading_level("medium")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_tags.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.tags'`.

- [ ] **Step 3: Implement the module**

`build/tags.py`:

```python
"""Tag vocabularies and the reading-level to age-tier mapping (spec sections 6 and 8)."""

AGE_TIERS = ("early", "young", "older")
SKILLS = (
    "vocabulary",
    "logic",
    "maths",
    "memory",
    "spatial",
    "observation",
    "social-emotional",
)
PERILS = ("gentle", "mild", "heroic")
READING_LEVELS = ("simple", "rich")

_READING_LEVEL_TIERS = {
    "simple": ("early", "young"),
    "rich": ("older",),
}


def tiers_for_reading_level(level: str) -> tuple[str, ...]:
    """Age tiers a reading level serves. Raises ValueError on an unknown level."""
    try:
        return _READING_LEVEL_TIERS[level]
    except KeyError:
        raise ValueError(f"unknown reading level: {level!r}") from None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_tags.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/tags.py tests/test_tags.py
git commit -m "feat: tag vocabularies and reading-level tier mapping"
```

---

## Task 4: Dice bands

**Files:**
- Create: `build/dice.py`
- Test: `tests/test_dice.py`

- [ ] **Step 1: Write the failing test**

`tests/test_dice.py`:

```python
from build import dice


def test_bands_and_floor():
    assert dice.BANDS == ("Easy", "Normal", "Hard")
    assert dice.DICE_FLOOR == "1d6"


def test_thresholds_for_known_sets_match_spec_table():
    assert dice.thresholds_for("1d6") == {"Easy": 3, "Normal": 4, "Hard": 5}
    assert dice.thresholds_for("d20-set") == {"Easy": 6, "Normal": 10, "Hard": 14}


def test_every_band_has_a_threshold_for_the_floor():
    floor = dice.thresholds_for(dice.DICE_FLOOR)
    assert set(floor) == set(dice.BANDS)


def test_thresholds_for_unknown_set_raises():
    import pytest

    with pytest.raises(KeyError):
        dice.thresholds_for("d4-only")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_dice.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.dice'`.

- [ ] **Step 3: Implement the module**

`build/dice.py`:

```python
"""Difficulty bands and their thresholds per dice set (spec section 7).

Rules and narration never name a die; they use bands. A single in-kit table
maps bands onto whatever dice a family owns. Every story is playable with 1d6.
"""

BANDS = ("Easy", "Normal", "Hard")
DICE_FLOOR = "1d6"

_BAND_THRESHOLDS = {
    "1d6": {"Easy": 3, "Normal": 4, "Hard": 5},
    "d20-set": {"Easy": 6, "Normal": 10, "Hard": 14},
}


def thresholds_for(dice_set: str) -> dict[str, int]:
    """Per-band minimum roll for a dice set. Raises KeyError if unknown."""
    return dict(_BAND_THRESHOLDS[dice_set])


def known_dice_sets() -> tuple[str, ...]:
    return tuple(_BAND_THRESHOLDS)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_dice.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/dice.py tests/test_dice.py
git commit -m "feat: difficulty bands and dice threshold tables"
```

---

## Task 5: Content models (Story, CanonEntry, LexiconTerm, World)

**Files:**
- Create: `build/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from build.models import Story, CanonEntry


def _valid_story_data():
    return {
        "world": "floating-isles",
        "id": "sleeping-garden",
        "title": {"en-GB": "The Sleeping Garden", "es-ES": "El Jardin Dormido"},
        "age": {"recommended": "young", "also_works_for": ["early", "older"]},
        "skills": ["vocabulary", "logic", "social-emotional"],
        "peril": "gentle",
        "adult_gm": True,
        "dice": {"minimum": "1d6", "recommended": "d20-set"},
        "players": {"min": 2, "max": 2},
        "play_time_minutes": 30,
    }


def test_valid_story_parses():
    story = Story.model_validate(_valid_story_data())
    assert story.id == "sleeping-garden"
    assert story.title["en-GB"] == "The Sleeping Garden"


def test_story_missing_synced_locale_in_title_fails():
    data = _valid_story_data()
    data["title"] = {"en-GB": "The Sleeping Garden"}
    with pytest.raises(ValidationError) as err:
        Story.model_validate(data)
    assert "es-ES" in str(err.value)


def test_story_unknown_peril_fails():
    data = _valid_story_data()
    data["peril"] = "terrifying"
    with pytest.raises(ValidationError):
        Story.model_validate(data)


def test_story_dice_floor_must_be_1d6():
    data = _valid_story_data()
    data["dice"]["minimum"] = "d20"
    with pytest.raises(ValidationError) as err:
        Story.model_validate(data)
    assert "1d6" in str(err.value)


def test_canon_entry_requires_both_locale_names():
    with pytest.raises(ValidationError) as err:
        CanonEntry.model_validate(
            {"id": "mist-cat", "names": {"en-GB": "Mist Cat"}, "kind": "creature"}
        )
    assert "es-ES" in str(err.value)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.models'`.

- [ ] **Step 3: Implement the models**

`build/models.py`:

```python
"""Typed content models mirroring the spec schema (sections 6 and 9)."""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from build import dice, locales, tags

_CANON_KINDS = ("place", "character", "creature", "item", "term")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _require_locales(mapping: dict[str, str], field_name: str) -> None:
    missing = locales.missing_locales(mapping)
    if missing:
        raise ValueError(f"{field_name} is missing locale(s): {', '.join(missing)}")


class Age(_Strict):
    recommended: str
    also_works_for: list[str] = []

    @field_validator("recommended")
    @classmethod
    def _known_recommended(cls, value: str) -> str:
        if value not in tags.AGE_TIERS:
            raise ValueError(f"recommended age {value!r} not in {tags.AGE_TIERS}")
        return value

    @field_validator("also_works_for")
    @classmethod
    def _known_also(cls, value: list[str]) -> list[str]:
        bad = [tier for tier in value if tier not in tags.AGE_TIERS]
        if bad:
            raise ValueError(f"also_works_for has unknown tiers: {bad}")
        return value


class Dice(_Strict):
    minimum: str
    recommended: str | None = None

    @field_validator("minimum")
    @classmethod
    def _floor_is_d6(cls, value: str) -> str:
        if value != dice.DICE_FLOOR:
            raise ValueError(
                f"dice.minimum must be {dice.DICE_FLOOR!r} so every story is "
                f"playable with a single d6; got {value!r}"
            )
        return value


class Players(_Strict):
    min: int
    max: int

    @model_validator(mode="after")
    def _min_le_max(self) -> "Players":
        if self.min > self.max:
            raise ValueError("players.min cannot exceed players.max")
        return self


class Story(_Strict):
    world: str
    id: str
    title: dict[str, str]
    age: Age
    skills: list[str]
    peril: str
    adult_gm: bool
    dice: Dice
    players: Players
    play_time_minutes: int

    @field_validator("title")
    @classmethod
    def _title_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "title")
        return value

    @field_validator("skills")
    @classmethod
    def _known_skills(cls, value: list[str]) -> list[str]:
        bad = [s for s in value if s not in tags.SKILLS]
        if bad:
            raise ValueError(f"unknown skills: {bad}")
        return value

    @field_validator("peril")
    @classmethod
    def _known_peril(cls, value: str) -> str:
        if value not in tags.PERILS:
            raise ValueError(f"peril {value!r} not in {tags.PERILS}")
        return value


class CanonEntry(_Strict):
    id: str
    names: dict[str, str]
    kind: str
    disposition: str | None = None
    description: dict[str, str] | None = None
    first_seen: str | None = None

    @field_validator("kind")
    @classmethod
    def _known_kind(cls, value: str) -> str:
        if value not in _CANON_KINDS:
            raise ValueError(f"kind {value!r} not in {_CANON_KINDS}")
        return value

    @field_validator("names")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "names")
        return value


class LexiconTerm(_Strict):
    id: str
    names: dict[str, str]

    @field_validator("names")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "names")
        return value


class World(_Strict):
    id: str
    name: dict[str, str]
    tone: str | None = None
    palette: list[str] = []
    lore_summary: dict[str, str] | None = None

    @field_validator("name")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "name")
        return value
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/models.py tests/test_models.py
git commit -m "feat: pydantic content models with locale and vocabulary validation"
```

---

## Task 6: Content loaders and a shared test fixture

**Files:**
- Create: `build/content.py`
- Create: `tests/conftest.py`
- Test: `tests/test_content.py`

- [ ] **Step 1: Write the shared fixture**

`tests/conftest.py` builds a tiny but valid world on a temporary path so loader, lint, and catalog tests share one realistic tree:

```python
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
                     "puzzles.md", "idea-bank.md"):
            (content_dir / name).write_text("placeholder\n", encoding="utf-8")

    lexicon_dir = tmp_path / "lexicon"
    lexicon_dir.mkdir()
    (lexicon_dir / "terms.yaml").write_text(textwrap.dedent("""
        - id: game-master
          names:
            en-GB: Game Master
            es-ES: Guia del Juego
    """).lstrip(), encoding="utf-8")

    return tmp_path
```

- [ ] **Step 2: Write the failing test**

`tests/test_content.py`:

```python
from build import content
from build.models import CanonEntry, Story, World


def test_load_world(sample_repo):
    world = content.load_world(sample_repo / "worlds" / "floating-isles" / "world.yaml")
    assert isinstance(world, World)
    assert world.name["es-ES"] == "Las Islas Flotantes"


def test_load_story(sample_repo):
    path = sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    story = content.load_story(path)
    assert isinstance(story, Story)
    assert story.id == "sleeping-garden"


def test_load_canon_merges_category_files(sample_repo):
    entries = content.load_canon(sample_repo / "worlds" / "floating-isles" / "canon")
    assert all(isinstance(e, CanonEntry) for e in entries)
    assert {e.id for e in entries} == {"mist-cat"}


def test_iter_stories_finds_all(sample_repo):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    assert [s.id for s in stories] == ["sleeping-garden"]
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest tests/test_content.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.content'`.

- [ ] **Step 4: Implement the loaders**

`build/content.py`:

```python
"""Load YAML content into typed models."""

from collections.abc import Iterator
from pathlib import Path

import yaml

from build.models import CanonEntry, LexiconTerm, Story, World


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


def load_lexicon(path: Path) -> list[LexiconTerm]:
    rows = _load_yaml(path) or []
    return [LexiconTerm.model_validate(row) for row in rows]


def iter_stories(worlds_dir: Path) -> Iterator[Story]:
    for story_yaml in sorted(worlds_dir.glob("*/stories/*/story.yaml")):
        yield load_story(story_yaml)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest tests/test_content.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add build/content.py tests/conftest.py tests/test_content.py
git commit -m "feat: YAML content loaders and shared sample-repo fixture"
```

---

## Task 7: Lint checks

The spec's binding is "authoritative plus lint" (section 9). This task implements the tractable, deterministic half: structural integrity of canon and stories. The fuzzy half (scanning prose for names absent from canon) is genuinely hard to do well and is left to the deferred spelling-style work; this lint instead guarantees that canon itself is complete and consistent and that every story is well formed with its required content files present.

**Files:**
- Create: `build/lint.py`
- Test: `tests/test_lint.py`

- [ ] **Step 1: Write the failing test**

`tests/test_lint.py`:

```python
from build import lint


def test_clean_repo_has_no_errors(sample_repo):
    issues = lint.lint_repo(sample_repo)
    assert [i for i in issues if i.level == "error"] == []


def test_duplicate_canon_id_is_an_error(sample_repo):
    canon = sample_repo / "worlds" / "floating-isles" / "canon" / "extra.yaml"
    canon.write_text(
        "- id: mist-cat\n"
        "  names: {en-GB: Mist Cat, es-ES: Gato de Niebla}\n"
        "  kind: creature\n",
        encoding="utf-8",
    )
    issues = lint.lint_repo(sample_repo)
    assert any(i.level == "error" and "mist-cat" in i.message for i in issues)


def test_missing_required_content_file_is_an_error(sample_repo):
    target = (
        sample_repo
        / "worlds/floating-isles/stories/sleeping-garden/content/es-ES/rules.md"
    )
    target.unlink()
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "error" and "rules.md" in i.message and "es-ES" in i.message
        for i in issues
    )


def test_story_world_mismatch_is_an_error(sample_repo):
    story_yaml = (
        sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    )
    text = story_yaml.read_text(encoding="utf-8").replace(
        "world: floating-isles", "world: greek-myth"
    )
    story_yaml.write_text(text, encoding="utf-8")
    issues = lint.lint_repo(sample_repo)
    assert any(i.level == "error" and "world" in i.message.lower() for i in issues)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_lint.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.lint'`.

- [ ] **Step 3: Implement the lint**

`build/lint.py`:

```python
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
        seen: dict[str, str] = {}
        for yaml_path in sorted(canon_dir.glob("*.yaml")):
            try:
                entries = content.load_canon(canon_dir)
            except ValidationError as exc:
                issues.append(_error(f"canon failed validation: {exc}", str(yaml_path)))
                continue
            for entry in entries:
                if entry.id in seen:
                    issues.append(
                        _error(
                            f"duplicate canon id {entry.id!r}",
                            f"{canon_dir} (also in {seen[entry.id]})",
                        )
                    )
                else:
                    seen[entry.id] = str(yaml_path)
            break  # load_canon already merges every file; one pass is enough

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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_lint.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/lint.py tests/test_lint.py
git commit -m "feat: structural lint for canon, stories, and content files"
```

---

## Task 8: Catalog generation

**Files:**
- Create: `build/catalog.py`
- Test: `tests/test_catalog.py`

- [ ] **Step 1: Write the failing test**

`tests/test_catalog.py`:

```python
from build import catalog, content


def test_catalog_lists_story_with_tags(sample_repo):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    markdown = catalog.build_catalog_markdown(stories)
    assert "| World | Title | Age | Skills | Peril | Dice | Players | Time |" in markdown
    assert "floating-isles" in markdown
    assert "The Sleeping Garden" in markdown
    assert "gentle" in markdown
    assert "30 min" in markdown


def test_write_catalog_creates_file(sample_repo, tmp_path):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    out = tmp_path / "catalog.md"
    catalog.write_catalog(stories, out)
    assert out.read_text(encoding="utf-8").startswith("# Catalog")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_catalog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.catalog'`.

- [ ] **Step 3: Implement the catalog**

`build/catalog.py`:

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_catalog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/catalog.py tests/test_catalog.py
git commit -m "feat: generate catalog.md from story metadata"
```

---

## Task 9: CLI (validate, lint, catalog)

**Files:**
- Create: `build/__main__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:

```python
from build.__main__ import main


def test_validate_ok_returns_zero(sample_repo, capsys):
    code = main(["validate", "--root", str(sample_repo)])
    assert code == 0
    assert "OK" in capsys.readouterr().out


def test_lint_reports_errors_with_nonzero_exit(sample_repo, capsys):
    (sample_repo / "worlds/floating-isles/stories/sleeping-garden/content/es-ES/rules.md").unlink()
    code = main(["lint", "--root", str(sample_repo)])
    assert code == 1
    assert "rules.md" in capsys.readouterr().out


def test_catalog_writes_file(sample_repo):
    out = sample_repo / "catalog.md"
    code = main(["catalog", "--root", str(sample_repo), "--out", str(out)])
    assert code == 0
    assert out.is_file()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.__main__'`.

- [ ] **Step 3: Implement the CLI**

`build/__main__.py`:

```python
"""Command line: python -m build {validate,lint,catalog}."""

import argparse
import sys
from pathlib import Path

from build import catalog, content, lint


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=Path("."), help="repo root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_root(sub.add_parser("validate", help="load and validate all content"))
    _add_root(sub.add_parser("lint", help="run structural lint"))
    catalog_parser = sub.add_parser("catalog", help="generate catalog.md")
    _add_root(catalog_parser)
    catalog_parser.add_argument("--out", type=Path, default=Path("catalog.md"))

    args = parser.parse_args(argv)

    if args.command == "validate":
        stories = list(content.iter_stories(args.root / "worlds"))
        print(f"OK: validated {len(stories)} story file(s)")
        return 0

    if args.command == "lint":
        issues = lint.lint_repo(args.root)
        for issue in issues:
            print(f"[{issue.level}] {issue.message} ({issue.location})")
        errors = [i for i in issues if i.level == "error"]
        if errors:
            print(f"{len(errors)} error(s)")
            return 1
        print("lint clean")
        return 0

    if args.command == "catalog":
        stories = list(content.iter_stories(args.root / "worlds"))
        catalog.write_catalog(stories, args.out)
        print(f"wrote {args.out}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `python -m pytest -v`
Expected: every test passes.

- [ ] **Step 6: Commit**

```bash
git add build/__main__.py tests/test_cli.py
git commit -m "feat: CLI for validate, lint, and catalog"
```

---

## Task 10 (DEFERRED): path-scoped spelling-lint seam

This task creates the seam only. The British-English and Spain-Spanish spelling rule set is intentionally not implemented yet (it needs real locale content from Plans 3 to 5, and must be path-scoped so it never fires on a future `en-US` folder). The stub keeps the interface stable so a later plan can fill it in without touching callers.

**Files:**
- Create: `build/spelling.py`
- Test: `tests/test_spelling.py`

- [ ] **Step 1: Write the test that pins the seam**

`tests/test_spelling.py`:

```python
from pathlib import Path

from build import spelling


def test_only_scopes_known_locale_folders():
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/en-GB/rules.md")) == "en-GB"
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/es-ES/rules.md")) == "es-ES"
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/en-US/rules.md")) is None
    assert spelling.locale_for_path(Path("README.md")) is None


def test_check_text_is_a_noop_stub_for_now():
    # Deferred: no rules implemented yet, so nothing is flagged.
    assert spelling.check_text("The colour of autumn.", "en-GB") == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_spelling.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.spelling'`.

- [ ] **Step 3: Implement the stub**

`build/spelling.py`:

```python
"""DEFERRED path-scoped spelling lint (en-GB and es-ES only).

Seam only. The rule set (American spellings inside en-GB, Latin American turns
of phrase inside es-ES) is implemented in a later plan once locale content
exists. `check_text` returns no findings today so callers can wire it in safely.
"""

from pathlib import Path

_SCOPED_LOCALES = ("en-GB", "es-ES")


def locale_for_path(path: Path) -> str | None:
    """Return the scoped locale if this path is inside one, else None."""
    parts = path.parts
    for code in _SCOPED_LOCALES:
        if code in parts:
            return code
    return None


def check_text(text: str, locale: str) -> list[str]:
    """Return human-readable findings. Deferred: always empty for now."""
    return []
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_spelling.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/spelling.py tests/test_spelling.py
git commit -m "chore: deferred path-scoped spelling-lint seam (stub)"
```

---

## Self-review

**Spec coverage (the system items from section 12 that belong to the data layer):**
- Schema: Task 5 (`models.py`). Covered.
- Tag vocabularies: Task 3 (`tags.py`). Covered.
- Dice bands: Task 4 (`dice.py`). Covered.
- Canon and lexicon structure: Tasks 5 and 6 (models and loaders). Covered.
- Lint: Task 7. Covered for the structural half; the prose-name-coverage half is explicitly carried by the deferred spelling work (Task 10 seam plus a future plan).
- Catalog generation: Task 8. Covered.
- Locale convention (en-GB, es-ES, explicit codes): Tasks 2, 5, 6 enforce it end to end.

**Items intentionally NOT in this plan (and where they go):** age-tiered character-sheet templates, Unicode font embedding, and the layout-only builders are all rendering, so they are Plan 2. The actual world, story, and guide prose are Plans 3 to 5. This plan deliberately ships no PDF.

**Placeholder scan:** every code step contains complete, runnable code; no TODO or "implement later" inside an active task. Task 10 is labelled DEFERRED and ships a real, tested stub rather than a placeholder.

**Type consistency:** module and symbol names are used identically across tasks: `locales.REQUIRED_LOCALES`, `locales.CANONICAL_LOCALE`, `locales.missing_locales`, `tags.AGE_TIERS/SKILLS/PERILS/READING_LEVELS`, `tags.tiers_for_reading_level`, `dice.BANDS/DICE_FLOOR/thresholds_for`, `models.Story/CanonEntry/LexiconTerm/World`, `content.load_world/load_story/load_canon/load_lexicon/iter_stories`, `lint.lint_repo/LintIssue`, `catalog.build_catalog_markdown/write_catalog`, `spelling.locale_for_path/check_text`. The lint reads content via `content.load_*`, matching their signatures.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-01-wits-and-wonder-01-content-model-and-tooling.md`.

Plans 2 to 5 (PDF pipeline, the two worlds and stories, and the Guide) are scoped in "The plan set and sequencing" above and will be written as their own documents. Plan 2 should be written next, since Plans 3 to 5 cannot be verified end to end until kits build.

Two execution options for Plan 1:

1. **Subagent-Driven (recommended):** a fresh subagent per task, with review between tasks and fast iteration.
2. **Inline Execution:** execute the tasks in this session with checkpoints for review.

Which approach?
