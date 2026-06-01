from build import tags


def test_vocabularies_match_spec():
    assert tags.AGE_TIERS == ("early", "young", "older")
    assert tags.PERILS == ("gentle", "mild", "heroic")
    assert tags.READING_LEVELS == ("simple", "rich")
    assert set(tags.SKILLS) == {
        "vocabulary", "logic", "maths", "memory",
        "spatial", "observation", "social-emotional",
    }


def test_reading_level_covers_expected_tiers():
    assert tags.tiers_for_reading_level("simple") == ("early", "young")
    assert tags.tiers_for_reading_level("rich") == ("older",)


def test_reading_level_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        tags.tiers_for_reading_level("medium")
