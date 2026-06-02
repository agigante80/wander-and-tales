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

import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import defusedxml.ElementTree as DefusedET

_SVG_NS = "http://www.w3.org/2000/svg"
_LINE_DY = 15  # vertical gap between wrapped label lines, in SVG user units


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


def template_keys(svg_path: Path) -> list[str]:
    """Return every data-label value in the template, in document order."""
    root = DefusedET.parse(svg_path).getroot()
    return [
        element.get("data-label")
        for element in root.iter()
        if element.get("data-label") is not None
    ]


def fill_template(svg_text: str, labels: dict[str, str]) -> str:
    """Write localized text into the data-label placeholders and return the SVG.

    A node with data-wrap="N" has its text balanced into up to N centered tspans.
    The data-label and data-wrap attributes are stripped from the output. Nodes
    without a data-label are left untouched, so a plain SVG comes back unchanged.

    Parsing uses defusedxml so a malicious contributed SVG cannot mount an XXE or
    entity-expansion attack; building and serializing use the stdlib ElementTree.
    """
    ET.register_namespace("", _SVG_NS)
    root = DefusedET.fromstring(svg_text)
    for element in root.iter():
        key = element.get("data-label")
        if key is None:
            continue
        text = labels.get(key, "")
        wrap = element.get("data-wrap")
        element.text = None
        for child in list(element):
            element.remove(child)
        if wrap:
            x = element.get("x", "0")
            for index, line in enumerate(_wrap(text, int(wrap))):
                tspan = ET.SubElement(element, f"{{{_SVG_NS}}}tspan")
                tspan.set("x", x)
                tspan.set("dy", "0" if index == 0 else str(_LINE_DY))
                tspan.text = line
        else:
            element.text = text
        for attribute in ("data-label", "data-wrap"):
            element.attrib.pop(attribute, None)
    return ET.tostring(root, encoding="unicode")


def render_map_template(svg_path: Path, out_path: Path, labels: dict[str, str]) -> Path:
    """Fill a template SVG with localized labels and render it to a one-page PDF."""
    filled = fill_template(svg_path.read_text(encoding="utf-8"), labels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(bytestring=filled.encode("utf-8"), write_to=str(out_path))
    return out_path
