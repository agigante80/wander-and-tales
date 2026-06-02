"""Font registry: the single source of truth for which typefaces exist.

A family is a named set of four TTF faces (regular, bold, italic, bold-italic).
Worlds choose a family by key in world.yaml; the model validates against
KNOWN_FAMILIES here, and the renderer registers the faces with reportlab. This
module is pure (pathlib only) so the model can import it without pulling in any
rendering dependency. Add a new typeface by vendoring its TTFs and adding one
entry below.
"""

from dataclasses import dataclass
from pathlib import Path

FONT_DIR = Path(__file__).parent / "assets" / "fonts"


@dataclass(frozen=True)
class FaceFiles:
    normal: str
    bold: str
    italic: str
    bold_italic: str


FAMILIES: dict[str, FaceFiles] = {
    "dejavu-sans": FaceFiles(
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique.ttf",
    ),
    "dejavu-serif": FaceFiles(
        "DejaVuSerif.ttf",
        "DejaVuSerif-Bold.ttf",
        "DejaVuSerif-Italic.ttf",
        "DejaVuSerif-BoldItalic.ttf",
    ),
}

DEFAULT_FAMILY = "dejavu-sans"
KNOWN_FAMILIES = tuple(FAMILIES)


def faces_for(family: str) -> FaceFiles:
    """Return the four face filenames for a family. Raises KeyError if unknown."""
    return FAMILIES[family]


def font_path(filename: str) -> Path:
    """Absolute path to a vendored TTF by filename."""
    return FONT_DIR / filename
