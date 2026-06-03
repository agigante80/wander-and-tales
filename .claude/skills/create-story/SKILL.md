---
name: create-story
description: Use when a user wants to create their own Wits & Wonder story (or a new world) and build their own printable kit to play at home. Guides choosing or creating a world, choosing or writing an idea, setting the audience and challenges, authoring the content in British English, Spanish from Spain, and Italian with image prompts, optionally generating the pictures with the user's own OpenAI key (or leaving prompts to paste elsewhere), validating, and building the printable PDFs into dist/. Defers all voice, reading-level, peril-tone, and canon-name rules to the authoring-story-content skill. Sharing the story with the public library is optional and handled by the separate contribute-story skill. Trigger on requests like "create a story", "make my own adventure", "make a kit about X", "write a new story to print", or "start a new world".
---

# Creating your own Wits & Wonder kit

This skill is an **orchestrator** for making your own kit. It runs the interview and
the mechanical steps (scaffold, validate, build) and leaves all the writing rules to
the `authoring-story-content` skill. The goal is to take the author from an idea to a
valid, on-brand story and their own printable PDFs, ready to print and play at home.

Sharing the story with the public library is optional and separate: when the kit is
done, the `contribute-story` skill opens a draft pull request if the author wants one.
This skill never needs the maintainer's key; any images are generated with the author's
own key.

## Step 0: load the authoring rules

**Invoke the `authoring-story-content` skill first** and follow it for every piece
of prose and YAML. It holds the no-lose ethos, the no em or en dash rule, the
associational-claims rule, the en-GB and es-ES register, reading levels, peril
tone, and canon-name discipline. Do not restate those rules here; obey them.

## Step 1: choose a world

Offer three paths (see `references/interview.md` for the script and the new-world
seed list):

- **Use an existing world.** List the worlds under `worlds/` and let the author
  pick one. Their story will reuse that world's canon and look.
- **Start from a suggested new world.** Offer a few on-brand seeds and let the
  author pick and adjust one.
- **Create a custom world.** The author describes it; you scaffold `world.yaml`
  (name per locale, tone, a palette of seven hex colours, `fonts.default`,
  `lore_summary` per locale, `visual_style`) and an initial `canon/`.

## Step 2: choose or write the story idea

Offer three to five ideas fitted to the world and the audience, or take the
author's own. Every idea must keep the no-lose, clever-and-kind ethos and match the
world's peril level. A heroic world may have a fearsome foe, but it is befriended or
"falls" without cruelty, never an elimination.

## Step 3: set the parameters

Gather, with sensible defaults so a one-line request works: age tier
(`early`/`young`/`older`), which reading levels to write (`simple`, `rich`, or
both), the skill mix (from the vocabulary in `build/tags.py`), peril
(`gentle`/`mild`/`heroic`), players (min and max), play time in minutes, and any
special requirements the author states (a theme, a learning focus, a length, a
named character they want).

## Step 4: reuse canon, never redefine it

Before naming anything, read the world's `canon/*.yaml` and the repo-wide
`lexicon/terms.yaml`. Reuse existing entries with their exact en-GB, es-ES, and it-IT
names, and treat each entry's `description` as a contract: an existing gentle
creature stays gentle, a named place keeps its nature. Add a new `canon/` entry for
anything genuinely new before you use it in prose. Never rewrite an existing entry.

## Step 5: author the content

Draft **en-GB first** (the source of truth), then **every locale in
`build/locales.py` `REQUIRED_LOCALES`** (es-ES and it-IT today), translating for the
target child's ear, not word for word. Produce:

- `worlds/<world>/stories/<story>/story.yaml`: the tags and the image entries (each
  with a `prompt`, locale-neutral and text-free, plus localized `alt`, following the
  authoring skill's image rules).
- `worlds/<world>/stories/<story>/content/<locale>/`: `narration.simple.md`,
  `narration.rich.md`, `rules.md`, `puzzles.md`.
- `worlds/<world>/content/<locale>/idea-bank.md`: the world-level idea bank. Author it
  once when you create a world; when you add a story to an existing world, reuse the
  world's idea bank rather than writing a per-story one.
- For a new world: `worlds/<world>/world.yaml` and `worlds/<world>/canon/*.yaml`.

Image entries always include prompts. They do not require generated art.

## Step 6: pictures, your choice

Offer the author a choice and respect it. None of these is required for a playable kit;
the art can always be added later.

- **Generate now with your own key.** If the author has their own `OPENAI_API_KEY` in
  `.env` and wants pictures, run `python -m build generate-images --root . --world
  <world>` (omit `--story` so the world-level cover and portraits are generated too;
  the prompt filter excludes world-level images when a story is named). This uses the
  author's key only, never a maintainer key. Confirm before spending credits, target
  only this world, and eyeball each image for on-brand, text-free, gentle art.
- **Prompts only, no key.** Leave `assets/` empty. The author can export the prompts
  (`python -m build prompts --root . --world <world>`), paste them into any image
  generator they like, and drop the PNGs in as `<image-id>.png`, or just play
  text-only.
- **Bring their own art.** The author drops their own original pictures into the story
  or world `assets/` as `<image-id>.png`.

## Step 7: advisory consistency check

Read the new story's use of canon against the existing canon descriptions and the
existing stories in the world, and surface any likely contradiction (for example
using a gentle creature as a villain, or giving a place a nature that clashes with
another story). Raise these for the author to resolve. This is advisory guidance,
not a hard gate.

## Step 8: validate and build the printable kit

1. `python -m build validate --root .` and `python -m build lint --root .` (fix any
   errors; image-file warnings are expected if the author chose prompts-only).
2. Build the full kit into `dist/` (the gitignored scratch folder). Kits are
   multilingual by design, so build every required locale:

   ```bash
   for loc in en-GB es-ES it-IT; do
     python -m build render --root . --world <world> --story <story> --locale "$loc" --reading-level simple
     python -m build render --root . --world <world> --story <story> --locale "$loc" --reading-level rich
     python -m build render-playbook --root . --world <world> --story <story> --locale "$loc"
     python -m build render-world --root . --world <world> --locale "$loc"
   done
   ```

   Tell the author the PDFs are under `dist/<locale>/<world>/...` (the Story Pack to
   play from, the Grown-up's Playbook with the answers, and the World Book) and that
   they can print and play.
3. Eyeball one built Story Pack (rasterize a page) to confirm it looks right: A4, the
   front page with the world paragraph, accents render, and any images embed.

Do **not** run `python -m build rebuild`: that rewrites the committed `kits/` tree and
the root README, which is the maintainer's publish step, not a personal build.

If the author wants their story added to the public library, hand off to the
**`contribute-story`** skill (it opens a draft pull request). That is entirely
optional; the author already has their own printable kit.

## Quick checklist before you call it done

- The authoring-story-content rules were followed for all prose.
- en-GB and every required locale are present and complete.
- Every named thing is in canon with matching names; no existing entry was rewritten.
- `validate` passes and `lint` has no errors.
- The printable kit built into `dist/` and was eyeballed.
- Only the author's own OpenAI key was ever used (never a maintainer key), and built
  PDFs were not committed.
