"""Register typefaces with reportlab and resolve the family for a world+locale.

The set of families and their TTF files comes from the fontspec vocabulary; this
module turns a family key into registered reportlab font names (one per face) and
applies the world's font choices. A face is named '<family>' for normal and
'<family>-bold', '<family>-italic', '<family>-bolditalic' for the rest.
"""

from dataclasses import dataclass

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from build import fontspec
from build.models import World


@dataclass(frozen=True)
class FontFaces:
    normal: str
    bold: str
    italic: str
    bold_italic: str


_registered: set[str] = set()


def register_family(family: str) -> FontFaces:
    """Register a family's four faces with reportlab. Safe to call repeatedly."""
    faces = FontFaces(
        normal=family,
        bold=f"{family}-bold",
        italic=f"{family}-italic",
        bold_italic=f"{family}-bolditalic",
    )
    if family in _registered:
        return faces
    files = fontspec.faces_for(family)
    pdfmetrics.registerFont(TTFont(faces.normal, str(fontspec.font_path(files.normal))))
    pdfmetrics.registerFont(TTFont(faces.bold, str(fontspec.font_path(files.bold))))
    pdfmetrics.registerFont(TTFont(faces.italic, str(fontspec.font_path(files.italic))))
    pdfmetrics.registerFont(
        TTFont(faces.bold_italic, str(fontspec.font_path(files.bold_italic)))
    )
    pdfmetrics.registerFontFamily(
        family,
        normal=faces.normal,
        bold=faces.bold,
        italic=faces.italic,
        boldItalic=faces.bold_italic,
    )
    _registered.add(family)
    return faces


def resolve_family(world: World | None, locale: str) -> str:
    """Family key for a world and locale: by_locale, then default, then global."""
    if world is not None and world.fonts is not None:
        if locale in world.fonts.by_locale:
            return world.fonts.by_locale[locale]
        return world.fonts.default
    return fontspec.DEFAULT_FAMILY


def resolve_faces(world: World | None, locale: str) -> FontFaces:
    """Resolve the family for a world+locale and register it, returning its faces."""
    return register_family(resolve_family(world, locale))
