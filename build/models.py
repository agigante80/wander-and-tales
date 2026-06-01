"""Typed content models mirroring the spec schema (sections 6 and 9)."""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from build import dice, locales, tags

_CANON_KINDS = ("place", "character", "creature", "item", "term")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _require_locales(mapping: dict[str, str], field_name: str) -> None:
    missing = locales.missing_locales(mapping)
    if missing:
        raise ValueError(f"{field_name} is missing locale(s): {', '.join(missing)}")


class Age(_Strict):
    recommended: str
    also_works_for: list[str] = []

    @field_validator("recommended")
    @classmethod
    def _known_recommended(cls, value: str) -> str:
        if value not in tags.AGE_TIERS:
            raise ValueError(f"recommended age {value!r} not in {tags.AGE_TIERS}")
        return value

    @field_validator("also_works_for")
    @classmethod
    def _known_also(cls, value: list[str]) -> list[str]:
        bad = [tier for tier in value if tier not in tags.AGE_TIERS]
        if bad:
            raise ValueError(f"also_works_for has unknown tiers: {bad}")
        return value


class Dice(_Strict):
    minimum: str
    recommended: str | None = None

    @field_validator("minimum")
    @classmethod
    def _floor_is_d6(cls, value: str) -> str:
        if value != dice.DICE_FLOOR:
            raise ValueError(
                f"dice.minimum must be {dice.DICE_FLOOR!r} so every story is "
                f"playable with a single d6; got {value!r}"
            )
        return value


class Players(_Strict):
    min: int
    max: int

    @model_validator(mode="after")
    def _min_le_max(self) -> "Players":
        if self.min > self.max:
            raise ValueError("players.min cannot exceed players.max")
        return self


class Story(_Strict):
    world: str
    id: str
    title: dict[str, str]
    age: Age
    skills: list[str]
    peril: str
    adult_gm: bool
    dice: Dice
    players: Players
    play_time_minutes: int

    @field_validator("title")
    @classmethod
    def _title_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "title")
        return value

    @field_validator("skills")
    @classmethod
    def _known_skills(cls, value: list[str]) -> list[str]:
        bad = [s for s in value if s not in tags.SKILLS]
        if bad:
            raise ValueError(f"unknown skills: {bad}")
        return value

    @field_validator("peril")
    @classmethod
    def _known_peril(cls, value: str) -> str:
        if value not in tags.PERILS:
            raise ValueError(f"peril {value!r} not in {tags.PERILS}")
        return value


class CanonEntry(_Strict):
    id: str
    names: dict[str, str]
    kind: str
    disposition: str | None = None
    description: dict[str, str] | None = None
    first_seen: str | None = None

    @field_validator("kind")
    @classmethod
    def _known_kind(cls, value: str) -> str:
        if value not in _CANON_KINDS:
            raise ValueError(f"kind {value!r} not in {_CANON_KINDS}")
        return value

    @field_validator("names")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "names")
        return value


class LexiconTerm(_Strict):
    id: str
    names: dict[str, str]

    @field_validator("names")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "names")
        return value


class World(_Strict):
    id: str
    name: dict[str, str]
    tone: str | None = None
    palette: list[str] = []
    lore_summary: dict[str, str] | None = None

    @field_validator("name")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "name")
        return value
