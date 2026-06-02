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
- Generate the image files directly from those prompts with an optional command
  that calls the OpenAI Images API, so a key holder can fill in the art in one
  step.
- Make prompt authoring part of the content authoring workflow (skill and spec),
  so every future world and story ships with its prompts.

## Non-goals (deferred, by agreement)

- Embedding images into the kit PDFs. The schema and the generated files are
  shaped so this drops in later, exactly like the optional map page.
- A lint that every declared image has a matching file on disk. Add when files
  start arriving.
- Support for image providers other than OpenAI. The generator is one small module
  behind a narrow interface, so another backend can be added later without
  touching the schema or the prompts.

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

## Image generation (optional command)

A key holder can generate the actual art from the composed prompts in one step,
without leaving the repo. This is optional: it is the same composed prompts as the
`prompts` export, just sent to the OpenAI Images API instead of printed.

A new module `build/generate.py` wraps generation behind a narrow interface so a
different backend could replace it later:

- `image_size_for(orientation) -> str` maps the orientation vocabulary to an
  OpenAI size: `portrait` to `1024x1536`, `landscape` to `1536x1024`, `square` to
  `1024x1024`.
- `generate_image(prompt, orientation, out_path, *, client=None) -> Path` calls
  the OpenAI Images API (`gpt-image-1`), decodes the returned base64 PNG, and
  writes it to `out_path`. The `client` argument is injectable so tests pass a fake
  and never hit the network.
- `target_path(root, entry) -> Path` returns the asset path for a `PromptEntry`:
  `worlds/<world>/assets/<id>.png` for a world image, or
  `worlds/<world>/stories/<story>/assets/<id>.png` for a story image. This is the
  same `assets/` location the map uses and the future embedding step will read.
- `generate_all(root, *, world=None, story=None, force=False, client) -> list[Path]`
  is the orchestrator the CLI calls: it resolves prompts with
  `iter_image_prompts`, applies the `--world`/`--story` filters, skips existing
  targets unless `force`, and calls `generate_image` for the rest, returning the
  paths written. The `client` is passed in, so tests drive it with a fake and the
  CLI constructs the real OpenAI client only after confirming the key exists.

A new CLI subcommand:

```
python -m build generate-images --root .                      # all missing images
python -m build generate-images --root . --world floating-isles --story sleeping-garden
python -m build generate-images --root . --force              # regenerate existing
```

Behaviour:

- Resolves prompts with the same `iter_image_prompts` the `prompts` command uses,
  so what you generate is exactly what you previewed.
- Skips any image whose target file already exists, unless `--force` is given.
- Requires the `OPENAI_API_KEY` environment variable; if it is missing the command
  prints a clear message and exits non-zero before calling the API.
- Reports each file written and a final count.

`openai` is added as a new optional dependency group `images` in `pyproject.toml`,
so the core install and the `render` install stay lean. The command imports
`openai` lazily inside its branch, so `validate`, `lint`, `catalog`, `prompts`,
and `render` all keep working without it installed.

Generated PNGs land in `assets/<id>.png`, the same place the map SVG lives, and
are committed like any other build asset. Reason: this is an open print and play
library, so the repo must build complete kits without anyone re-spending API
money; the chosen art is a build input, exactly like `map.svg`. The command writes
one file per image id (the chosen art), and `--force` overwrites it in place, so
the tree never fills with throwaway candidates.

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
- `tests/test_generate.py`: `image_size_for` maps each orientation correctly;
  `target_path` returns the right `assets/` location for world and story images;
  `generate_image` with an injected fake client writes the decoded PNG bytes and
  never touches the network.
- `tests/test_cli_generate.py`: the `generate-images` subcommand, run with a fake
  client, writes the expected files, skips existing files without `--force`,
  overwrites with `--force`, and exits non-zero with a clear message when
  `OPENAI_API_KEY` is absent.
- `python -m build validate --root .` stays green with the new content.

## File touch list

- New: `build/visuals.py`, `build/prompts.py`, `build/generate.py`, and their
  tests.
- Modified: `build/models.py` (Image, `World.visual_style`, `World.images`,
  `Story.images`), `build/__main__.py` (the `prompts` and `generate-images`
  subcommands), `build/lint.py` (optional `canon_ref` existence warning),
  `pyproject.toml` (the `images` optional dependency group for `openai`).
- Content: `worlds/floating-isles/world.yaml`,
  `worlds/floating-isles/stories/sleeping-garden/story.yaml`.
- Docs: the main spec's new section, and the `authoring-story-content` skill.

## Future work (named, not built here)

- Embed images into kit PDFs by role and orientation, optional and skipped when a
  file is absent, exactly like the map page.
- A lint that every declared image has a file once generation begins.
- Additional image backends behind the same `generate.py` interface, if a provider
  other than OpenAI is ever wanted.
