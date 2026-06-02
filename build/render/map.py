"""Render a map SVG to a single-page PDF via cairosvg, and resolve which map.

A kit can carry either a story map (specific to one adventure, for example the
Sleeping Garden's path of stops) or a world map (an overview of the whole
setting), and either may have a per-locale variant when the art has baked-in
text. find_map encodes the lookup order: the most specific and locale-matched
file wins. Canon-driven labels (spec section 9) are deferred, so until a locale
has its own map a kit in that locale simply omits the map rather than showing
another language's labels. The page keeps the SVG's own aspect ratio, so the map
is typically landscape and merges cleanly with the portrait content pages.
"""

from pathlib import Path

import cairosvg


def find_map(world_dir: Path, story_dir: Path, locale: str) -> Path | None:
    """Resolve the map for a (world, story, locale), or None if there is none.

    Order: story map for the locale, story map generic, world map for the locale,
    world map generic. A story map overrides a world map; a locale-specific file
    overrides a generic one.
    """
    candidates = (
        story_dir / "assets" / f"map.{locale}.svg",
        story_dir / "assets" / "map.svg",
        world_dir / "assets" / f"map.{locale}.svg",
        world_dir / "assets" / "map.svg",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def render_svg_to_pdf(svg_path: Path, out_path: Path) -> Path:
    """Convert an SVG file to a one-page PDF at out_path. Returns out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(out_path))
    return out_path
