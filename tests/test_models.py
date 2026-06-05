import pytest
from pydantic import ValidationError

from build.models import Story, CanonEntry, World


def _valid_world_data():
    return {
        "id": "greek-myth",
        "name": {"en-GB": "Greece", "es-ES": "Grecia", "it-IT": "Grecia"},
    }


def test_world_hero_powers_defaults_to_magic():
    assert World.model_validate(_valid_world_data()).hero_powers == "magic"


def test_world_hero_powers_accepts_strength():
    data = _valid_world_data() | {"hero_powers": "strength"}
    assert World.model_validate(data).hero_powers == "strength"


def test_world_unknown_hero_powers_fails():
    with pytest.raises(ValidationError):
        World.model_validate(_valid_world_data() | {"hero_powers": "spells"})


def _valid_story_data():
    return {
        "world": "floating-isles",
        "id": "sleeping-garden",
        "title": {"en-GB": "The Sleeping Garden", "es-ES": "El Jardin Dormido",
                  "it-IT": "Il Giardino Addormentato"},
        "age": {"recommended": "young", "also_works_for": ["early", "older"]},
        "skills": ["vocabulary", "logic", "social-emotional"],
        "peril": "gentle",
        "adult_gm": True,
        "dice": {"minimum": "1d6", "recommended": "d20-set"},
        "players": {"min": 2, "max": 2},
        "play_time_minutes": 30,
    }


def test_valid_story_parses():
    story = Story.model_validate(_valid_story_data())
    assert story.id == "sleeping-garden"
    assert story.title["en-GB"] == "The Sleeping Garden"


def test_story_missing_synced_locale_in_title_fails():
    data = _valid_story_data()
    data["title"] = {"en-GB": "The Sleeping Garden"}
    with pytest.raises(ValidationError) as err:
        Story.model_validate(data)
    assert "es-ES" in str(err.value)


def test_story_unknown_peril_fails():
    data = _valid_story_data()
    data["peril"] = "terrifying"
    with pytest.raises(ValidationError):
        Story.model_validate(data)


def test_story_dice_floor_must_be_1d6():
    data = _valid_story_data()
    data["dice"]["minimum"] = "d20"
    with pytest.raises(ValidationError) as err:
        Story.model_validate(data)
    assert "1d6" in str(err.value)


def test_canon_entry_requires_both_locale_names():
    with pytest.raises(ValidationError) as err:
        CanonEntry.model_validate(
            {"id": "mist-cat", "names": {"en-GB": "Mist Cat"}, "kind": "creature"}
        )
    assert "es-ES" in str(err.value)
