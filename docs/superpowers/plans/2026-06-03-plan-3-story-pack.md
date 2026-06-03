# Plan 3: The Story Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the combined kit into the child-safe **Story Pack**: an always-on front page (title, world paragraph, cover art when present), the map, the narration, the scene gallery, the character sheet, and the colophon, written to the language-first versioned output path. Remove the rules, puzzles, idea bank, and glossary from it.

**Architecture:** `build/render/kit.py`'s `build_kit` becomes `build_story_pack`. A new `frontpage_flowables` helper in `images.py` builds the front page from the story title, the world's `lore_summary`, and the optional cover image. The builder reuses Plan 2's `version`, `colophon`, and `footer` helpers and writes `<out_dir>/<locale>/<world>/<story>/story-pack-<level>-v<n>.pdf`. The CLI `render` command and both GitHub workflows call the renamed function.

**Tech Stack:** Python 3.11, reportlab, pypdf, pytest.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Part 2). Depends on Plans 1 and 2.

---

## File Structure

- `build/render/images.py` (modify): add `frontpage_flowables(title, world_paragraph, cover_path, styles)`.
- `build/render/strings.py` (modify): add `colophon_artifact_storypack` (en-GB, es-ES).
- `build/render/kit.py` (modify): rename `build_kit` to `build_story_pack`; new page set, nested versioned path, colophon, footer, metadata; drop glossary and prose pages.
- `build/__main__.py` (modify): `render` calls `build_story_pack`.
- `.github/workflows/validate-pr.yml` (modify): `fetch-depth: 0`; `build_story_pack`.
- `.github/workflows/build-art.yml` (modify): `fetch-depth: 0`; `build_story_pack` (the loop is replaced by `rebuild` in Plan 6).
- Tests: `tests/test_render_kit.py` (rewrite), `tests/test_cli_render.py` (modify).

---

### Task 1: The front page helper

**Files:**
- Modify: `build/render/images.py`
- Test: `tests/test_render_images.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_images.py`:

```python
def test_frontpage_without_cover_is_title_and_paragraph(tmp_path):
    from reportlab.platypus import Paragraph

    from build.render import fonts, images, theme

    styles = theme.make_styles(theme.Theme.default(), fonts.register_family("dejavu-sans"))
    flows = images.frontpage_flowables("The Sleeping Garden", "A world of floating isles.", None, styles)
    assert all(isinstance(f, Paragraph) or f.__class__.__name__ == "Spacer" for f in flows)
    assert any(isinstance(f, Paragraph) for f in flows)


def test_frontpage_with_cover_includes_an_image(tmp_path):
    from PIL import Image as PILImage
    from reportlab.platypus import Image as RLImage

    from build.render import fonts, images, theme

    cover = tmp_path / "cover.png"
    PILImage.new("RGB", (400, 600), "white").save(cover)
    styles = theme.make_styles(theme.Theme.default(), fonts.register_family("dejavu-sans"))
    flows = images.frontpage_flowables("Title", "Paragraph.", cover, styles)
    assert any(isinstance(f, RLImage) for f in flows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_images.py::test_frontpage_without_cover_is_title_and_paragraph -v`
Expected: FAIL with `AttributeError: module 'build.render.images' has no attribute 'frontpage_flowables'`.

- [ ] **Step 3: Implement `frontpage_flowables`**

In `build/render/images.py`, add a constant near the other size constants:

```python
_FRONT_COVER_MAX_HEIGHT = 170 * mm  # leaves room above for the title and paragraph
```

and add this function (after `cover_flowables`):

```python
def frontpage_flowables(
    title: str, world_paragraph: str, cover_path: Path | None, styles: dict
) -> list:
    """The always-on front page: title banner, a short world paragraph, optional cover.

    The cover image is omitted cleanly when there is no art, so a story with no cover
    still opens with its title and the world paragraph.
    """
    flows: list = [Paragraph(md.inline_to_rl(title), styles["h1"])]
    if world_paragraph:
        flows.append(Spacer(1, 8))
        flows.append(Paragraph(md.inline_to_rl(world_paragraph), styles["body"]))
    if cover_path is not None:
        flows.append(Spacer(1, 12))
        flows.append(image_flowable(cover_path, CONTENT_WIDTH, _FRONT_COVER_MAX_HEIGHT))
    return flows
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_images.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/images.py tests/test_render_images.py
git commit -m "feat(render): always-on front page (title, world paragraph, optional cover)"
git push origin main
```

---

### Task 2: Rename to `build_story_pack` with the new page set and path

**Files:**
- Modify: `build/render/strings.py`
- Modify: `build/render/kit.py`
- Test: `tests/test_render_kit.py` (rewrite)

- [ ] **Step 1: Add the Story Pack colophon label**

In `build/render/strings.py`, add to the `"en-GB"` dict:

```python
        "colophon_artifact_storypack": "Story Pack",
```

and to the `"es-ES"` dict:

```python
        "colophon_artifact_storypack": "Cuaderno de la historia",
```

- [ ] **Step 2: Rewrite the kit test file**

Replace the entire contents of `tests/test_render_kit.py` with:

```python
from pypdf import PdfReader

from build.render import kit

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)

_NEUTRAL_MAP = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="20" text-anchor="middle"></text>'
    '<text data-label="stop:start" x="40" y="100" text-anchor="middle"></text>'
    "</svg>"
)


def _story_assets(repo):
    assets = (
        repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    return assets


def _is_a4(width: float, height: float) -> bool:
    portrait = (595.276, 841.890)
    return (
        (abs(width - portrait[0]) < 2 and abs(height - portrait[1]) < 2)
        or (abs(width - portrait[1]) < 2 and abs(height - portrait[0]) < 2)
    )


def test_reading_level_selects_narration_file():
    assert kit.NARRATION_BY_LEVEL == {
        "simple": "narration.simple.md",
        "rich": "narration.rich.md",
    }


def test_story_pack_writes_nested_versioned_pdf(sample_repo, tmp_path):
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    assert out == tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.pdf"
    assert out.read_bytes().startswith(b"%PDF")


def test_story_pack_has_only_front_narration_sheet_colophon(sample_repo, tmp_path):
    # No map, no cover, no scenes: front + narration + sheet + colophon = 4 pages.
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "rich",
        out_dir=tmp_path,
    )
    assert len(PdfReader(str(out)).pages) == 4


def test_story_pack_adds_a_landscape_map_page(sample_repo, tmp_path):
    (_story_assets(sample_repo) / "map.svg").write_text(_NEUTRAL_MAP, encoding="utf-8")
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    pages = PdfReader(str(out)).pages
    assert len(pages) == 5  # the four above plus the map
    assert all(_is_a4(float(p.mediabox.width), float(p.mediabox.height)) for p in pages)


def test_cover_image_stays_on_the_front_page(sample_repo, tmp_path):
    from PIL import Image as PILImage

    story_dir = sample_repo / "worlds/floating-isles/stories/sleeping-garden"
    assets = story_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    PILImage.new("RGB", (400, 600), "white").save(assets / "cover.png")
    sy = story_dir / "story.yaml"
    sy.write_text(
        sy.read_text(encoding="utf-8")
        + (
            "images:\n  - id: cover\n    role: cover\n    orientation: portrait\n"
            "    prompt: A cover.\n    alt:\n      en-GB: A cover.\n      es-ES: Una portada.\n"
        ),
        encoding="utf-8",
    )
    out = kit.build_story_pack(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path,
    )
    # The cover is embedded on the front page, so the page count is unchanged at 4.
    assert len(PdfReader(str(out)).pages) == 4
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: FAIL with `AttributeError: module 'build.render.kit' has no attribute 'build_story_pack'`.

- [ ] **Step 4: Rewrite `kit.py`**

Replace the entire contents of `build/render/kit.py` with:

```python
"""Assemble one printable Story Pack PDF per (world, story, locale, reading_level).

The Story Pack is the child-safe play material: a front page (title, a short world
paragraph, the cover art when it exists), the map, the narration for the reading
level, the story-in-pictures gallery, the character sheet, and the colophon. The
rules, puzzles, idea bank, and glossary live in the Grown-up's Playbook and the World
Book, not here. Pages are merged with pypdf, then the footer and metadata are stamped.
"""

import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build import content
from build.render import (
    colophon,
    fonts,
    footer,
    images,
    map as kit_map,
    pages,
    sheets,
    strings,
    theme,
    version,
)

NARRATION_BY_LEVEL = {
    "simple": "narration.simple.md",
    "rich": "narration.rich.md",
}


def _image_file(assets_dir: Path, image_id: str) -> Path | None:
    path = assets_dir / f"{image_id}.png"
    return path if path.is_file() else None


def _map_label(key: str, story, canon_by_id: dict, locale: str) -> str:
    if key == "title":
        return story.title.get(locale, story.id)
    if key.startswith("stop:"):
        canon_id = key[len("stop:"):]
        entry = canon_by_id.get(canon_id)
        if entry is not None:
            return entry.names.get(locale, canon_id)
        return strings.ui(locale, "map_" + canon_id)
    return strings.ui(locale, "map_" + key.replace(":", "_").replace("-", "_"))


def _merge(parts: list[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path


def build_story_pack(
    root: Path,
    world_id: str,
    story_id: str,
    locale: str,
    reading_level: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the Story Pack and return its nested, versioned path under out_dir."""
    if reading_level not in NARRATION_BY_LEVEL:
        raise ValueError(f"unknown reading level {reading_level!r}")

    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    content_dir = story_dir / "content" / locale

    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")
    canon = content.load_canon(world_dir / "canon")

    th = theme.Theme.from_world(world)
    faces = fonts.resolve_faces(world, locale)
    styles = theme.make_styles(th, faces)

    story_assets = story_dir / "assets"
    cover_path = next(
        (
            f
            for image in story.images
            if image.role == "cover"
            and (f := _image_file(story_assets, image.id)) is not None
        ),
        None,
    )
    scene_items = [
        (f, image.alt.get(locale, ""))
        for image in story.images
        if image.role == "scene"
        and (f := _image_file(story_assets, image.id)) is not None
    ]

    if version_info is None:
        version_info = version.version_info(
            root,
            version.story_pack_inputs(root, world_id, story_id, locale, reading_level),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    title = story.title.get(locale, story.id)
    world_paragraph = (world.lore_summary or {}).get(locale, "")
    label = strings.ui(locale, "colophon_artifact_storypack")

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        front = images.frontpage_flowables(title, world_paragraph, cover_path, styles)
        parts.append(pages.render_flowables(front, tmp_path / "00_front.pdf", world))

        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            canon_by_id = {entry.id: entry for entry in canon}
            labels = {
                key: _map_label(key, story, canon_by_id, locale)
                for key in kit_map.template_keys(map_svg)
            }
            parts.append(
                kit_map.render_map_template(map_svg, tmp_path / "05_map.pdf", labels)
            )

        narration = content_dir / NARRATION_BY_LEVEL[reading_level]
        parts.append(
            pages.render_markdown_file(
                narration, tmp_path / "10_narration.pdf", world, locale
            )
        )

        if scene_items:
            gallery = images.gallery_flowables(
                strings.ui(locale, "gallery_title"), scene_items, styles
            )
            parts.append(
                pages.render_flowables(gallery, tmp_path / "15_scenes.pdf", world)
            )

        sheet = tmp_path / "80_sheet.pdf"
        sheets.render_character_sheet(sheet, locale, story.age.recommended, th, faces)
        parts.append(sheet)

        qr = f"{colophon.PROJECT_URL}/tree/main/kits/{locale}/{world_id}/{story_id}"
        colo = colophon.colophon_flowables(styles, locale, version_info, label, qr)
        parts.append(pages.render_flowables(colo, tmp_path / "90_colophon.pdf", world))

        out_path = (
            out_dir / locale / world_id / story_id
            / f"story-pack-{reading_level}-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label} · {title}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{title}, {label}, {locale}, {version_info.label}",
        subject=f"Story Pack, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {story_id}, {locale}, {reading_level}, {version_info.label}",
    )
    return out_path
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: PASS (all five tests).

- [ ] **Step 6: Commit**

```bash
git add build/render/kit.py build/render/strings.py tests/test_render_kit.py
git commit -m "feat(render): build the Story Pack (front page, no answers, versioned nested path)"
git push origin main
```

---

### Task 3: Point the CLI `render` at `build_story_pack`

**Files:**
- Modify: `build/__main__.py`
- Test: `tests/test_cli_render.py`

- [ ] **Step 1: Write the failing test**

Replace `test_render_builds_a_kit` in `tests/test_cli_render.py` with:

```python
def test_render_builds_a_story_pack(sample_repo, tmp_path, capsys):
    code = main([
        "render", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--reading-level", "simple",
        "--out-dir", str(tmp_path),
    ])
    assert code == 0
    expected = tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.pdf"
    assert expected.is_file()
    assert "story-pack-simple-v0.pdf" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py::test_render_builds_a_story_pack -v`
Expected: FAIL (the CLI still calls `build_kit` and prints the old flat name).

- [ ] **Step 3: Update the `render` command**

In `build/__main__.py`, replace the `render` command block with:

```python
    if args.command == "render":
        from build.render import kit

        out = kit.build_story_pack(
            args.root, args.world, args.story, args.locale, args.reading_level,
            out_dir=args.out_dir,
        )
        print(f"built {out}")
        return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/__main__.py tests/test_cli_render.py
git commit -m "feat(cli): render builds the Story Pack"
git push origin main
```

---

### Task 4: Update the workflows to the renamed function

**Files:**
- Modify: `.github/workflows/validate-pr.yml`
- Modify: `.github/workflows/build-art.yml`

- [ ] **Step 1: Update `validate-pr.yml`**

Give the checkout full history (so `version_info` works) by changing the checkout step to:

```yaml
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
```

In the "Build preview kits" inline Python, change the build call from `kit.build_kit(` to `kit.build_story_pack(`:

```python
                  kit.build_story_pack(Path("."), world, story.id, locale, "simple", out_dir=Path("preview"))
```

- [ ] **Step 2: Update `build-art.yml`**

Change its checkout step the same way:

```yaml
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
```

In the "Rebuild kits and the catalogue" inline Python, change `kit.build_kit(` to `kit.build_story_pack(`:

```python
                  kit.build_story_pack(Path("."), world, story, locale, level, out_dir=Path("kits"))
```

(The whole inline loop in `build-art.yml` is replaced by `python -m build rebuild` in Plan 6; this keeps it working in the meantime.)

- [ ] **Step 3: Verify the workflows are valid YAML**

Run: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/validate-pr.yml')); yaml.safe_load(open('.github/workflows/build-art.yml')); print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/validate-pr.yml .github/workflows/build-art.yml
git commit -m "ci: build the Story Pack and fetch full history for versioning"
git push origin main
```

---

## Self-Review

- **Spec coverage (Part 2):** the front page is always on (Task 1), the Story Pack drops rules/puzzles/idea-bank/glossary and keeps front/map/narration/scenes/sheet/colophon (Task 2, asserted by the exact page counts), and the nested versioned path `story-pack-<level>-v<n>.pdf` is produced (Task 2) and used by the CLI (Task 3) and workflows (Task 4).
- **Placeholder scan:** none.
- **Type consistency:** `build_story_pack(root, world_id, story_id, locale, reading_level, *, out_dir=None, version_info=None)` reuses `version.story_pack_inputs`, `colophon.colophon_flowables`, `colophon.PROJECT_URL`, `footer.stamp_footers`, and `footer.set_metadata` exactly as defined in Plan 2; `images.frontpage_flowables(title, world_paragraph, cover_path, styles)` is defined in Task 1 and called in Task 2; `strings.ui(locale, "colophon_artifact_storypack")` is added in Task 2.
- **Note:** `build_kit` no longer exists; every in-repo caller (CLI, both workflows, tests) is updated in this plan, so nothing references the old name.
