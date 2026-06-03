# Plan 6: Rebuild, README Generation, and Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `rebuild` command that builds the whole library into the language-first `kits/` tree, prunes superseded versions, regenerates the catalogue, and rewrites the README download block; update the README, CONTRIBUTING, PR template, and the two authoring skills; point the release workflow at `rebuild`; and do the first real library rebuild.

**Architecture:** A new `build/render/library.py` orchestrates the per-artifact builders from Plans 3 and 4 plus the guide from Plan 2, collects the results, prunes stale versioned PDFs, and generates the README table between HTML-comment markers. The `rebuild` CLI command wires it to the catalogue and the README. Docs are brought in line with the three-artifact, world-level-idea-bank, automatic-version reality.

**Tech Stack:** Python 3.11, pytest, GitHub Actions, Markdown.

Spec: `docs/superpowers/specs/2026-06-03-print-presentation-and-world-pdf-design.md` (Part 6 rebuild, "The README", Part 7 licensing, Impact list). Depends on Plans 1 to 5.

---

## File Structure

- `build/render/library.py` (create): `build_all`, `prune_old`, `readme_block`, `apply_readme_block`, `rebuild`, and the `Built` dataclass.
- `build/__main__.py` (modify): add the `rebuild` command.
- `README.md` (modify): markers around the generated table, the split note, the Licence section, the updated command list and `kits/` description.
- `CONTRIBUTING.md` (modify): a licensing line.
- `.github/pull_request_template.md` (modify): a licensing checkbox.
- `.claude/skills/authoring-story-content/SKILL.md` (modify): world-level idea bank, three artifacts, automatic version.
- `.claude/skills/create-story/SKILL.md` (modify): author the idea bank once per world.
- `.github/workflows/build-art.yml` (modify): call `python -m build rebuild`.
- Tests: `tests/test_render_library.py` (create).

---

### Task 1: The library orchestrator

**Files:**
- Create: `build/render/library.py`
- Test: `tests/test_render_library.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_library.py`:

```python
from build.render import library


def test_build_all_creates_every_artifact(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    assert (out_dir / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.pdf").is_file()
    assert (out_dir / "en-GB" / "floating-isles" / "sleeping-garden" / "playbook-v0.pdf").is_file()
    assert (out_dir / "en-GB" / "floating-isles" / "world-book-v0.pdf").is_file()
    assert ("floating-isles", "sleeping-garden", "es-ES", "rich") in built.story_packs


def test_prune_removes_superseded_versions(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    stale = out_dir / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v9.pdf"
    stale.write_bytes(b"%PDF-stale")
    removed = library.prune_old(out_dir, built)
    assert stale in removed
    assert not stale.exists()
    # the current version survives
    assert (out_dir / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.pdf").is_file()


def test_readme_block_lists_stories_and_links(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    block = library.readme_block(sample_repo, built)
    assert library.README_BEGIN in block
    assert library.README_END in block
    assert "The Sleeping Garden" in block
    assert "story-pack-simple-v0.pdf" in block
    assert "World books" in block


def test_apply_readme_block_replaces_only_between_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# Title\n\nIntro.\n\n{library.README_BEGIN}\nold\n{library.README_END}\n\nFooter.\n",
        encoding="utf-8",
    )
    library.apply_readme_block(readme, f"{library.README_BEGIN}\nNEW\n{library.README_END}")
    text = readme.read_text(encoding="utf-8")
    assert "NEW" in text
    assert "old" not in text
    assert "# Title" in text
    assert "Footer." in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_library.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.render.library'`.

- [ ] **Step 3: Implement `library.py`**

Create `build/render/library.py`:

```python
"""Build the whole committed library and regenerate the README download block.

Walks the content tree, builds every artifact into the language-first kits/ tree,
prunes superseded versioned files, regenerates the catalogue, and rewrites the README
download section between its markers. Used by the `rebuild` CLI and the release
workflow.
"""

from dataclasses import dataclass, field
from pathlib import Path

from build import content
from build.locales import REQUIRED_LOCALES
from build.render import kit, pages, playbook, version, world_pdf
from build.render.colophon import PROJECT_URL

LEVELS = ("simple", "rich")
README_BEGIN = "<!-- BEGIN KIT TABLE -->"
README_END = "<!-- END KIT TABLE -->"

_LANG_NAME = {"en-GB": "English", "es-ES": "Español", "it-IT": "Italiano"}
_AGE_RANGE = {"early": "3 to 5", "young": "6 to 8", "older": "9 to 12"}


@dataclass
class Built:
    story_packs: dict = field(default_factory=dict)  # (world, story, locale, level) -> Path
    playbooks: dict = field(default_factory=dict)    # (world, story, locale) -> Path
    world_books: dict = field(default_factory=dict)  # (world, locale) -> Path
    guides: dict = field(default_factory=dict)       # locale -> Path


def build_all(root: Path, out_dir: Path) -> Built:
    """Build every artifact for every world, story, locale, and level."""
    built = Built()
    worlds_dir = root / "worlds"
    for world_yaml in sorted(worlds_dir.glob("*/world.yaml")):
        world_id = world_yaml.parent.name
        stories = sorted((world_yaml.parent / "stories").glob("*/story.yaml"))
        for locale in REQUIRED_LOCALES:
            built.world_books[(world_id, locale)] = world_pdf.build_world_pdf(
                root, world_id, locale, out_dir=out_dir
            )
            for story_yaml in stories:
                story_id = story_yaml.parent.name
                built.playbooks[(world_id, story_id, locale)] = playbook.build_playbook(
                    root, world_id, story_id, locale, out_dir=out_dir
                )
                for level in LEVELS:
                    built.story_packs[(world_id, story_id, locale, level)] = (
                        kit.build_story_pack(
                            root, world_id, story_id, locale, level, out_dir=out_dir
                        )
                    )
    for locale in REQUIRED_LOCALES:
        guide_md = root / "guide" / locale / "guide.md"
        if guide_md.is_file():
            vi = version.version_info(root, version.guide_inputs(root, locale))
            out = out_dir / "guides" / f"Guide_for_the_Grown-Up_{locale}-{vi.label}.pdf"
            qr = f"{PROJECT_URL}/tree/main/kits/guides"
            built.guides[locale] = pages.render_guide(guide_md, out, locale, version=vi, qr_url=qr)
    return built


def prune_old(out_dir: Path, built: Built) -> list[Path]:
    """Remove every *.pdf under out_dir that the build did not just write."""
    keep = set()
    for mapping in (built.story_packs, built.playbooks, built.world_books, built.guides):
        keep.update(p.resolve() for p in mapping.values())
    removed: list[Path] = []
    for pdf in sorted(out_dir.rglob("*.pdf")):
        if pdf.resolve() not in keep:
            pdf.unlink()
            removed.append(pdf)
    return removed


def _rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def readme_block(root: Path, built: Built) -> str:
    """Render the README download block (between the markers) from the built tree."""
    rows: dict = {}
    for (world_id, story_id, locale, level), path in built.story_packs.items():
        rows.setdefault((world_id, story_id, locale), {})[level] = path

    lines = [
        README_BEGIN,
        "",
        "| Story | World | Language | Ages | Story Pack | Grown-up's Playbook |",
        "|---|---|---|---|---|---|",
    ]
    for key in sorted(rows):
        world_id, story_id, locale = key
        story = content.load_story(
            root / "worlds" / world_id / "stories" / story_id / "story.yaml"
        )
        world = content.load_world(root / "worlds" / world_id / "world.yaml")
        title = story.title.get(locale, story_id)
        world_name = world.name.get(locale, world_id)
        ages = _AGE_RANGE.get(story.age.recommended, "")
        lang = _LANG_NAME.get(locale, locale)
        pack_links = " · ".join(
            f"[{name}]({_rel(root, rows[key][lvl])})"
            for name, lvl in (("Simple", "simple"), ("Rich", "rich"))
            if lvl in rows[key]
        )
        playbook_path = built.playbooks.get((world_id, story_id, locale))
        playbook_link = f"[Open]({_rel(root, playbook_path)})" if playbook_path else ""
        lines.append(
            f"| {title} | {world_name} | {lang} | {ages} | {pack_links} | {playbook_link} |"
        )

    lines += ["", "### World books", ""]
    world_rows: dict = {}
    for (world_id, locale), path in built.world_books.items():
        world_rows.setdefault(world_id, {})[locale] = path
    for world_id in sorted(world_rows):
        world = content.load_world(root / "worlds" / world_id / "world.yaml")
        name = world.name.get("en-GB", world_id)
        links = " · ".join(
            f"[{_LANG_NAME.get(loc, loc)}]({_rel(root, path)})"
            for loc, path in sorted(world_rows[world_id].items())
        )
        lines.append(f"- {name}: {links}")

    if built.guides:
        guide_links = " · ".join(
            f"[{_LANG_NAME.get(loc, loc)}]({_rel(root, path)})"
            for loc, path in sorted(built.guides.items())
        )
        lines += [
            "",
            f"**New to running a game like this?** Read the Guide for the Grown-Up: {guide_links}.",
        ]

    lines += ["", README_END]
    return "\n".join(lines)


def apply_readme_block(readme_path: Path, block: str) -> None:
    """Replace the text between the README markers with `block`, leaving the rest."""
    text = readme_path.read_text(encoding="utf-8")
    start = text.index(README_BEGIN)
    end = text.index(README_END) + len(README_END)
    readme_path.write_text(text[:start] + block + text[end:], encoding="utf-8")


def rebuild(root: Path, out_dir: Path) -> Built:
    """Build the library, prune old versions, regenerate the catalogue and README."""
    from build import catalog

    built = build_all(root, out_dir)
    prune_old(out_dir, built)
    catalog.write_catalog(list(content.iter_stories(root / "worlds")), root / "catalog.md")
    apply_readme_block(root / "README.md", readme_block(root, built))
    return built
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_render_library.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/library.py tests/test_render_library.py
git commit -m "feat(render): library orchestrator, version pruning, README block generator"
git push origin main
```

---

### Task 2: The `rebuild` CLI command

**Files:**
- Modify: `build/__main__.py`
- Test: `tests/test_cli_render.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli_render.py`:

```python
def test_rebuild_builds_the_library_and_rewrites_readme(sample_repo):
    from build.__main__ import main

    # the rebuild rewrites README.md between markers, so seed one
    (sample_repo / "README.md").write_text(
        "# Wits and Wonder\n\n<!-- BEGIN KIT TABLE -->\nold\n<!-- END KIT TABLE -->\n\nEnd.\n",
        encoding="utf-8",
    )
    code = main(["rebuild", "--root", str(sample_repo), "--out-dir", str(sample_repo / "kits")])
    assert code == 0
    assert (
        sample_repo / "kits" / "en-GB" / "floating-isles" / "world-book-v0.pdf"
    ).is_file()
    readme = (sample_repo / "README.md").read_text(encoding="utf-8")
    assert "The Sleeping Garden" in readme
    assert "old" not in readme
    assert "End." in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py::test_rebuild_builds_the_library_and_rewrites_readme -v`
Expected: FAIL (`invalid choice: 'rebuild'`).

- [ ] **Step 3: Add the `rebuild` command**

In `build/__main__.py`, add the parser (after the `render-world` parser):

```python
    rebuild_parser = sub.add_parser(
        "rebuild", help="build the whole library, prune old versions, refresh README and catalogue"
    )
    _add_root(rebuild_parser)
    rebuild_parser.add_argument("--out-dir", type=Path, default=None)
```

and the command block (after the `render-world` block):

```python
    if args.command == "rebuild":
        from build.render import library

        out_dir = args.out_dir if args.out_dir is not None else args.root / "kits"
        built = library.rebuild(args.root, out_dir)
        total = (
            len(built.story_packs) + len(built.playbooks)
            + len(built.world_books) + len(built.guides)
        )
        print(f"rebuilt {total} artifact(s) into {out_dir}")
        return 0
```

Update the module docstring (line 1) to include `rebuild`:

```python
"""Command line: python -m build {validate,lint,catalog,render,render-guide,render-playbook,render-world,rebuild,prompts,generate-images}."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/__main__.py tests/test_cli_render.py
git commit -m "feat(cli): rebuild command for the whole library"
git push origin main
```

---

### Task 3: README, CONTRIBUTING, and PR template

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `.github/pull_request_template.md`

- [ ] **Step 1: Replace the download section with the markers and the split note**

In `README.md`, replace the block that begins `Each kit is a single printable PDF.` and runs through the Guide callout paragraph (ending `It explains everything in about five minutes.`) with:

```markdown
Each story comes as a **Story Pack** (what you play from, safe for a child to see), a
**Grown-up's Playbook** (the rules and the puzzle answers), and each world has a
**World Book** (its lore, who's who, and idea bank). The **Simple** Story Pack reads
aloud well for ages 3 to 8; the **Rich** one suits ages 9 to 12. Every PDF shows its
version on the last page, and the links below are generated automatically.

<!-- BEGIN KIT TABLE -->
<!-- END KIT TABLE -->
```

(The `rebuild` command fills the table between the markers; do not hand-edit between them.)

- [ ] **Step 2: Add the three new commands to the Everyday commands block**

In `README.md`, in the `### Everyday commands` fenced block, replace the two render lines for the kit and guide with:

```bash
# build one printable Story Pack into dist/
python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple

python -m build render-playbook --root . --world floating-isles --story sleeping-garden --locale en-GB
python -m build render-world --root . --world floating-isles --locale en-GB
python -m build render-guide --root . --locale en-GB        # build the Guide PDF
python -m build rebuild --root .                            # build the whole library + refresh README
python -m build prompts --root .                            # export the image prompts
python -m build generate-images --root .                   # generate art (needs OPENAI_API_KEY)
```

- [ ] **Step 3: Update the `kits/` description**

In `README.md`, in the `### Where things live` list, replace the `kits/` bullet with:

```markdown
- `kits/` holds the built PDFs in a language-first tree:
  `kits/<locale>/<world>/world-book-v<n>.pdf` and
  `kits/<locale>/<world>/<story>/{story-pack-simple,story-pack-rich,playbook}-v<n>.pdf`,
  plus `kits/guides/`. `dist/` is the scratch build output and is not tracked.
```

- [ ] **Step 4: Add the Licence section**

In `README.md`, add this section immediately before the `## The promise` heading:

```markdown
## Licence

The **content** (everything under `worlds/`, `guide/`, and `lexicon/`, and the
generated PDFs in `kits/`) is licensed **CC BY-SA 4.0**: share and adapt it, even
commercially, with credit to Wits and Wonder, and keep derivatives under the same
licence. See [`LICENSE-CONTENT`](LICENSE-CONTENT) and
<https://creativecommons.org/licenses/by-sa/4.0/>.

The **code** (the `build/` package and `tests/`) is licensed **MIT**. See
[`LICENSE`](LICENSE).

By contributing, you agree to license your contribution under these same terms.
```

- [ ] **Step 5: Add a licensing line to CONTRIBUTING.md**

Append to `CONTRIBUTING.md`:

```markdown
## Licensing

By opening a pull request you agree that your contribution is offered under the
project licences: content under CC BY-SA 4.0 (`LICENSE-CONTENT`) and any code under
MIT (`LICENSE`). Please contribute only material you have the right to give.
```

- [ ] **Step 6: Add a licensing checkbox to the PR template**

Append to `.github/pull_request_template.md`:

```markdown
- [ ] I license this contribution under CC BY-SA 4.0 (content) and MIT (code), and it is mine to give.
```

- [ ] **Step 7: Verify the markers exist and commit**

Run: `grep -c "BEGIN KIT TABLE\|END KIT TABLE" README.md`
Expected: `2`.

```bash
git add README.md CONTRIBUTING.md .github/pull_request_template.md
git commit -m "docs: README split note, generated-table markers, and dual-licence section"
git push origin main
```

---

### Task 4: Update the authoring skills for the world-level idea bank

**Files:**
- Modify: `.claude/skills/authoring-story-content/SKILL.md`
- Modify: `.claude/skills/create-story/SKILL.md`

- [ ] **Step 1: Update the content-types table in `authoring-story-content/SKILL.md`**

In `.claude/skills/authoring-story-content/SKILL.md`, in the "Content types and where they live" table, replace the idea-bank row:

```markdown
| `worlds/<world>/content/<locale>/idea-bank.md` | adult GM | adult | world-level improv prompts; one per world, shared by its stories |
```

and add a sentence to the paragraph under the table (or just below it):

```markdown
The idea bank is world-level (one per world per locale), not per story; the narration,
rules, and puzzles remain per story. Version numbers, the colophon, and the licence are
added automatically at build time, so you never edit them.
```

- [ ] **Step 2: Update Step 5 in `create-story/SKILL.md`**

In `.claude/skills/create-story/SKILL.md`, in "Step 5: author the content", replace the per-story content bullet so the idea bank is not listed there:

```markdown
- `worlds/<world>/stories/<story>/content/<locale>/`: `narration.simple.md`,
  `narration.rich.md`, `rules.md`, `puzzles.md`.
```

and add a new bullet just below it:

```markdown
- `worlds/<world>/content/<locale>/idea-bank.md`: the world-level idea bank. Author it
  once when you create a world; when you add a story to an existing world, reuse the
  world's idea bank rather than writing a per-story one.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/authoring-story-content/SKILL.md .claude/skills/create-story/SKILL.md
git commit -m "docs(skills): author the idea bank at the world level"
git push origin main
```

---

### Task 5: Point the release workflow at `rebuild` and do the first real rebuild

**Files:**
- Modify: `.github/workflows/build-art.yml`
- Rebuild: `kits/`, `catalog.md`, `README.md`

- [ ] **Step 1: Replace the inline build loop in `build-art.yml`**

In `.github/workflows/build-art.yml`, replace the entire "Rebuild kits and the catalogue" step (the `run: |` block with the inline Python) with:

```yaml
      - name: Rebuild the library, the catalogue, and the README
        run: python -m build rebuild --root .
```

and update the commit step's `git add` line to include the README:

```yaml
          git add worlds kits catalog.md README.md
```

- [ ] **Step 2: Verify the workflow is valid YAML**

Run: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/build-art.yml')); print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Remove the old flat kits and run the real rebuild**

```bash
git rm -r --quiet kits
.venv/bin/python -m build rebuild --root . --out-dir kits
```

This builds the full language-first tree (the `git rm` clears the old flat files; `rebuild` also prunes any stray versioned PDFs), regenerates `catalog.md`, and rewrites the README table between the markers.

- [ ] **Step 4: Verify the result**

Run:
```bash
.venv/bin/python -m pytest && .venv/bin/python -m build lint --root .
find kits -name '*.pdf' | sort
grep -A3 "BEGIN KIT TABLE" README.md | head -8
```
Expected: the suite passes; `lint clean`; `kits/` holds the nested versioned tree (story packs, playbooks, world books, and `kits/guides/`); the README table between the markers lists the real stories with working links.

- [ ] **Step 5: Eyeball one of each real artifact**

```bash
pdftoppm -png -r 110 "$(find kits -name 'story-pack-rich-*.pdf' | head -1)" /tmp/sp
pdftoppm -png -r 110 "$(find kits -name 'playbook-*.pdf' | head -1)" /tmp/pb
pdftoppm -png -r 110 "$(find kits -name 'world-book-*.pdf' | head -1)" /tmp/wb
```
Confirm A4 white pages, the front page with the world paragraph, the colophon with the QR and version, the footer with `page x of y`, and the redesigned character sheet in the Story Pack.

- [ ] **Step 6: Commit the rebuilt library**

```bash
git add kits catalog.md README.md .github/workflows/build-art.yml
git commit -m "build: rebuild the library into the language-first versioned tree"
git push origin main
```

---

## Self-Review

- **Spec coverage:** `rebuild` builds all artifacts, prunes superseded versions, regenerates the catalogue, and rewrites the generated README block (Part 6, "The README"); the README gains the split note, the markers, and the Licence section (Part 7); CONTRIBUTING and the PR template carry the licence agreement (Part 7); the skills move the idea bank to the world level and note the automatic version/colophon/licence (Impact list); `build-art.yml` calls `rebuild`; the first real rebuild produces the committed tree.
- **Placeholder scan:** none; full code for `library.py` and exact edits elsewhere.
- **Type consistency:** `library.build_all/prune_old/readme_block/apply_readme_block/rebuild` and the `Built` dataclass are defined in Task 1 and used by the CLI in Task 2; they call `kit.build_story_pack`, `playbook.build_playbook`, `world_pdf.build_world_pdf`, `pages.render_guide`, `version.version_info`/`guide_inputs`, and `colophon.PROJECT_URL` with the exact signatures from Plans 2 to 4. `README_BEGIN`/`README_END` are the same constants the tests and `apply_readme_block` use.
- **Note:** the README edits in Task 3 must land before the real rebuild in Task 5, so `apply_readme_block` finds the markers; the task order enforces this.
