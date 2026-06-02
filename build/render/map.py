"""Render a world map SVG to a single-page PDF via cairosvg.

Canon-driven map labels are deferred (spec section 9); for now the SVG art is
rendered as authored. The page keeps the SVG's own aspect ratio, so the map is
typically landscape and merges cleanly with the portrait content pages.
"""

from pathlib import Path

import cairosvg


def render_svg_to_pdf(svg_path: Path, out_path: Path) -> Path:
    """Convert an SVG file to a one-page PDF at out_path. Returns out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(out_path))
    return out_path
