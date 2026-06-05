from reportlab.pdfbase import pdfmetrics

from build import fontspec
from build.models import World
from build.render import fonts


def _world(fonts_block=None):
    data = {"id": "w", "name": {"en-GB": "W", "es-ES": "W", "it-IT": "W", "pt-PT": "W"}}
    if fonts_block is not None:
        data["fonts"] = fonts_block
    return World.model_validate(data)


def test_register_family_is_idempotent_and_registers_faces():
    fonts.register_family("dejavu-sans")
    faces = fonts.register_family("dejavu-sans")  # twice must not raise
    registered = set(pdfmetrics.getRegisteredFontNames())
    assert {faces.normal, faces.bold, faces.italic, faces.bold_italic} <= registered


def test_resolve_family_defaults_when_world_has_no_fonts():
    assert fonts.resolve_family(_world(), "en-GB") == fontspec.DEFAULT_FAMILY
    assert fonts.resolve_family(None, "en-GB") == fontspec.DEFAULT_FAMILY


def test_resolve_family_uses_world_default():
    world = _world({"default": "dejavu-serif"})
    assert fonts.resolve_family(world, "en-GB") == "dejavu-serif"
    assert fonts.resolve_family(world, "es-ES") == "dejavu-serif"


def test_per_locale_override_wins_within_a_world():
    world = _world({"default": "dejavu-sans", "by_locale": {"es-ES": "dejavu-serif"}})
    assert fonts.resolve_family(world, "en-GB") == "dejavu-sans"
    assert fonts.resolve_family(world, "es-ES") == "dejavu-serif"


def test_resolve_faces_registers_and_returns_the_resolved_family():
    world = _world({"default": "dejavu-serif"})
    faces = fonts.resolve_faces(world, "en-GB")
    assert faces.normal == "dejavu-serif"
    assert faces.bold in set(pdfmetrics.getRegisteredFontNames())
