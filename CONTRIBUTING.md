# Contributing to Wits & Wonder

Thank you for wanting to add a story. This library grows through contributions, and
adding a world or a story is a writing task, not a coding task.

## The easiest way: the create-story skill

In Claude Code, ask to "create a story" (or "add an adventure", "start a new
world"). The `create-story` skill walks you through everything: choosing or creating
a world, picking or writing an idea, setting the audience and challenges, writing the
content in British English and Spanish from Spain, validating it, previewing the kit,
and opening a draft pull request. It follows the project's voice and ethos rules for
you (see `CLAUDE.md` and the `authoring-story-content` guidance).

You can also author the files by hand if you prefer; the skill just removes the
friction.

## What a pull request should contain

- The content: `worlds/<world>/...` (the `world.yaml` and `canon/` for a new world,
  the `story.yaml` and `content/<locale>/*.md` for the story), any `guide/` change,
  and the regenerated `catalog.md`.
- Image **prompts** in `story.yaml` (and `world.yaml`). Pictures are optional.
- Optionally, pictures you made yourself: art you drew, art you generated with your
  **own** image-generation key, or art you have the right to give. Do not include
  someone else's images.

Please do **not** commit built PDFs or anything under `dist/`. Those are derived
artifacts that continuous integration and the maintainer rebuild.

## How review and merge work

- Every pull request is reviewed by a maintainer, who may request changes or merge.
- You do **not** need an OpenAI key. A prompts-only story is illustrated by the
  maintainer after it is accepted, using the maintainer's own key. That key is never
  exposed to a contributor or to a pull request build.
- Non-English text is treated as machine-drafted and may receive a native-speaker
  review before it is considered final. British English is the source of truth.

## Before you open the PR

- `python -m build validate --root .` passes.
- `python -m build lint --root .` reports no errors (image-file warnings are fine).
- The story keeps the promise every kit makes: cooperative play, nobody loses, and
  you win by being clever and kind.
