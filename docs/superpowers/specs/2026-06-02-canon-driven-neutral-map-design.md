# Wits & Wonder: canon-driven neutral map

**Status:** approved design, ready to plan.

**Context:** The Sleeping Garden's adventure map is currently a hand-drawn SVG with
Spanish text baked in (`map.es-ES.svg`). Because the labels are baked in, the map
serves only es-ES; en-GB kits ship without a map. This design makes the board a
single locale-neutral template: the art and number badges stay in the SVG, and the
text labels (title, stop names, legend, start and goal markers) are filled in at
render time from the story title, the canon place names in the kit's locale, and a
few localized UI strings. One `map.svg` then serves every language, and the en-GB
gap closes.

This mirrors the lesson the maps work taught us: art that bakes in text cannot be
shared across languages. Here the art stays text-free and the text is composed per
locale, the same split as the kit pages (locale-neutral layout, localized strings).

## Goals

- One neutral map template per story (or world) that renders correctly in every
  locale, with no per-locale art file.
- Labels driven by canon (place names) and the story title, so the map can never
  disagree with the world bible.
- A generic mechanism: any future story or world map works the same way by
  following the `data-label` key convention.
- Close the en-GB Sleeping Garden map gap.

## Non-goals (deferred)

- Redrawing or improving the map art itself. We reuse the existing art and only
  change how text gets onto it.
- Auto-placing labels by reading canon positions. Label positions stay authored in
  the SVG, where the artist tuned them.
- Removing per-locale `map.<locale>.svg` support. It stays as a fallback for art
  that must be hand-localized (the resolver order is unchanged); the Sleeping
  Garden simply stops needing it.

## The template SVG

`worlds/floating-isles/stories/sleeping-garden/assets/map.svg` replaces
`map.es-ES.svg`. It keeps every locale-neutral element of the current art: the sky
gradient and dashed border, the sun, clouds, golden path, trees, scattered
flowers, the white stop circles, the number badges `1` to `4`, the heart icon, and
the banner and legend box shapes. Each Spanish `<text>` becomes an empty
placeholder carrying a `data-label` key (and, for narrow stop labels, a
`data-wrap` count), positioned and styled exactly where the original text was:

| data-label | resolves to | wraps |
|---|---|---|
| `title` | `story.title[locale]` | no |
| `subtitle` | UI string `map_subtitle` | no |
| `stop:start` | UI string `map_start` | no |
| `hint:start` | UI string `map_hint_start` | no |
| `stop:vine-gate` | `canon["vine-gate"].names[locale]` | 2 |
| `stop:flower-bed` | `canon["flower-bed"].names[locale]` | 2 |
| `stop:talking-fountain` | `canon["talking-fountain"].names[locale]` | 2 |
| `stop:garden-heart` | `canon["garden-heart"].names[locale]` | 2 |
| `goal` | UI string `map_goal` | no |
| `legend:title` | UI string `map_legend_title` | no |
| `legend:a1`, `legend:a2`, `legend:b1`, `legend:b2`, `legend:foot` | UI strings `map_legend_a1` ... | no |

The number badges (`1` to `4`) stay as plain text in the art: they are
locale-neutral. The root `font-family` is set to `DejaVu Sans` so cairosvg renders
accents through fontconfig (DejaVu is vendored and system-available).

## Rendering (`build/render/map.py`)

`map.py` stays pure-SVG and gains two functions:

- `template_keys(svg_path: Path) -> list[str]`: parse the SVG and return every
  `data-label` value, in document order.
- `render_map_template(svg_path: Path, out_path: Path, labels: dict[str, str]) -> Path`:
  parse the SVG with `xml.etree.ElementTree` (register the SVG namespace as the
  default so output has no `ns0:` prefixes). For each `<text>` whose `data-label` is
  in `labels`, set its text to `labels[key]`; if the element has `data-wrap="N"`,
  clear its text and add up to N centered `<tspan>` children (a balanced word wrap),
  the first at the element's `y` and each next offset by a line height. Strip the
  `data-label` and `data-wrap` attributes from the output (they are not valid SVG
  presentation attributes, though cairosvg ignores them). Serialize and call the
  existing cairosvg render to a one-page PDF. Returns `out_path`.

A plain SVG with no `data-label` nodes passes through unchanged, so
`render_map_template` is backward compatible with any hand-localized
`map.<locale>.svg`.

Wrapping helper: `_wrap(text, max_lines) -> list[str]` splits on spaces into at most
`max_lines` lines, balancing word counts so a two-word name like "Vine Gate" splits
one word per line and a one-word name stays on one line. It never drops words; if a
single line would exceed the count it still emits at most `max_lines` lines with the
remaining words packed onto the last line.

## Localized strings (`build/render/strings.py`)

Add the map UI strings to the existing `UI` table for both `en-GB` and `es-ES`:
`map_subtitle`, `map_start`, `map_hint_start`, `map_goal`, `map_legend_title`,
`map_legend_a1`, `map_legend_a2`, `map_legend_b1`, `map_legend_b2`,
`map_legend_foot`. The existing `tests/test_render_strings.py` already asserts that
every required locale carries every key, so this stays balanced.

## Kit integration (`build/render/kit.py`)

The kit already resolves the map via `map.find_map(world_dir, story_dir, locale)`.
With only `map.svg` present (the neutral template), `find_map` returns it for every
locale, including en-GB. The kit then:

1. Reads the template keys: `keys = map.template_keys(map_svg)`.
2. Builds `labels` by resolving each key with a small helper:
   - `title` to `story.title[locale]`.
   - `stop:<id>` to `canon_by_id[<id>].names[locale]` when `<id>` is a canon id,
     otherwise to the UI string `strings.ui(locale, "map_" + <id>)` (this covers
     `stop:start`).
   - any other key to `strings.ui(locale, "map_" + key.replace(":", "_").replace("-", "_"))`
     (so `hint:start` to `map_hint_start`, `legend:a1` to `map_legend_a1`,
     `goal` to `map_goal`, `subtitle` to `map_subtitle`).
3. Calls `map.render_map_template(map_svg, tmp/"00_map.pdf", labels)` instead of the
   old `render_svg_to_pdf`.

This keeps `map.py` ignorant of canon and strings (the kit owns content), and the
resolution rule is generic: a new map template works as long as its keys are
`title`, `stop:<canon-id>`, or names that match a `map_*` UI string.

## Cleanup and docs

- Delete `worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg`; add
  `assets/map.svg` (the template).
- Update the maps note in the main spec
  (`2026-06-01-floating-isles-story-kit-library-design.md`) and in `CLAUDE.md`: the
  neutral template is now the documented default; `map.<locale>.svg` remains a
  supported fallback for hand-localized art; the Sleeping Garden map now serves
  every locale and en-GB kits include it.

## Testing

- `tests/test_render_map.py` (extend): `template_keys` returns the expected keys for
  a small inline template; `render_map_template` fills a template and the resulting
  intermediate SVG (exposed via a helper or checked by re-parsing) contains the
  substituted locale text; a long `data-wrap="2"` label yields two `<tspan>`s; a
  plain SVG (no `data-label`) still renders to a `%PDF`; `_wrap` splits a two-word
  name one word per line and keeps a one-word name on one line.
- `tests/test_render_kit.py` (extend): with the real neutral `map.svg` in a fixture
  world (or the sample repo plus a tiny template), a kit build for both `en-GB` and
  `es-ES` includes a map page (en-GB no longer omitted), and the en-GB and es-ES
  filled maps differ (different locale labels). Assert via the fill step, since text
  inside a rendered PDF is hard to read back.
- The existing `test_render_strings.py` balance test covers the new strings.
- After implementation, build the real Sleeping Garden kits for en-GB and es-ES and
  rasterize the map page to confirm the labels render in the right language with
  accents and the layout holds.

## File touch list

- New: `worlds/floating-isles/stories/sleeping-garden/assets/map.svg` (neutral
  template, authored from the existing art).
- Deleted: `worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg`.
- Modified: `build/render/map.py` (`template_keys`, `render_map_template`, `_wrap`),
  `build/render/strings.py` (map UI strings), `build/render/kit.py` (build labels,
  route through `render_map_template`).
- Tests: `tests/test_render_map.py`, `tests/test_render_kit.py`.
- Docs: the main spec's maps note and `CLAUDE.md`.

## Future work (named, not built here)

- Apply the same neutral-template treatment to a future world-level map.
- Optionally draw map labels in the world's typeface (would move text rendering to
  a reportlab overlay; deferred since DejaVu on the SVG reads well and is simpler).
