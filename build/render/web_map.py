"""Render each story's trail map to a standalone PNG for the website.

The map is normally drawn only into the Atlas PDF (a hand-drawn template SVG via
cairosvg, or a generated trail map via mapgen). The website wants the map as an
image on the story page, so this re-uses the same map logic, renders it to a
single-page PDF, and rasterizes that to PNG with pdftoppm.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from build import content
from build.locales import REQUIRED_LOCALES
from build.render import theme
from build.render import map as kit_map, mapgen
from build.render.kit import _map_label

# Warm paper beige. The map page is rendered on pure white; in the browser that reads
# too stark next to the cream/dark theme, so we replace the near-white pixels with this.
_PAPER = (237, 228, 208)


def _recolor_background(src: Path, dst: Path, paper: tuple = _PAPER, cutoff: int = 248) -> None:
    """Repaint the near-white background of a rasterized map to a warm beige.

    Only pixels where every channel is near-white become beige, so the trail,
    markers, labels, and the tinted scenery shapes are untouched.
    """
    im = Image.open(src).convert("RGB")
    r, g, b = im.split()
    near = lambda ch: ch.point(lambda v: 255 if v >= cutoff else 0)
    mask = ImageChops.multiply(ImageChops.multiply(near(r), near(g)), near(b))
    Image.composite(Image.new("RGB", im.size, paper), im, mask).save(dst)


def render_story_map_png(
    root: Path, world_id: str, story_id: str, locale: str, out_png: Path, dpi: int = 150
) -> Path:
    """Render one story's map for one locale to a PNG."""
    world_dir = root / "worlds" / world_id
    story_dir = world_dir / "stories" / story_id
    world = content.load_world(world_dir / "world.yaml")
    story = content.load_story(story_dir / "story.yaml")
    canon = content.load_canon(world_dir / "canon")
    th = theme.Theme.from_world(world)
    title = story.title.get(locale, story.id)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        map_pdf = tmp_path / "map.pdf"

        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            canon_by_id = {entry.id: entry for entry in canon}
            labels = {
                key: _map_label(key, story, canon_by_id, locale)
                for key in kit_map.template_keys(map_svg)
            }
            kit_map.render_map_template(map_svg, map_pdf, labels)
        else:
            mapgen.render_generated_map(
                map_pdf, locale, title,
                story_dir / "content" / locale / "narration.simple.md", th,
            )

        prefix = tmp_path / "out"
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-singlefile", str(map_pdf), str(prefix)],
            check=True, capture_output=True,
        )
        _recolor_background(Path(str(prefix) + ".png"), out_png)
    return out_png


def render_all_maps(root: Path, out_root: Path, locales: list[str] | None = None) -> int:
    """Render every story map for every required locale into out_root/<world>/<story>/map-<locale>.png."""
    locales = locales or list(REQUIRED_LOCALES)
    count = 0
    worlds_dir = root / "worlds"
    for world_dir in sorted(p for p in worlds_dir.iterdir() if p.is_dir()):
        stories_dir = world_dir / "stories"
        if not stories_dir.is_dir():
            continue
        for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
            for locale in locales:
                out_png = out_root / world_dir.name / story_dir.name / f"map-{locale}.png"
                render_story_map_png(root, world_dir.name, story_dir.name, locale, out_png)
                count += 1
    return count
