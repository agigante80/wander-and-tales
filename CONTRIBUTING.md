# Contributing to Wander & Tales

Thank you for wanting to add a story. This library grows through contributions, and
adding a world or a story is a writing task, not a coding task.

## The easiest way: two skills in Claude Code

Most people start by making their own kit, then decide whether to share it.

- **`create-story`** walks you through writing your own adventure (choosing or
  creating a world, the idea, the audience, the challenges, in every language the
  project ships, currently British English, Spanish from Spain, Italian, and European
  Portuguese) and builds your printable PDFs into `dist/`. That is all you need
  to print and play at home; sharing is optional.
- **`contribute-story`** is the optional next step: when your story is done, it opens a
  draft pull request so a maintainer can review it for the public library.

Both follow the project's voice and ethos rules for you (see `CLAUDE.md` and the
`authoring-story-content` guidance). You can also author the files by hand if you
prefer; the skills just remove the friction.

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
- The story keeps the promise every kit makes: cooperative play, nobody loses, no
  wrong answers, and you win by being kind and full of ideas.

## Maintainer: publishing a merged story

This part is for the maintainer, after a story or world is merged. Contributors do not
do this; built PDFs are never in a contributor PR.

Publishing turns merged content into the committed library: every declared image is
generated (with the maintainer's key), the translations are double-reviewed, the kits
are built, the root README catalogue is regenerated, and the PDFs are checked. The
**`publish-story` skill** in Claude Code runs this end to end (ask to "publish this
story"). By hand, the short version is: ensure the art exists
(`python -m build generate-images --root . --world <w>`), commit the content and art,
then build and refresh the README from a clean tree
(`python -m build rebuild --root .`), confirm `python -m pytest` is green and no
filename carries a `+`, and commit `kits/` and `README.md`.

## Licensing

By opening a pull request you agree that your contribution is offered under the
project licences: content under CC BY-SA 4.0 (`LICENSE-CONTENT`) and any code under
MIT (`LICENSE`). Please contribute only material you have the right to give.
