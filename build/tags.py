"""Tag vocabularies and the reading-level to age-tier mapping (spec sections 6 and 8)."""

AGE_TIERS = ("early", "young", "older")
SKILLS = (
    "vocabulary",
    "logic",
    "maths",
    "memory",
    "spatial",
    "observation",
    "social-emotional",
)
PERILS = ("gentle", "mild", "heroic")
READING_LEVELS = ("simple", "rich")

_READING_LEVEL_TIERS = {
    "simple": ("early", "young"),
    "rich": ("older",),
}


def tiers_for_reading_level(level: str) -> tuple[str, ...]:
    """Age tiers a reading level serves. Raises ValueError on an unknown level."""
    try:
        return _READING_LEVEL_TIERS[level]
    except KeyError:
        raise ValueError(f"unknown reading level: {level!r}") from None
