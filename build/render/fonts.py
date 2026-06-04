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


@dataclass(frozen=True)
class SheetFaces:
    """The character sheet's fixed typeface set, the same across worlds (the world
    identity on a sheet comes from its palette, not its prose face): a rounded
    display face for headings, a clean body face, and a handwriting face for the
    pre-filled example answers so a filled sheet reads differently from a blank one."""

    display: str
    body: str
    body_bold: str
    hand: str


_registered: set[str] = set()

# Vendored OFL faces for the sheet (instanced static weights under assets/fonts/).
_SHEET_FONTS = {
    "ww-display": "Quicksand-SemiBold.ttf",
    "ww-body": "Nunito-Regular.ttf",
    "ww-body-bold": "Nunito-Bold.ttf",
    "ww-hand": "Caveat-SemiBold.ttf",
}


def sheet_faces() -> SheetFaces:
    """Register and return the sheet typeface set. Falls back to the default family
    if the vendored OFL TTFs are absent, so the build never breaks on a missing font."""
    names = SheetFaces("ww-display", "ww-body", "ww-body-bold", "ww-hand")
    if "ww-sheet" in _registered:
        return names
    try:
        for font_name, filename in _SHEET_FONTS.items():
            pdfmetrics.registerFont(
                TTFont(font_name, str(fontspec.font_path(filename)))
            )
        _registered.add("ww-sheet")
        return names
    except Exception:
        f = register_family(fontspec.DEFAULT_FAMILY)
        return SheetFaces(display=f.bold, body=f.normal, body_bold=f.bold, hand=f.italic)


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
