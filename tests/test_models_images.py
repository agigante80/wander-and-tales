import pytest
from pydantic import ValidationError

from build.models import Image, Story, World


def _image(**over):
    data = {
        "id": "cover",
        "role": "cover",
        "orientation": "portrait",
        "prompt": "A sleeping garden on a floating island.",
        "alt": {"en-GB": "A sleeping garden.", "es-ES": "Un jardin dormido."},
    }
    data.update(over)
    return data


def _story(images=None):
    data = {
        "world": "floating-isles",
        "id": "sleeping-garden",
        "title": {"en-GB": "The Sleeping Garden", "es-ES": "El Jardin Dormido"},
        "age": {"recommended": "young"},
        "skills": ["logic"],
        "peril": "gentle",
        "adult_gm": True,
        "dice": {"minimum": "1d6"},
        "players": {"min": 2, "max": 2},
        "play_time_minutes": 30,
    }
    if images is not None:
        data["images"] = images
    return data


def test_valid_image_parses():
    img = Image.model_validate(_image(canon_ref="mist-cat"))
    assert img.role == "cover"
    assert img.canon_ref == "mist-cat"


def test_image_defaults_canon_ref_to_none():
    assert Image.model_validate(_image()).canon_ref is None


def test_unknown_role_fails():
    with pytest.raises(ValidationError):
        Image.model_validate(_image(role="banner"))


def test_unknown_orientation_fails():
    with pytest.raises(ValidationError):
        Image.model_validate(_image(orientation="tall"))


def test_missing_alt_locale_fails():
    with pytest.raises(ValidationError) as err:
        Image.model_validate(_image(alt={"en-GB": "only english"}))
    assert "es-ES" in str(err.value)


def test_world_without_images_defaults_empty_and_no_style():
    world = World.model_validate({"id": "w", "name": {"en-GB": "W", "es-ES": "W"}})
    assert world.images == []
    assert world.visual_style is None


def test_world_collects_visual_style_and_images():
    world = World.model_validate(
        {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
         "visual_style": "Soft storybook art.", "images": [_image()]}
    )
    assert world.visual_style == "Soft storybook art."
    assert world.images[0].id == "cover"


def test_story_collects_images():
    story = Story.model_validate(_story(images=[_image()]))
    assert story.images[0].id == "cover"


def test_duplicate_image_ids_in_a_world_fail():
    with pytest.raises(ValidationError) as err:
        World.model_validate(
            {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
             "images": [_image(id="dup"), _image(id="dup")]}
        )
    assert "dup" in str(err.value)


def test_duplicate_image_ids_in_a_story_fail():
    with pytest.raises(ValidationError):
        Story.model_validate(_story(images=[_image(id="dup"), _image(id="dup")]))
