from reportlab.lib.colors import HexColor, white

from build.models import World
from build.render import fonts, theme


def test_page_fill_is_white():
    assert theme.PAGE_FILL == white


def _world():
    return World.model_validate(
        {
            "id": "floating-isles",
            "name": {"en-GB": "The Floating Isles", "es-ES": "Las Islas Flotantes",
                     "it-IT": "Le Isole Fluttuanti"},
            "palette": ["#fef9ef", "#4ea24a", "#2bb3a3", "#d36fb0",
                        "#3f8fd6", "#f2a93b", "#8a6fd6"],
        }
    )


def test_theme_from_world_maps_palette_by_role():
    th = theme.Theme.from_world(_world())
    assert th.background == HexColor("#fef9ef")
    assert th.primary == HexColor("#4ea24a")


def test_theme_default_fills_in_when_palette_is_short():
    bare = World.model_validate(
        {"id": "x", "name": {"en-GB": "X", "es-ES": "X", "it-IT": "X"}, "palette": []}
    )
    th = theme.Theme.from_world(bare)
    assert th.background is not None and th.primary is not None


def test_make_styles_binds_body_to_faces_and_headings_to_display():
    faces = fonts.register_family("dejavu-serif")
    styles = theme.make_styles(theme.Theme.default(), faces)
    # body prose stays in the given (world serif) face
    assert styles["body"].fontName == faces.normal
    # headings use the shared display face (Quicksand), not a flat title bar
    assert styles["h1"].fontName == fonts.sheet_faces().display
    assert styles["h1"].backColor is None
    assert set(styles) >= {"h1", "h2", "h3", "body", "bullet"}
