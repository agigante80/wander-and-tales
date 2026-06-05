"""Build a world's example-hero sheets: four pre-filled adventure sheets per locale.

Two young and two older example heroes, each rendered as a filled character sheet
with its name, chosen magics or qualities (resolved from canon), energy stars, carried
items, and a drawn hero portrait. The four sheets are merged into one A4 PDF per world
per locale, ready to print and play or to use as inspiration.
"""

import tempfile
from pathlib import Path

from build import content
from build.render import footer, sheets, strings, theme, version
from build.render.kit import _merge


def build_example_heroes(
    root: Path,
    world_id: str,
    locale: str,
    *,
    out_dir: Path | None = None,
    version_info: version.VersionInfo | None = None,
) -> Path:
    """Build the example-heroes PDF for a (world, locale) and return its path."""
    world_dir = root / "worlds" / world_id
    world = content.load_world(world_dir / "world.yaml")
    canon = {entry.id: entry for entry in content.load_canon(world_dir / "canon")}
    heroes = content.load_heroes(world_dir)

    th = theme.Theme.from_world(world)

    if version_info is None:
        version_info = version.version_info(
            root,
            version.example_heroes_inputs(root, world_id, locale),
            version.render_sources(root),
        )

    out_dir = out_dir if out_dir is not None else root / "dist"
    world_name = world.name.get(locale, world_id)

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, hero in enumerate(heroes):
            magics = []
            for magic_id in hero.magics:
                entry = canon.get(magic_id)
                name = entry.names.get(locale, magic_id) if entry else magic_id
                does = (entry.description or {}).get(locale, "") if entry else ""
                magics.append((name, does))
            example = {
                "name": hero.name,
                "hero_of": hero.hero_of.get(locale, ""),
                "magics": magics,
                "energy": hero.energy,
                "carry": [item.get(locale, "") for item in hero.carry],
            }
            image_path = world_dir / "assets" / f"{hero.image.id}.png"
            hero_image = image_path if image_path.is_file() else None
            sheet = tmp_path / f"{index:02d}_{hero.id}.pdf"
            sheets.render_character_sheet(
                sheet, locale, hero.tier, th, world_name=world_name,
                powers=world.hero_powers, example=example, hero_image=hero_image,
            )
            parts.append(sheet)

        out_path = (
            out_dir / locale / world_id / f"example-heroes-{version_info.label}.pdf"
        )
        _merge(parts, out_path)

    label = strings.ui(locale, "examples_title")
    footer.stamp_footers(
        out_path, identity=f"Wander and Tales · {label} · {world_name}",
        locale=locale, version_info=version_info,
    )
    footer.set_metadata(
        out_path,
        title=f"{world_name}, {label}, {locale}, {version_info.label}",
        subject=f"Example Heroes, {version_info.label}, {version_info.updated}",
        keywords=f"{world_id}, {locale}, example-heroes, {version_info.label}",
    )
    return out_path
