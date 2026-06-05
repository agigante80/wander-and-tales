---
name: publish-story
description: Use when a maintainer wants to publish a newly added or just-merged Wander & Tales story or world to the library: make sure every declared image exists (generating the missing ones with the maintainer's key), double-review the translations, build the kits, refresh the root README catalogue, confirm the PDFs render correctly, and commit. This is the maintainer-side counterpart to the create-story skill. Trigger on requests like "publish this story", "publish the kits", "a story was merged, build and publish it", "release the new world", or "rebuild and update the README".
---

# Publishing a Wander & Tales story or world

This skill is the **maintainer's publish step**, the counterpart to `create-story`.
`create-story` takes a contributor from an idea to a draft PR (content only, no built
PDFs). This skill takes a story or world that has just been authored or merged and
**publishes** it: every declared image exists, the translations have been reviewed,
the kits build correctly, the root README catalogue is refreshed, and the result is
committed to `main`.

It is maintainer-only because it is the only place that **uses the maintainer's OpenAI
key** and **commits built PDFs** to `main`. Contributors never run it.

Defer all voice, reading-level, peril-tone, and canon-name rules to the
`authoring-story-content` skill; this skill orchestrates the mechanical and review
steps around them.

## Step 0: scope and preconditions

- Identify what to publish: the world id and story id (or a whole new world) that was
  just added or merged. Note other worlds must be left untouched.
- Confirm you are the maintainer working on `main` with the project virtualenv
  (`.venv/`) and, if any art needs generating, an `OPENAI_API_KEY` in `.env`.
- Warn the maintainer that this step may spend OpenAI credits (image generation) and
  will commit built PDFs to `main`.

## Step 1: validate and lint

```bash
.venv/bin/python -m build validate --root .
.venv/bin/python -m build lint --root .
```

`validate` must pass. `lint` must report no `[error]` lines. `[warning]` lines for
images with no generated file are expected at this point; they clear in Step 2.

## Step 2: make sure every declared image exists

Each declared image (`id`) is expected at its `assets/<id>.png`. List what is declared
and generate the missing files.

- See the declared images and prompts: `python -m build prompts --root . --world <w>`
  (and the lint warnings name any image with no generated file).
- Generate the missing art with the maintainer's key. To include the world-level
  images (cover, portraits) as well as the story's, run with the world only, since the
  prompt filter excludes world-level images when a story is named:

  ```bash
  .venv/bin/python -m build generate-images --root . --world <w>
  ```

  Confirm with the maintainer before spending credits, and pass only the intended
  `--world` so no other world is touched. `generate-images` skips images that already
  have a file, so it only fills the gaps (use `--force` only to redo one deliberately).
- **Eyeball every new image.** Rasterize or open each PNG and confirm it is on-brand
  (the world's watercolour style), text-free (no letters, words, or numbers, so one
  image serves every language), gentle (nothing frightening), and faithful to canon
  (a `canon_ref` image must match that entry's description, for example a friendly,
  not scary, foe).
- Re-run `lint`: the image-file warnings for this world should now be gone.

If the maintainer chooses to leave a story prompts-only for now, that is fine; the kit
builds without the art and the warnings simply remain.

## Step 3: double-review the translations

This is the human-judgment pass the automated lint cannot do. For every content file
(`narration.simple.md`, `narration.rich.md`, `rules.md`, `puzzles.md`, the world
`idea-bank.md`, and any `guide.md` change), and for each `story.yaml`/`world.yaml`
localized field, compare **en-GB (the source of truth)** against **es-ES** (and any
other locale) and check:

- **Same beats, not literal.** The Spanish tells the same story with the same warmth
  and rhythm, translated for a Spanish child's ear, not word for word.
- **Peninsular Spanish.** Vosotros for the player pair, correct full accents, and
  inverted opening punctuation (the embedded Unicode font renders them).
- **No mixed register.** No Americanism in en-GB, no Latin American turn of phrase in
  es-ES (these are separate languages, like pt-PT versus pt-BR).
- **Canon names match.** Every named place, character, creature, item, or term uses
  the canonical name for that locale, and en and es agree on the same canon id.
- **Ethos intact.** Nobody loses; a failed roll reads as a detour, not a defeat; any
  claim about children stays associational, never causal.
- **No em or en dashes** anywhere, in any locale.

Read the narration aloud in your head; it should sound good in a grown-up's voice.
Fix issues in the non-English files (keeping en-GB canonical), or flag them for a
native-speaker review. Follow the `authoring-story-content` skill for the exact rules.

## Step 4: build and publish (from a clean tree)

The committed library must be built from a **clean** tree, or the versioned filenames
pick up a `+` (which marks a work-in-progress build that saw uncommitted inputs). So:

1. Commit the content and any generated art first (so the version inputs are clean):

   ```bash
   git add worlds/<w> guide/ lexicon/
   git commit -m "story: <Story Title> in <World> (or: world: <World>)"
   ```

2. Rebuild the whole library into `kits/`. This builds the language-first tree, prunes
   superseded versions, and rewrites the README catalogue table between its markers:

   ```bash
   .venv/bin/python -m build rebuild --root . --out-dir kits
   ```

The README's "Get the kit" table is generated, so do not hand-edit between the
`BEGIN KIT TABLE` and `END KIT TABLE` markers; `rebuild` owns that block.

## Step 5: confirm the PDFs are created correctly

- Run the test suite; it is green only if the structural invariants hold (every page
  A4, the Story Pack omits the answers and the glossary, the colophon and footer are
  present, and so on):

  ```bash
  .venv/bin/python -m pytest -q
  ```

- Rasterize a page of each new artifact and look at it:

  ```bash
  pdftoppm -png -r 110 "$(find kits -name 'story-pack-rich-*.pdf' | grep <w> | head -1)" /tmp/check
  ```

  Confirm: A4 white pages; the front page shows the world paragraph and the cover when
  art exists; the map page renders (a hand-drawn map where one exists, otherwise the
  generated trail map: START, the numbered stops, and a GOAL, with the stop names as
  labels in that locale and the trail reading start to finish); accents render; scene
  images embed; the last page is the colophon with the QR, the licence, and the
  version; and every page has the footer with `page x of y`. Check the World Book
  (cover, glossary with portraits, idea bank, stories list) and the Grown-up's Playbook
  (rules then answers) the same way.
- Confirm the README links resolve and no filename carries a `+`:

  ```bash
  for l in $(grep -oE 'kits/[^)]+\.pdf' README.md); do [ -f "$l" ] || echo "MISSING: $l"; done
  ls kits/**/*+*.pdf 2>/dev/null && echo "stray + version" || echo "clean versions"
  ```

## Step 6: commit and push

```bash
git add kits README.md
git commit -m "build: publish <World> / <Story> (art, kits, README)"
git push origin main
```

If art was generated in Step 2 but not yet committed, include `worlds/<w>` in this
commit (or commit it in Step 4). Push to `main` so the README download links resolve
on GitHub.

## Quick checklist before you call it published

- `validate` passes and `lint` has no errors.
- Every declared image for the world has a file, eyeballed and on-brand, or the
  maintainer deliberately left it prompts-only.
- The es-ES (and any other locale) text was reviewed against en-GB and reads naturally.
- The library was rebuilt from a clean tree (no `+` in any filename).
- `pytest` is green and a page of each new artifact was eyeballed.
- The README catalogue table and links are current and resolve.
- The maintainer's OpenAI key was used only for the intended world, never exposed in a
  commit.
