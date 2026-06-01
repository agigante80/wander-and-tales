"""Difficulty bands and their thresholds per dice set (spec section 7).

Rules and narration never name a die; they use bands. A single in-kit table
maps bands onto whatever dice a family owns. Every story is playable with 1d6.
"""

BANDS = ("Easy", "Normal", "Hard")
DICE_FLOOR = "1d6"

_BAND_THRESHOLDS = {
    "1d6": {"Easy": 3, "Normal": 4, "Hard": 5},
    "d20-set": {"Easy": 6, "Normal": 10, "Hard": 14},
}


def thresholds_for(dice_set: str) -> dict[str, int]:
    """Per-band minimum roll for a dice set. Raises KeyError if unknown."""
    return dict(_BAND_THRESHOLDS[dice_set])


def known_dice_sets() -> tuple[str, ...]:
    return tuple(_BAND_THRESHOLDS)
