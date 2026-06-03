# Plan 4: The Grown-up's Playbook and the World Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the idea bank to the world level, then build the two remaining artifacts: the **Grown-up's Playbook** (rules plus puzzles and answers, per story) and the **World Book** (cover and lore, glossary, the world idea bank, and a stories list, per world). Both reuse Plan 2's version, colophon, and footer helpers.

**Architecture:** The idea bank moves from `worlds/<world>/stories/<story>/content/<locale>/idea-bank.md` to `worlds/<world>/content/<locale>/idea-bank.md`; the lint drops it from the per-story required set and adds a per-world check. Two new builders, `build/render/playbook.py` and `build/render/world_pdf.py`, assemble their pages and reuse `kit._merge`, `version`, `colophon`, and `footer`. Two new CLI commands, `render-playbook` and `render-world`, drive them.

**Tech Stack:** Python 3.11, reportlab, pypdf, pytest.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Parts 3, 4). Depends on Plans 1, 2, 3.

---

## File Structure

- `build/lint.py` (modify): drop `idea-bank.md` from `_REQUIRED_CONTENT_FILES`; add a per-world idea-bank check.
- `tests/conftest.py` (modify): `sample_repo` writes a world-level idea bank and no per-story one.
- `worlds/floating-isles/content/<locale>/idea-bank.md`, `worlds/greek-myth/content/<locale>/idea-bank.md` (move): the four real idea banks relocate.
- `build/render/playbook.py` (create): `build_playbook(root, world, story, locale, *, out_dir, version_info)`.
- `build/render/world_pdf.py` (create): `build_world_pdf(root, world, locale, *, out_dir, version_info)`.
- `build/render/strings.py` (modify): add the playbook and world-book labels and the secret note and stories title (en-GB, es-ES).
- `build/__main__.py` (modify): add `render-playbook` and `render-world`.
- Tests: `tests/test_render_playbook.py`, `tests/test_render_world_pdf.py` (create); `tests/test_lint.py`, `tests/test_cli_render.py` (modify).

> Skill and README text for the world-level idea bank are updated in Plan 6 with the other docs.

---

### Task 1: Move the idea bank to the world level

**Files:**
- Modify: `build/lint.py`
- Modify: `tests/conftest.py`
- Move: the four real `idea-bank.md` files
- Test: `tests/test_lint.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_lint.py`:

```python
def test_lint_requires_a_world_level_idea_bank(sample_repo):
    from build import lint

    target = sample_repo / "worlds" / "floating-isles" / "content" / "en-GB" / "idea-bank.md"
    target.unlink()
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "error" and "world idea bank" in i.message for i in issues
    )


def test_lint_does_not_require_a_per_story_idea_bank(sample_repo):
    from build import lint

    story_idea = (
        sample_repo / "worlds" / "floating-isles" / "stories" / "sleeping-garden"
        / "content" / "en-GB" / "idea-bank.md"
    )
    # There is no per-story idea bank, and that must not be an error.
    assert not story_idea.exists()
    errors = [i for i in lint.lint_repo(sample_repo) if i.level == "error"]
    assert not any("idea-bank.md" in e.message for e in errors)
```

- [ ] **Step 2: Update `conftest.py` so the sample repo matches the new layout**

In `tests/conftest.py`, in the `sample_repo` fixture, change the per-story content loop to drop the idea bank:

```python
    for content_dir in (content_en, content_es):
        for name in ("narration.simple.md", "narration.rich.md", "rules.md",
                     "puzzles.md"):
            (content_dir / name).write_text("placeholder\n", encoding="utf-8")
```

and add a world-level idea bank just below that loop (before the `lexicon_dir` block):

```python
    for code in ("en-GB", "es-ES"):
        world_content = world_dir / "content" / code
        world_content.mkdir(parents=True)
        (world_content / "idea-bank.md").write_text(
            "# Idea bank\n\nImprov fuel for this world.\n", encoding="utf-8"
        )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_lint.py::test_lint_requires_a_world_level_idea_bank -v`
Expected: FAIL (the lint does not yet check a world-level idea bank).

- [ ] **Step 4: Update the lint**

In `build/lint.py`, remove `"idea-bank.md"` from `_REQUIRED_CONTENT_FILES` so it reads:

```python
_REQUIRED_CONTENT_FILES = (
    "narration.simple.md",
    "narration.rich.md",
    "rules.md",
    "puzzles.md",
)
```

In `_lint_world`, add the per-world idea-bank check. Insert it just after the `world_yaml` block (after the `else:` branch that lints image refs and files), before the `stories_dir = world_dir / "stories"` line:

```python
    for code in locales.REQUIRED_LOCALES:
        idea = world_dir / "content" / code / "idea-bank.md"
        if not idea.is_file():
            issues.append(_error(f"missing world idea bank for {code}", str(idea)))
```

Also update the module docstring's third sentence to mention the world idea bank:

```python
every required content file exists for every required locale, and each world has a
world-level idea bank for every required locale.
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_lint.py tests/test_render_kit.py -v`
Expected: PASS.

- [ ] **Step 6: Move the four real idea-bank files**

```bash
mkdir -p worlds/floating-isles/content/en-GB worlds/floating-isles/content/es-ES
mkdir -p worlds/greek-myth/content/en-GB worlds/greek-myth/content/es-ES
git mv worlds/floating-isles/stories/sleeping-garden/content/en-GB/idea-bank.md worlds/floating-isles/content/en-GB/idea-bank.md
git mv worlds/floating-isles/stories/sleeping-garden/content/es-ES/idea-bank.md worlds/floating-isles/content/es-ES/idea-bank.md
git mv worlds/greek-myth/stories/the-singing-spring/content/en-GB/idea-bank.md worlds/greek-myth/content/en-GB/idea-bank.md
git mv worlds/greek-myth/stories/the-singing-spring/content/es-ES/idea-bank.md worlds/greek-myth/content/es-ES/idea-bank.md
```

- [ ] **Step 7: Verify the real repo still lints clean**

Run: `.venv/bin/python -m build lint --root .`
Expected: `lint clean` (no `[error]` lines; image-file warnings for prompts-only art are fine).

- [ ] **Step 8: Commit**

```bash
git add build/lint.py tests/conftest.py tests/test_lint.py worlds/
git commit -m "feat(content): move the idea bank to the world level"
git push origin main
```

---

### Task 2: The Grown-up's Playbook builder and command

**Files:**
- Modify: `build/render/strings.py`
- Create: `build/render/playbook.py`
- Modify: `build/__main__.py`
- Test: `tests/test_render_playbook.py`, `tests/test_cli_render.py`

- [ ] **Step 1: Add the Playbook strings**

In `build/render/strings.py`, add to the `"en-GB"` dict:

```python
        "colophon_artifact_playbook": "Grown-up's Playbook",
        "playbook_secret_note": "The answers are here. This part is for the grown-up, not for the child.",
```

and to the `"es-ES"` dict:

```python
        "colophon_artifact_playbook": "Cuaderno para la persona adulta",
        "playbook_secret_note": "Aquí están las respuestas. Esta parte es para la persona adulta, no para quien juega.",
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_render_playbook.py`:

```python
from pypdf import PdfReader

from build.render import playbook


def test_playbook_writes_nested_versioned_pdf(sample_repo, tmp_path):
    out = playbook.build_playbook(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", out_dir=tmp_path
    )
    assert out == (
        tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "playbook-v0.pdf"
    )
    assert out.read_bytes().startswith(b"%PDF")
    # title + rules + puzzles + colophon = 4 pages
    assert len(PdfReader(str(out)).pages) == 4


def test_playbook_renders_in_spanish(sample_repo, tmp_path):
    out = playbook.build_playbook(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", out_dir=tmp_path
    )
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_playbook.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.playbook'`.

- [ ] **Step 4: Implement `playbook.py`**

Create `build/render/playbook.py`:

```python
"""Build the Grown-up's Playbook PDF per (world, story, locale).

The Playbook is the grown-up's private prep: how to run this story (its rules) and
the puzzles together with their solutions. It is the only artifact that holds the
answers, so a child reading the Story Pack never meets one. Single adult level, one
per locale. Pages are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from reportlab.platypus import Paragraph

from build import content
from build.render import colophon, fonts, footer, pages, strings, theme, version
from build.render import markdown as md
from build.render.kit import _merge


def build_playbook(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Grown-up's Playbook and return its nested, versioned path."""
    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    content_dir = story_dir / "content" / locale

    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    if version_info is None:
        version_info = version.version_info(
            root, version.playbook_inputs(root, world_id, story_id, locale)
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    label = strings.ui(locale, "colophon_artifact_playbook")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        head = [
            Paragraph(md.inline_to_rl(f"{label}: {title}"), styles["h1"]),
            Paragraph(
                md.inline_to_rl(strings.ui(locale, "playbook_secret_note")),
                styles["body"],
            ),
        ]
        parts.append(pages.render_flowables(head, tmp_path / "00_title.pdf", world))
        parts.append(
            pages.render_markdown_file(
                content_dir / "rules.md", tmp_path / "10_rules.pdf", world, locale
            )
        )
        parts.append(
            pages.render_markdown_file(
                content_dir / "puzzles.md", tmp_path / "20_puzzles.pdf", world, locale
            )
        )
        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"playbook-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Grown-ups Playbook, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, playbook, {version_info.label}",
    )
    return out_path
```

- [ ] **Step 5: Add the `render-playbook` CLI command**

In `build/__main__.py`, add this parser next to the other `render` parsers (after the `render-guide` parser):

```python
    playbook_parser = sub.add_parser("render-playbook", help="build a Grown-up's Playbook PDF")
    _add_root(playbook_parser)
    playbook_parser.add_argument("--world", required=True)
    playbook_parser.add_argument("--story", required=True)
    playbook_parser.add_argument("--locale", required=True)
    playbook_parser.add_argument("--out-dir", type=Path, default=None)
```

and add this command block (after the `render-guide` block):

```python
    if args.command == "render-playbook":
        from build.render import playbook

        out = playbook.build_playbook(
            args.root, args.world, args.story, args.locale, out_dir=args.out_dir
        )
        print(f"built {out}")
        return 0
```

Add a CLI test to `tests/test_cli_render.py`:

```python
def test_render_playbook_builds(sample_repo, tmp_path):
    from build.__main__ import main

    code = main([
        "render-playbook", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (
        tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "playbook-v0.pdf"
    ).is_file()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_playbook.py tests/test_cli_render.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add build/render/playbook.py build/render/strings.py build/__main__.py tests/test_render_playbook.py tests/test_cli_render.py
git commit -m "feat(render): build the Grown-up's Playbook (rules and answers)"
git push origin main
```

---

### Task 3: The World Book builder and command

**Files:**
- Modify: `build/render/strings.py`
- Create: `build/render/world_pdf.py`
- Modify: `build/__main__.py`
- Test: `tests/test_render_world_pdf.py`, `tests/test_cli_render.py`

- [ ] **Step 1: Add the World Book strings**

In `build/render/strings.py`, add to the `"en-GB"` dict:

```python
        "colophon_artifact_worldbook": "World Book",
        "worldbook_stories_title": "Stories in this world",
```

and to the `"es-ES"` dict:

```python
        "colophon_artifact_worldbook": "Libro del Mundo",
        "worldbook_stories_title": "Historias de este mundo",
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_render_world_pdf.py`:

```python
from pypdf import PdfReader

from build.render import world_pdf


def test_world_book_writes_nested_versioned_pdf(sample_repo, tmp_path):
    out = world_pdf.build_world_pdf(
        sample_repo, "floating-isles", "en-GB", out_dir=tmp_path
    )
    assert out == tmp_path / "en-GB" / "floating-isles" / "world-book-v0.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    # cover + glossary + idea bank + stories list + colophon = 5 pages
    assert len(PdfReader(str(out)).pages) == 5


def test_world_book_renders_in_spanish(sample_repo, tmp_path):
    out = world_pdf.build_world_pdf(
        sample_repo, "floating-isles", "es-ES", out_dir=tmp_path
    )
    assert out.read_bytes().startswith(b"%PDF")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_world_pdf.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.world_pdf'`.

- [ ] **Step 4: Implement `world_pdf.py`**

Create `build/render/world_pdf.py`:

```python
"""Build the World Book PDF per (world, locale).

The World Book is the world reference shared by every story: the world cover and
lore, the full who's-who glossary from canon (with portraits when art exists), the
world-level idea bank, and a list of the stories in the world. One per locale. Pages
are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from reportlab.platypus import Paragraph

from build import content
from build.render import (
    colophon,
    fonts,
    footer,
    glossary,
    images,
    pages,
    strings,
    theme,
    version,
)
from build.render import markdown as md
from build.render.kit import _image_file, _merge


def _first_sentence(path: Path) -> str:
    """The first prose sentence of a narration file, skipping headings and blanks."""
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for end in (". ", "! ", "? "):
            if end in stripped:
                return stripped.split(end)[0] + end.strip()
        return stripped
    return ""


def _portrait_paths(root: Path, world_id: str, world) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    world_dir = root / "worlds" / world_id
    for image in world.images:
        if image.role == "portrait" and image.canon_ref:
            found = _image_file(world_dir / "assets", image.id)
            if found is not None:
                paths[image.canon_ref] = found
    for story_yaml in sorted((world_dir / "stories").glob("*/story.yaml")):
        story = content.load_story(story_yaml)
        for image in story.images:
            if image.role == "portrait" and image.canon_ref:
                found = _image_file(story_yaml.parent / "assets", image.id)
                if found is not None:
                    paths[image.canon_ref] = found
    return paths


def _stories_flowables(root: Path, world_id: str, locale: str, styles: dict) -> list:
    flows = [
        Paragraph(
            md.inline_to_rl(strings.ui(locale, "worldbook_stories_title")), styles["h1"]
        )
    ]
    stories_dir = root / "worlds" / world_id / "stories"
    for story_yaml in sorted(stories_dir.glob("*/story.yaml")):
        story = content.load_story(story_yaml)
        title = story.title.get(locale, story.id)
        hook = _first_sentence(story_yaml.parent / "content" / locale / "narration.simple.md")
        line = f"**{title}** ({story.age.recommended}). {hook}".strip()
        flows.append(Paragraph(md.inline_to_rl(line), styles["body"]))
    return flows


def build_world_pdf(
    root: Path,
    world_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the World Book and return its nested, versioned path."""
    world_dir = root / "worlds" / world_id
    world = content.load_world(world_dir / "world.yaml")
    canon = content.load_canon(world_dir / "canon")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    if version_info is None:
        version_info = version.version_info(
            root, version.world_book_inputs(root, world_id, locale)
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    label = strings.ui(locale, "colophon_artifact_worldbook")
    world_name = world.name.get(locale, world_id)
    lore = (world.lore_summary or {}).get(locale, "")
    cover_path = next(
        (
            f
            for image in world.images
            if image.role == "cover"
            and (f := _image_file(world_dir / "assets", image.id)) is not None
        ),
        None,
    )

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        cover = images.frontpage_flowables(world_name, lore, cover_path, styles)
        parts.append(pages.render_flowables(cover, tmp_path / "00_cover.pdf", world))

        gloss = glossary.glossary_flowables(
            canon, locale, styles, th, _portrait_paths(root, world_id, world)
        )
        parts.append(pages.render_flowables(gloss, tmp_path / "10_glossary.pdf", world))

        idea = world_dir / "content" / locale / "idea-bank.md"
        parts.append(
            pages.render_markdown_file(idea, tmp_path / "20_idea.pdf", world, locale)
        )

        stories = _stories_flowables(root, world_id, locale, styles)
        parts.append(pages.render_flowables(stories, tmp_path / "30_stories.pdf", world))

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = out_dir / locale / world_id / f"world-book-{version_info.label}.pdf"
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label} · {world_name}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{world_name}, {label}, {locale}, {version_info.label}",
        subject=f"World Book, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {locale}, world-book, {version_info.label}",
    )
    return out_path
```

- [ ] **Step 5: Add the `render-world` CLI command**

In `build/__main__.py`, add this parser (after the `render-playbook` parser):

```python
    world_parser = sub.add_parser("render-world", help="build a World Book PDF")
    _add_root(world_parser)
    world_parser.add_argument("--world", required=True)
    world_parser.add_argument("--locale", required=True)
    world_parser.add_argument("--out-dir", type=Path, default=None)
```

and this command block (after the `render-playbook` block):

```python
    if args.command == "render-world":
        from build.render import world_pdf

        out = world_pdf.build_world_pdf(
            args.root, args.world, args.locale, out_dir=args.out_dir
        )
        print(f"built {out}")
        return 0
```

Also update the module docstring on line 1 of `build/__main__.py` to list the new commands:

```python
"""Command line: python -m build {validate,lint,catalog,render,render-guide,render-playbook,render-world,prompts,generate-images}."""
```

Add a CLI test to `tests/test_cli_render.py`:

```python
def test_render_world_builds(sample_repo, tmp_path):
    from build.__main__ import main

    code = main([
        "render-world", "--root", str(sample_repo),
        "--world", "floating-isles", "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "en-GB" / "floating-isles" / "world-book-v0.pdf").is_file()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_world_pdf.py tests/test_cli_render.py -v`
Expected: PASS.

- [ ] **Step 7: Run the whole suite and lint**

Run: `.venv/bin/python -m pytest && .venv/bin/python -m build lint --root .`
Expected: suite PASS; `lint clean`.

- [ ] **Step 8: Manually verify a real Playbook and World Book**

```bash
.venv/bin/python -m build render-playbook --root . --world floating-isles --story sleeping-garden --locale en-GB --out-dir /tmp/pb
.venv/bin/python -m build render-world --root . --world floating-isles --locale en-GB --out-dir /tmp/wb
pdftoppm -png -r 110 "$(find /tmp/pb -name '*.pdf')" /tmp/pb_img
pdftoppm -png -r 110 "$(find /tmp/wb -name '*.pdf')" /tmp/wb_img
```
Confirm the Playbook shows the rules then the puzzles and answers, the World Book shows lore, the glossary, the idea bank, and the stories list, and both end with a colophon and carry the footer.

- [ ] **Step 9: Commit**

```bash
git add build/render/world_pdf.py build/render/strings.py build/__main__.py tests/test_render_world_pdf.py tests/test_cli_render.py
git commit -m "feat(render): build the World Book (lore, glossary, idea bank, stories)"
git push origin main
```

---

## Self-Review

- **Spec coverage (Parts 3, 4):** the idea bank is world-level (Task 1, lint plus migration); the Playbook holds rules and answers only (Task 2); the World Book holds cover and lore, glossary, idea bank, and the stories list (Task 3). Both write the nested versioned path and carry colophon, footer, and metadata.
- **Placeholder scan:** none.
- **Type consistency:** `build_playbook(root, world_id, story_id, locale, *, out_dir=None, version_info=None)` and `build_world_pdf(root, world_id, locale, *, out_dir=None, version_info=None)` mirror `build_story_pack`'s shape; both reuse `kit._merge`, `kit._image_file`, `version.playbook_inputs`/`world_book_inputs`, `colophon.colophon_flowables`, `colophon.PROJECT_URL`, `footer.stamp_footers`, `footer.set_metadata`, and `images.frontpage_flowables`, all defined in earlier plans. New strings `colophon_artifact_playbook`, `playbook_secret_note`, `colophon_artifact_worldbook`, `worldbook_stories_title` are added before use.
- **Note:** the per-story `idea-bank.md` is removed from the lint requirement and the real files are moved; `content.py` needs no change because the idea bank is rendered straight from its markdown path, not loaded into a model.
