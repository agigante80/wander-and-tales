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


def _wrap(text: str, max_lines: int) -> list[str]:
    """Split text on spaces into at most max_lines balanced lines, preserving order.

    One word stays on one line; a two-word name splits one word per line; a longer
    name is balanced as evenly as possible. No word is ever dropped.
    """
    words = text.split()
    if max_lines <= 1 or len(words) <= 1:
        return [text] if text else []
    lines_wanted = min(max_lines, len(words))
    per = len(words) / lines_wanted
    lines: list[str] = []
    start = 0
    for index in range(lines_wanted):
        end = round((index + 1) * per)
        lines.append(" ".join(words[start:end]))
        start = end
    return [line for line in lines if line]


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
