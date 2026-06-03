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
    # Drop any directory left empty by a removed story or world, deepest first.
    for directory in sorted(out_dir.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
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
