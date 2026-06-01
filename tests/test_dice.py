from build import dice


def test_bands_and_floor():
    assert dice.BANDS == ("Easy", "Normal", "Hard")
    assert dice.DICE_FLOOR == "1d6"


def test_thresholds_for_known_sets_match_spec_table():
    assert dice.thresholds_for("1d6") == {"Easy": 3, "Normal": 4, "Hard": 5}
    assert dice.thresholds_for("d20-set") == {"Easy": 6, "Normal": 10, "Hard": 14}


def test_every_band_has_a_threshold_for_the_floor():
    floor = dice.thresholds_for(dice.DICE_FLOOR)
    assert set(floor) == set(dice.BANDS)


def test_thresholds_for_unknown_set_raises():
    import pytest

    with pytest.raises(KeyError):
        dice.thresholds_for("d4-only")
