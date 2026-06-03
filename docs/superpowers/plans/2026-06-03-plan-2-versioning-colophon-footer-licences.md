# Plan 2: Versioning, Colophon, Footer, and Licences (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reusable "page furniture" every artifact will share, automatic git-derived versioning, a colophon end page with a QR code, a per-page footer, PDF metadata, and the two licence files, and prove it end to end on the Guide for the Grown-Up.

**Architecture:** Three new pure modules. `version.py` derives a `VersionInfo` (commit count plus last-changed date) from git over an artifact's own source files. `colophon.py` builds the end-page flowables including a `segno` QR. `footer.py` runs two final passes over a merged PDF: it stamps a per-page footer (a reportlab overlay sized per page) and sets PDF metadata. The Guide builder adopts all of it (colophon page, footer, metadata, versioned filename under `guides/`). The Story Pack, Playbook, and World Book adopt the same helpers in Plans 3 and 4.

**Tech Stack:** Python 3.11, reportlab, pypdf, segno, git (via subprocess), pytest.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Parts 6, 7, 8).

> **Decomposition note:** the spec's Plan 2 says "prove the convention on the two builders that exist today (kit and guide)." This plan proves it on the **Guide** only, because the kit is rewritten into the Story Pack in Plan 3 (new pages, nested path, per-artifact QR URL) and would otherwise be wired twice. Plan 3's Story Pack adopts the identical helpers. The Guide is a real, final-location artifact, so the convention is still proven end to end here.

---

## File Structure

- `build/render/version.py` (create): `VersionInfo` dataclass, `version_info(root, paths)`, and the per-artifact input-path helpers.
- `build/render/colophon.py` (create): `colophon_flowables(styles, locale, version_info, artifact_label, qr_url)` and the project/licence constants.
- `build/render/footer.py` (create): `stamp_footers(...)` and `set_metadata(...)`, both operating on a finished PDF.
- `build/render/strings.py` (modify): add the five `colophon_*` strings plus `colophon_artifact_guide`, en-GB and es-ES.
- `build/render/pages.py` (modify): `render_guide` gains the colophon page, the footer, metadata, and an injected version.
- `build/__main__.py` (modify): `render-guide` computes the version, writes under `<out_dir>/guides/` with the `-v<n>` suffix, and passes the version and QR URL in.
- `pyproject.toml` (modify): add `segno` to the `render` extra.
- `LICENSE` (create): MIT, for the code.
- `LICENSE-CONTENT` (create): CC BY-SA 4.0, for the content and PDFs.
- Tests: `tests/test_render_version.py`, `tests/test_render_colophon.py`, `tests/test_render_footer.py`, `tests/test_licenses.py` (create); `tests/test_cli_render.py` (modify).

---

### Task 1: Automatic git-derived versioning

**Files:**
- Create: `build/render/version.py`
- Test: `tests/test_render_version.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_version.py`:

```python
import subprocess
from pathlib import Path

from build.render import version


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "Test")


def _commit(root: Path, path: Path, text: str, message: str) -> None:
    path.write_text(text, encoding="utf-8")
    _git(root, "add", str(path.relative_to(root)))
    _git(root, "commit", "-m", message)


def test_version_counts_commits_and_dates(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "a.txt"
    _commit(tmp_path, f, "one", "first")
    _commit(tmp_path, f, "two", "second")
    info = version.version_info(tmp_path, [f])
    assert info.number == 2
    assert info.updated.count("-") == 2  # YYYY-MM-DD
    assert info.dirty is False
    assert info.label == "v2"


def test_version_with_no_history_is_unreleased(tmp_path):
    _init_repo(tmp_path)
    info = version.version_info(tmp_path, [tmp_path / "missing.txt"])
    assert info.number == 0
    assert info.updated == "unreleased"
    assert info.label == "v0"


def test_version_marks_a_dirty_input(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "a.txt"
    _commit(tmp_path, f, "one", "first")
    f.write_text("uncommitted change", encoding="utf-8")
    info = version.version_info(tmp_path, [f])
    assert info.number == 1
    assert info.dirty is True
    assert info.label == "v1+"


def test_story_pack_inputs_lists_the_right_paths(tmp_path):
    paths = version.story_pack_inputs(tmp_path, "w", "s", "en-GB", "simple")
    names = {p.name for p in paths}
    assert "story.yaml" in names
    assert "narration.simple.md" in names
    assert "world.yaml" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_version.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.version'`.

- [ ] **Step 3: Implement `version.py`**

Create `build/render/version.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_version.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/version.py tests/test_render_version.py
git commit -m "feat(render): git-derived per-artifact versioning"
git push origin main
```

---

### Task 2: The colophon flowables and the QR

**Files:**
- Modify: `pyproject.toml`
- Create: `build/render/colophon.py`
- Modify: `build/render/strings.py`
- Test: `tests/test_render_colophon.py`

- [ ] **Step 1: Add the `segno` dependency and install it**

In `pyproject.toml`, change the `render` extra to add `segno`:

```toml
render = [
    "reportlab>=4.0",
    "cairosvg>=2.7",
    "pypdf>=4.0",
    "defusedxml>=0.7",
    "segno>=1.6",
]
```

Run: `.venv/bin/pip install -e ".[dev,render]"`
Expected: segno installs.

- [ ] **Step 2: Write the failing test**

Create `tests/test_render_colophon.py`:

```python
from pypdf import PdfReader
from reportlab.platypus import Image as RLImage

from build.models import World
from build.render import colophon, fonts, pages, theme
from build.render.version import VersionInfo


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def _world():
    return World.model_validate(
        {"id": "_", "name": {"en-GB": "_", "es-ES": "_"}}
    )


def test_colophon_includes_a_qr_and_text():
    flows = colophon.colophon_flowables(
        _styles(), "en-GB", VersionInfo(3, "2026-06-03"), "Story Pack",
        "https://example.com/x",
    )
    assert any(isinstance(f, RLImage) for f in flows)
    assert len(flows) >= 6


def test_colophon_renders_one_page_in_spanish(tmp_path):
    flows = colophon.colophon_flowables(
        _styles(), "es-ES", VersionInfo(1, "2026-06-03"), "Libro del Mundo",
        "https://example.com/x",
    )
    out = pages.render_flowables(flows, tmp_path / "c.pdf", _world())
    assert len(PdfReader(str(out)).pages) == 1
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_colophon.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.colophon'`.

- [ ] **Step 4: Add the colophon strings**

In `build/render/strings.py`, add these keys inside the `"en-GB"` dict:

```python
        "colophon_project": "Wits and Wonder",
        "colophon_artifact_guide": "Guide for the Grown-Up",
        "colophon_licence": "Content licence: {code} ({url})",
        "colophon_version": "Version {number}, updated {updated}, {locale}",
        "colophon_qr_caption": "Scan for the latest version",
        "colophon_promise": "Here nobody loses. If a try does not work, find another way.",
```

and these inside the `"es-ES"` dict:

```python
        "colophon_project": "Wits and Wonder",
        "colophon_artifact_guide": "Guía para la persona adulta",
        "colophon_licence": "Licencia del contenido: {code} ({url})",
        "colophon_version": "Versión {number}, actualizada el {updated}, {locale}",
        "colophon_qr_caption": "Escanea para la última versión",
        "colophon_promise": "Aquí nadie pierde. Si algo no sale, se busca otra manera.",
```

- [ ] **Step 5: Implement `colophon.py`**

Create `build/render/colophon.py`:

```python
"""The colophon end page: project link, content licence, version, and a QR code.

A printed kit is frozen at its printed version, so the QR links to the artifact's
GitHub directory, which always shows the newest versioned file. The QR image and the
URLs are locale-neutral; only the surrounding words are localized.
"""

import io

import segno
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, Paragraph, Spacer

from build.render import markdown as md, strings
from build.render.version import VersionInfo

PROJECT_URL = "https://github.com/agigante80/wits-and-wonder"
LICENCE_CODE = "CC BY-SA 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
_QR_SIZE = 30 * mm


def _qr_image(url: str) -> RLImage:
    buffer = io.BytesIO()
    segno.make(url, error="m").save(buffer, kind="png", scale=8, border=1)
    buffer.seek(0)
    return RLImage(buffer, width=_QR_SIZE, height=_QR_SIZE)


def colophon_flowables(
    styles: dict,
    locale: str,
    version_info: VersionInfo,
    artifact_label: str,
    qr_url: str,
) -> list:
    """Flowables for the single colophon page at the end of every artifact."""
    licence = strings.ui(locale, "colophon_licence").format(
        code=LICENCE_CODE, url=LICENCE_URL
    )
    version_line = strings.ui(locale, "colophon_version").format(
        number=version_info.number, updated=version_info.updated, locale=locale
    )
    return [
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_project")), styles["h1"]),
        Spacer(1, 12),
        Paragraph(md.inline_to_rl(artifact_label), styles["h2"]),
        Spacer(1, 6),
        Paragraph(md.inline_to_rl(PROJECT_URL), styles["body"]),
        Paragraph(md.inline_to_rl(licence), styles["body"]),
        Paragraph(md.inline_to_rl(version_line), styles["body"]),
        Spacer(1, 16),
        _qr_image(qr_url),
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_qr_caption")), styles["body"]),
        Spacer(1, 16),
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_promise")), styles["body"]),
    ]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_colophon.py tests/test_render_strings.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml build/render/colophon.py build/render/strings.py tests/test_render_colophon.py
git commit -m "feat(render): colophon end page with project link, licence, version, and QR"
git push origin main
```

---

### Task 3: The per-page footer and PDF metadata

**Files:**
- Create: `build/render/footer.py`
- Test: `tests/test_render_footer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_footer.py`:

```python
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from build.render import footer
from build.render.version import VersionInfo


def _two_page_pdf(path):
    c = rl_canvas.Canvas(str(path), pagesize=A4)
    c.drawString(100, 100, "one")
    c.showPage()
    c.drawString(100, 100, "two")
    c.showPage()
    c.save()


def test_stamp_footers_keeps_page_count(tmp_path):
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.stamp_footers(
        p, identity="Wits and Wonder . Story Pack . The Sleeping Garden",
        locale="en-GB", version_info=VersionInfo(7, "2026-06-03"),
    )
    assert len(PdfReader(str(p)).pages) == 2


def test_set_metadata_writes_fields(tmp_path):
    p = tmp_path / "d.pdf"
    _two_page_pdf(p)
    footer.set_metadata(
        p, title="The Sleeping Garden, Story Pack, en-GB, v7",
        subject="Story Pack, v7, 2026-06-03", keywords="floating-isles, sleeping-garden",
    )
    meta = PdfReader(str(p)).metadata
    assert meta.title == "The Sleeping Garden, Story Pack, en-GB, v7"
    assert meta.author == "Wits and Wonder"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_footer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.footer'`.

- [ ] **Step 3: Implement `footer.py`**

Create `build/render/footer.py`:

```python
"""Final passes over a finished, merged PDF: stamp a per-page footer, set metadata.

Each artifact is several sub-PDFs merged with pypdf, so the total page count and a
uniform footer are only knowable on the merged file. The footer is a reportlab
overlay sized to each page, so portrait and landscape pages both get it.
"""

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from build.render.version import VersionInfo

_FOOTER_GREY = HexColor("#8a8a8a")
_FOOTER_FONT = "Helvetica"  # a standard PDF font, no embedding, covers Latin accents
_FOOTER_SIZE = 7


def _overlay_page(width: float, height: float, left: str, right: str):
    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=(width, height))
    c.setFillColor(_FOOTER_GREY)
    c.setFont(_FOOTER_FONT, _FOOTER_SIZE)
    c.drawString(12 * mm, 6 * mm, left)
    c.drawRightString(width - 12 * mm, 6 * mm, right)
    c.showPage()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def stamp_footers(
    pdf_path: Path, *, identity: str, locale: str, version_info: VersionInfo
) -> Path:
    """Draw a discreet footer on every page of the merged PDF, in place."""
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    writer = PdfWriter()
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        right = f"{locale} · {version_info.label} · page {index} of {total}"
        page.merge_page(_overlay_page(width, height, identity, right))
        writer.add_page(page)
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    return pdf_path


def set_metadata(
    pdf_path: Path, *, title: str, subject: str, keywords: str,
    author: str = "Wits and Wonder",
) -> Path:
    """Set the PDF document metadata, in place. Separators are commas, never dashes."""
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.add_metadata(
        {"/Title": title, "/Author": author, "/Subject": subject, "/Keywords": keywords}
    )
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    return pdf_path
```

(`·` is the middle dot; it is in the standard font encoding and is not a dash.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_footer.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/footer.py tests/test_render_footer.py
git commit -m "feat(render): per-page footer stamping and PDF metadata"
git push origin main
```

---

### Task 4: The licence files

**Files:**
- Create: `LICENSE`
- Create: `LICENSE-CONTENT`
- Test: `tests/test_licenses.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_licenses.py`:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_code_licence_is_mit():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "Wits and Wonder" in text


def test_content_licence_is_cc_by_sa():
    text = (ROOT / "LICENSE-CONTENT").read_text(encoding="utf-8")
    assert "CC BY-SA 4.0" in text
    assert "creativecommons.org/licenses/by-sa/4.0" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_licenses.py -v`
Expected: FAIL (files do not exist).

- [ ] **Step 3: Create `LICENSE` (MIT)**

Create `LICENSE` with the standard MIT text (use a hyphen only to join words; no dashes):

```
MIT License

Copyright (c) 2026 Wits and Wonder maintainers (github.com/agigante80)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Create `LICENSE-CONTENT` (CC BY-SA 4.0)**

Create `LICENSE-CONTENT` (note: this covers content, not code):

```
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)

This licence covers the creative content of Wits and Wonder: everything under
worlds/, guide/, and lexicon/, and the generated PDFs under kits/. The software
toolchain (the build/ package and tests/) is licensed separately under the MIT
licence in LICENSE.

You are free to share and adapt this content, including for commercial purposes,
under these terms:

  Attribution. You must give appropriate credit to Wits and Wonder
  (github.com/agigante80/wits-and-wonder), provide a link to the licence, and
  indicate if changes were made.

  ShareAlike. If you remix, transform, or build upon the content, you must
  distribute your contributions under this same CC BY-SA 4.0 licence.

  No additional restrictions. You may not apply legal terms or technological
  measures that legally restrict others from doing anything the licence permits.

The full legal code is at https://creativecommons.org/licenses/by-sa/4.0/legalcode
and the human-readable summary at https://creativecommons.org/licenses/by-sa/4.0/.

By contributing content to this project, you agree to license your contribution
under CC BY-SA 4.0 (and any code contribution under MIT).
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_licenses.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add LICENSE LICENSE-CONTENT tests/test_licenses.py
git commit -m "docs: add MIT (code) and CC BY-SA 4.0 (content) licences"
git push origin main
```

---

### Task 5: Wire the colophon, footer, metadata, and version into the Guide

**Files:**
- Modify: `build/render/pages.py`
- Modify: `build/__main__.py`
- Test: `tests/test_cli_render.py`

- [ ] **Step 1: Write the failing test**

Replace the two guide tests in `tests/test_cli_render.py` with versions that assert the new path under `guides/` with the `-v<n>` suffix (a tmp `sample_repo` is not a git repo, so the version is `v0`):

```python
def test_render_guide_builds_under_guides_with_version(sample_repo, tmp_path):
    guide_dir = sample_repo / "guide" / "en-GB"
    guide_dir.mkdir(parents=True)
    (guide_dir / "guide.md").write_text("# Guide\n\nThree jobs.\n", encoding="utf-8")
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "guides" / "Guide_for_the_Grown-Up_en-GB-v0.pdf").is_file()


def test_render_guide_missing_markdown_returns_one(sample_repo, tmp_path):
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "es-ES", "--out-dir", str(tmp_path),
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py::test_render_guide_builds_under_guides_with_version -v`
Expected: FAIL (the guide is currently written flat as `Guide_for_the_Grown-Up_en-GB.pdf`).

- [ ] **Step 3: Update `render_guide` to add the colophon, footer, metadata, and version**

In `build/render/pages.py`, update the imports at the top:

```python
from reportlab.platypus import PageBreak, SimpleDocTemplate

from build.models import World
from build.render import colophon, flowables, fonts, footer, theme
from build.render import markdown as md
from build.render import strings
from build.render.version import VersionInfo
```

Replace `render_guide` with:

```python
def render_guide(
    src: Path,
    out_path: Path,
    locale: str = "en-GB",
    *,
    version: VersionInfo | None = None,
    qr_url: str = colophon.PROJECT_URL,
) -> Path:
    """Render the world-agnostic Guide for the Grown-Up to a themed PDF.

    The guide is shared across worlds, so it uses the default theme and family
    (DejaVu covers en-GB and es-ES). It ends with the colophon page and is stamped
    with the per-page footer and PDF metadata.
    """
    version = version or VersionInfo(0, "unreleased")
    faces = fonts.resolve_faces(None, locale)
    th = theme.Theme.default()
    styles = theme.make_styles(th, faces)
    blocks = md.parse_markdown(src.read_text(encoding="utf-8"))
    flows = flowables.blocks_to_flowables(blocks, styles, th)
    label = strings.ui(locale, "colophon_artifact_guide")
    flows.append(PageBreak())
    flows.extend(colophon.colophon_flowables(styles, locale, version, label, qr_url))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = _doc(out_path, landscape_page=False)
    paint = theme.page_painter(th)
    doc.build(list(flows), onFirstPage=paint, onLaterPages=paint)
    footer.stamp_footers(
        out_path, identity=f"Wits and Wonder · {label}", locale=locale,
        version_info=version,
    )
    footer.set_metadata(
        out_path, title=f"{label}, {locale}, {version.label}",
        subject=f"Guide for the Grown-Up, {version.label}, {version.updated}",
        keywords=f"wits-and-wonder, guide, {locale}",
    )
    return out_path
```

- [ ] **Step 4: Update the `render-guide` CLI command**

In `build/__main__.py`, replace the `render-guide` command block with:

```python
    if args.command == "render-guide":
        from build.render import pages, version as ver
        from build.render.colophon import PROJECT_URL

        src = args.root / "guide" / args.locale / "guide.md"
        if not src.is_file():
            print(f"no guide markdown at {src}")
            return 1
        out_dir = args.out_dir if args.out_dir is not None else args.root / "dist"
        vi = ver.version_info(args.root, ver.guide_inputs(args.root, args.locale))
        out = out_dir / "guides" / f"Guide_for_the_Grown-Up_{args.locale}-{vi.label}.pdf"
        qr = f"{PROJECT_URL}/tree/main/kits/guides"
        pages.render_guide(src, out, args.locale, version=vi, qr_url=qr)
        print(f"built {out}")
        return 0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py tests/test_render_guide.py -v`
Expected: PASS (the `test_render_guide.py` tests still pass because they assert `>= 1` pages; the guide now has a colophon page too).

- [ ] **Step 6: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS.

- [ ] **Step 7: Manually verify the guide colophon, footer, and QR**

Run:
```bash
.venv/bin/python -m build render-guide --root . --locale en-GB --out-dir /tmp/g
pdftoppm -png -r 110 "$(ls /tmp/g/guides/*.pdf)" /tmp/guide
```
Open the last `/tmp/guide-*.png`: confirm the colophon shows the project link, the CC BY-SA 4.0 line, the version, and a scannable QR, and that every page has the grey footer with `page x of y`.

- [ ] **Step 8: Commit**

```bash
git add build/render/pages.py build/__main__.py tests/test_cli_render.py
git commit -m "feat(render): guide gains colophon, footer, metadata, and versioned path"
git push origin main
```

---

## Self-Review

- **Spec coverage (Parts 6 to 8):** `version.py` is the git-derived version with per-artifact input helpers (Part 6); `colophon.py` is the end page with the QR (Part 7); `footer.py` is the per-page footer stamping plus metadata (Part 8); `LICENSE`/`LICENSE-CONTENT` are the dual licence (Part 7). The Guide proves all four end to end.
- **Deviation:** the kit is not wired here (it becomes the Story Pack in Plan 3 and adopts the same helpers), avoiding double wiring; noted at the top.
- **Placeholder scan:** none; full code for every module and test.
- **Type consistency:** `VersionInfo(number, updated, dirty)` with `.label`; `colophon_flowables(styles, locale, version_info, artifact_label, qr_url)`; `footer.stamp_footers(pdf_path, *, identity, locale, version_info)` and `footer.set_metadata(pdf_path, *, title, subject, keywords, author=...)`; `colophon.PROJECT_URL` reused by `pages.py` and the CLI. These exact signatures are consumed unchanged by Plans 3, 4, and 6.
