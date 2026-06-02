# Wits & Wonder: images and art prompts

**Status:** approved design, ready to plan.

**Context:** Wits & Wonder kits are currently text plus a hand-authored SVG map.
We want worlds and stories to be able to carry illustrations (covers, scene art,
creature and character portraits, decorative motifs), and we want each image to
ship with a ready-to-paste prompt for an external AI image generator. The prompts
must be authored as a normal part of writing a world or story, so future content
arrives illustration ready. Generating and embedding the actual image files is a
later step; this design delivers the schema, the prompts, an export command, and
the authoring rules.

This design reuses a lesson from the maps work: art that bakes in text cannot be
shared across languages. So generated art here is locale neutral and free of any
text; only the alternative text is localized.

## Goals

- Declare any number of images per world and per story, each with a role and a
  generation prompt, in the existing YAML, validated by the model.
- Keep prompts DRY and visually consistent: the world owns one art direction
  preamble; each image owns only its subject.
- Export a copy and paste ready prompt list with a CLI.
- Make prompt authoring part of the content authoring workflow (skill and spec),
  so every future world and story ships with its prompts.

## Non-goals (deferred, by agreement)

- Generating the image files (done by an external tool, by hand for now).
- Embedding images into the kit PDFs. The schema is shaped so this drops in later.
- A lint that every declared image has a matching file on disk. Add when files
  start arriving.

## Vocabulary (single source of truth)

A new pure module `build/visuals.py`, sitting beside `fontspec.py`, `tags.py`,
`dice.py`, `locales.py`:

```python
IMAGE_ROLES = ("cover", "scene", "portrait", "motif")
ORIENTATIONS = ("portrait", "landscape", "square")
```

- `cover`: one hero image for a world or a story.
- `scene`: an illustration of a moment or stop in a story.
- `portrait`: a creature or character, usually tied to a canon entry.
- `motif`: a small decorative element (border flourish, icon).

Orientation drives the aspect ratio hint in the exported prompt and, later, the
layout slot the renderer uses.

## Schema (model)

A new strict model `Image` (extra forbidden, like every other model):

| field | type | required | notes |
|---|---|---|---|
| `id` | str | yes | stable, unique within its owning world or story |
| `role` | str | yes | in `visuals.IMAGE_ROLES` |
| `orientation` | str | yes | in `visuals.ORIENTATIONS` |
| `prompt` | str | yes | the subject to draw; locale neutral; describes text free art |
| `alt` | dict[str,str] | yes | localized alt text; carries all `REQUIRED_LOCALES` |
| `canon_ref` | str or null | no | optional canon id this image depicts |

Added fields on existing models:

- `World.visual_style: str | None` is the world's art direction preamble (medium,
  mood, palette hexes, content safety notes), written once, shared by every image
  in the world.
- `World.images: list[Image] = []`
- `Story.images: list[Image] = []`

Validation:

- `role` in `IMAGE_ROLES`; `orientation` in `ORIENTATIONS` (field validators).
- `alt` carries every `REQUIRED_LOCALES` entry (reuse `_require_locales`).
- `id` unique within a single world's `images`, and within a single story's
  `images` (model validator on the list owner).
- `canon_ref`, when present, is a non-empty string. Cross checking that it names a
  real canon entry is a lint concern, added in the lint task (warning level), so
  the model stays decoupled from canon loading.

`visual_style` is plain text (one short paragraph). It is not localized: it is art
direction, not kid-facing prose.

## Prompt composition and export

The stored `prompt` is only the subject. The full, paste ready prompt is composed
at export time, so editing `visual_style` once updates every prompt in the world.

Composition for one image, in order:

1. the world's `visual_style` (or a neutral default if the world has none),
2. the image `prompt` (subject),
3. a technical line derived from `role` and `orientation`: an aspect ratio hint
   (portrait about 3:4, landscape about 4:3, square 1:1), then the fixed rules
   "No text, letters, words, or numbers anywhere in the image. Soft children's
   storybook illustration. Gentle and friendly, nothing scary or violent.",
4. if `canon_ref` is set and resolvable, a short "Depicts: <canon name>, <canon
   description>" line in the canonical locale, for consistency.

A new module `build/prompts.py` exposes:

- `compose_prompt(world, image, canon_by_id) -> str`
- `iter_image_prompts(root) -> list[PromptEntry]` where `PromptEntry` carries the
  world id, story id (or None for world images), the `Image`, and the composed
  text.
- `build_prompts_markdown(entries) -> str` and `write_prompts(entries, path)`.

A new CLI subcommand:

```
python -m build prompts --root .            # print all composed prompts
python -m build prompts --root . --out prompts.md
python -m build prompts --root . --world floating-isles --story sleeping-garden
```

Output is grouped by world then story; each image shows a heading
(`<owner> / <id> [role, orientation]`), the composed prompt in a fenced block for
easy copying, and the alt text per locale.

## Authoring workflow (the "future generation" requirement)

Two documentation changes make prompts a standard part of authoring:

- The main design spec gains an "Images and art prompts" section pointing here and
  stating the locale neutral, text free art rule and the localized alt rule.
- The `authoring-story-content` skill gains an images section: when authoring a
  world, write `visual_style` and any world level images; when authoring a story,
  write its `images` with subject only prompts that are gentle, palette consistent
  with the world, canon consistent, and free of any in image text. Alt text is
  written in en-GB first, then es-ES, like all other prose.

## Worked content delivered now

Real, authored values added to the existing content:

- `worlds/floating-isles/world.yaml`: a `visual_style` paragraph, a world `cover`,
  and two `portrait` images (`mist-cat`, `lonely-sprite`) with `canon_ref` set.
- `worlds/floating-isles/stories/sleeping-garden/story.yaml`: a story `cover` and
  four `scene` images (the vine gate, the flower bed, the talking fountain, the
  heart of the garden), each with en-GB and es-ES alt text.

These double as the fixtures that prove the export end to end and as the first
real prompts to paste into a generator.

## Testing

- `tests/test_visuals.py`: the role and orientation vocabularies.
- `tests/test_models_images.py`: a valid image parses; unknown role and
  orientation fail; missing alt locale fails; duplicate image ids within a world
  or story fail; `visual_style` and `images` default cleanly when absent.
- `tests/test_prompts.py`: `compose_prompt` includes the style preamble, the
  subject, the no text rule, and an aspect hint matching orientation; `canon_ref`
  pulls in the canon description; the markdown export contains a fenced prompt and
  the alt text.
- `tests/test_cli_prompts.py`: the `prompts` subcommand prints and writes, and the
  `--world`/`--story` filters narrow the output.
- `python -m build validate --root .` stays green with the new content.

## File touch list

- New: `build/visuals.py`, `build/prompts.py`, and their tests.
- Modified: `build/models.py` (Image, `World.visual_style`, `World.images`,
  `Story.images`), `build/__main__.py` (the `prompts` subcommand),
  `build/lint.py` (optional `canon_ref` existence warning).
- Content: `worlds/floating-isles/world.yaml`,
  `worlds/floating-isles/stories/sleeping-garden/story.yaml`.
- Docs: the main spec's new section, and the `authoring-story-content` skill.

## Future work (named, not built here)

- Generate the image files (external tool) and drop them in story or world
  `assets/`.
- Embed images into kit PDFs by role and orientation, optional and skipped when a
  file is absent, exactly like the map page.
- A lint that every declared image has a file once generation begins.
