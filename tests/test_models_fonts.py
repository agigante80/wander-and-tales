import pytest
from pydantic import ValidationError

from build.models import World


def _world(fonts=None):
    data = {"id": "w", "name": {"en-GB": "W", "es-ES": "W"}}
    if fonts is not None:
        data["fonts"] = fonts
    return data


def test_world_without_fonts_is_valid_and_none():
    world = World.model_validate(_world())
    assert world.fonts is None


def test_world_with_default_family_parses():
    world = World.model_validate(_world({"default": "dejavu-serif"}))
    assert world.fonts.default == "dejavu-serif"
    assert world.fonts.by_locale == {}


def test_world_with_per_locale_override_parses():
    world = World.model_validate(
        _world({"default": "dejavu-serif", "by_locale": {"es-ES": "dejavu-sans"}})
    )
    assert world.fonts.by_locale["es-ES"] == "dejavu-sans"


def test_unknown_default_family_fails():
    with pytest.raises(ValidationError) as err:
        World.model_validate(_world({"default": "papyrus"}))
    assert "papyrus" in str(err.value)


def test_unknown_override_family_fails():
    with pytest.raises(ValidationError):
        World.model_validate(
            _world({"default": "dejavu-sans", "by_locale": {"es-ES": "comic"}})
        )
