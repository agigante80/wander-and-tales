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
from build.render import examples, kit, pages, playbook, version, world_pdf
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
    example_heroes: dict = field(default_factory=dict)  # (world, locale) -> Path
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
            if (world_yaml.parent / "heroes.yaml").is_file():
                built.example_heroes[(world_id, locale)] = examples.build_example_heroes(
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
    for mapping in (
        built.story_packs, built.playbooks, built.world_books,
        built.example_heroes, built.guides,
    ):
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


# Localized labels for the per-language download links in the catalogue cell.
_LEVEL_LABELS = {
    "en-GB": {"simple": "Simple", "rich": "Rich", "playbook": "Playbook"},
    "es-ES": {"simple": "Sencillo", "rich": "Completo", "playbook": "Cuaderno"},
    "it-IT": {"simple": "Semplice", "rich": "Completo", "playbook": "Quaderno"},
}


def readme_block(root: Path, built: Built) -> str:
    """Render the README catalogue and download block (between the markers).

    One row per story carries its tags (ages, skills, peril, time) and the download
    links for every language, so the README is the single browse-and-download view.
    """
    stories: dict = {}
    for (world_id, story_id, locale, level), path in built.story_packs.items():
        stories.setdefault((world_id, story_id), {}).setdefault(locale, {})[level] = path
    for (world_id, story_id, locale), path in built.playbooks.items():
        stories.setdefault((world_id, story_id), {}).setdefault(locale, {})["playbook"] = path

    stories_by_world: dict = {}
    for world_id, story_id in stories:
        stories_by_world.setdefault(world_id, []).append(story_id)
    world_books: dict = {}
    for (world_id, locale), path in built.world_books.items():
        world_books.setdefault(world_id, {})[locale] = path
    hero_books: dict = {}
    for (world_id, locale), path in built.example_heroes.items():
        hero_books.setdefault(world_id, {})[locale] = path

    locales = ("en-GB", "es-ES", "it-IT")

    def _lang_links(by_locale: dict) -> str:
        return " · ".join(
            f"[{_LANG_NAME.get(loc, loc)}]({_rel(root, by_locale[loc])})"
            for loc in locales
            if loc in by_locale
        )

    header = (
        "| Story | Ages | Peril | Time | Skills | "
        + " | ".join(_LANG_NAME[loc] for loc in locales)
        + " |"
    )
    divider = "|" + "---|" * (5 + len(locales))

    lines = [
        README_BEGIN,
        "",
        "Every story is cooperative and no-lose, for two or more (a grown-up and one",
        "or more children), and playable with a single ordinary die. Each kit comes in",
        "three languages: pick a Story Pack to play from, the Grown-up's Playbook for the",
        "answers, and the World Book for the lore.",
    ]
    if built.guides:
        guide_links = " · ".join(
            f"[{_LANG_NAME.get(loc, loc)}]({_rel(root, path)})"
            for loc, path in sorted(built.guides.items())
        )
        lines += [
            "",
            f"**New to running a game like this?** Read the Guide for the Grown-Up: {guide_links}.",
        ]
    for world_id in sorted(stories_by_world):
        world = content.load_world(root / "worlds" / world_id / "world.yaml")
        world_name = world.name.get("en-GB", world_id)
        lines += ["", f"### {world_name}", ""]
        if world_id in world_books:
            lines += [f"**World Book:** {_lang_links(world_books[world_id])}", ""]
        if world_id in hero_books:
            lines += [f"**Example heroes:** {_lang_links(hero_books[world_id])}", ""]
        lines += [header, divider]
        loaded = {
            sid: content.load_story(
                root / "worlds" / world_id / "stories" / sid / "story.yaml"
            )
            for sid in stories_by_world[world_id]
        }
        for story_id in sorted(
            stories_by_world[world_id],
            key=lambda sid: loaded[sid].title.get("en-GB", sid),
        ):
            story = loaded[story_id]
            title = story.title.get("en-GB", story_id)
            ages = _AGE_RANGE.get(story.age.recommended, "")
            skills = ", ".join(story.skills)
            time = f"{story.play_time_minutes} min"
            cols = []
            for loc in locales:
                files = stories[(world_id, story_id)].get(loc, {})
                labels = _LEVEL_LABELS.get(loc, _LEVEL_LABELS["en-GB"])
                parts = [
                    f"[{labels[kind]}]({_rel(root, files[kind])})"
                    for kind in ("simple", "rich", "playbook")
                    if kind in files
                ]
                cols.append(" · ".join(parts))
            lines.append(
                f"| {title} | {ages} | {story.peril} | {time} | {skills} | "
                + " | ".join(cols)
                + " |"
            )

    lines += ["", README_END]
    return "\n".join(lines)


def apply_readme_block(readme_path: Path, block: str) -> None:
    """Replace the text between the README markers with `block`, leaving the rest."""
    text = readme_path.read_text(encoding="utf-8")
    start = text.index(README_BEGIN)
    end = text.index(README_END) + len(README_END)
    readme_path.write_text(text[:start] + block + text[end:], encoding="utf-8")


def rebuild(root: Path, out_dir: Path) -> Built:
    """Build the library, prune old versions, and rewrite the README catalogue."""
    built = build_all(root, out_dir)
    prune_old(out_dir, built)
    apply_readme_block(root / "README.md", readme_block(root, built))
    return built
