"""Typed content models mirroring the spec schema (sections 6 and 9)."""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from build import dice, fontspec, locales, tags, visuals

_CANON_KINDS = ("place", "character", "creature", "item", "term", "quality")


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


class Image(_Strict):
    """A declared illustration plus its generation prompt.

    The prompt is the locale-neutral subject; the world's visual_style preamble
    and a technical line are added at export time (see build/prompts.py). Art is
    text-free and language-neutral; only alt is localized.
    """

    id: str
    role: str
    orientation: str
    prompt: str
    alt: dict[str, str]
    canon_ref: str | None = None

    @field_validator("role")
    @classmethod
    def _known_role(cls, value: str) -> str:
        if value not in visuals.IMAGE_ROLES:
            raise ValueError(f"image role {value!r} not in {visuals.IMAGE_ROLES}")
        return value

    @field_validator("orientation")
    @classmethod
    def _known_orientation(cls, value: str) -> str:
        if value not in visuals.ORIENTATIONS:
            raise ValueError(
                f"image orientation {value!r} not in {visuals.ORIENTATIONS}"
            )
        return value

    @field_validator("alt")
    @classmethod
    def _alt_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "alt")
        return value

    @field_validator("canon_ref")
    @classmethod
    def _canon_ref_nonempty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("canon_ref, when given, must be a non-empty id")
        return value


def _unique_image_ids(images: list[Image]) -> list[Image]:
    seen: set[str] = set()
    for image in images:
        if image.id in seen:
            raise ValueError(f"duplicate image id {image.id!r}")
        seen.add(image.id)
    return images


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
    images: list[Image] = []

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

    @field_validator("images")
    @classmethod
    def _unique_images(cls, value: list[Image]) -> list[Image]:
        return _unique_image_ids(value)


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


class ExampleHero(_Strict):
    """A pre-filled example hero for a world's sample adventure sheets.

    A ready-to-use or inspiration hero: a name, what they are a hero of, three
    chosen magics or qualities (canon term ids), some filled energy stars, a few
    carried items, and a text-free hero portrait drawn in the sheet's draw box.
    """

    id: str
    tier: str  # young or older (the two example sheet tiers)
    name: str
    hero_of: dict[str, str]
    magics: list[str]  # exactly 3 canon term ids (magics or qualities)
    energy: int = 0
    carry: list[dict[str, str]] = []
    image: Image

    @field_validator("tier")
    @classmethod
    def _known_tier(cls, value: str) -> str:
        if value not in ("young", "older"):
            raise ValueError(f"example hero tier {value!r} must be 'young' or 'older'")
        return value

    @field_validator("hero_of")
    @classmethod
    def _hero_of_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "hero_of")
        return value

    @field_validator("magics")
    @classmethod
    def _three_magics(cls, value: list[str]) -> list[str]:
        if len(value) != 3:
            raise ValueError("a hero needs exactly 3 magics or qualities")
        return value

    @field_validator("energy")
    @classmethod
    def _energy_range(cls, value: int) -> int:
        if not 0 <= value <= 5:
            raise ValueError("energy must be 0 to 5")
        return value

    @field_validator("carry")
    @classmethod
    def _carry_locales(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(value) > 6:
            raise ValueError("at most 6 carry items")
        for item in value:
            _require_locales(item, "carry item")
        return value


class LexiconTerm(_Strict):
    id: str
    names: dict[str, str]

    @field_validator("names")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "names")
        return value


class WorldFonts(_Strict):
    """A world's typeface: a default family plus optional per-locale overrides.

    Resolution at render time is by_locale[locale], then default. Families are
    validated against the fontspec registry so a typo fails at load, not at draw.
    """

    default: str
    by_locale: dict[str, str] = {}

    @field_validator("default")
    @classmethod
    def _known_default(cls, value: str) -> str:
        if value not in fontspec.KNOWN_FAMILIES:
            raise ValueError(
                f"font family {value!r} not in {fontspec.KNOWN_FAMILIES}"
            )
        return value

    @field_validator("by_locale")
    @classmethod
    def _known_overrides(cls, value: dict[str, str]) -> dict[str, str]:
        bad = {
            loc: fam
            for loc, fam in value.items()
            if fam not in fontspec.KNOWN_FAMILIES
        }
        if bad:
            raise ValueError(f"unknown font families in by_locale: {bad}")
        return value


class World(_Strict):
    id: str
    name: dict[str, str]
    tone: str | None = None
    palette: list[str] = []
    lore_summary: dict[str, str] | None = None
    fonts: WorldFonts | None = None
    visual_style: str | None = None
    hero_powers: str = "magic"
    images: list[Image] = []

    @field_validator("name")
    @classmethod
    def _name_locales(cls, value: dict[str, str]) -> dict[str, str]:
        _require_locales(value, "name")
        return value

    @field_validator("hero_powers")
    @classmethod
    def _known_hero_powers(cls, value: str) -> str:
        if value not in tags.HERO_POWERS:
            raise ValueError(
                f"hero_powers {value!r} not in {tags.HERO_POWERS}"
            )
        return value

    @field_validator("images")
    @classmethod
    def _unique_images(cls, value: list[Image]) -> list[Image]:
        return _unique_image_ids(value)
