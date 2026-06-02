---
name: create-story
description: Use when a user wants to create a new Wits & Wonder story (or a new world for one) and optionally open a pull request to contribute it. Guides choosing or creating a world, choosing or writing a story idea, setting the audience and challenges, authoring the content in every project locale (en-GB first, then es-ES) with image prompts, validating and previewing the kit, and opening a draft PR. Defers all voice, reading-level, peril-tone, and canon-name rules to the authoring-story-content skill. Trigger on requests like "create a story", "add a new adventure", "make a kit about X", "I want to contribute a story", or "start a new world".
---

# Creating a Wits & Wonder story

This skill is an **orchestrator**. It runs the interview and the mechanical steps
(scaffold, validate, preview, submit) and leaves all the writing rules to the
`authoring-story-content` skill. Your job here is to take an author from an idea to
a valid, on-brand story and, if they wish, a clean draft pull request, without ever
touching the maintainer's OpenAI key.

Read the design at
`docs/superpowers/specs/2026-06-02-community-story-contributions-design.md` for the
trust model. The short version: contributions are draft PRs a maintainer reviews;
the PR carries text and image prompts, and optionally pictures the author made
themselves; built PDFs and the maintainer's key are never in a contributor PR.

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
`lexicon/terms.yaml`. Reuse existing entries with their exact en-GB and es-ES
names, and treat each entry's `description` as a contract: an existing gentle
creature stays gentle, a named place keeps its nature. Add a new `canon/` entry for
anything genuinely new before you use it in prose. Never rewrite an existing entry.

## Step 5: author the content

Draft **en-GB first** (the source of truth), then **every locale in
`build/locales.py` `REQUIRED_LOCALES`** (es-ES today), translating for the target
child's ear, not word for word. Produce:

- `worlds/<world>/stories/<story>/story.yaml`: the tags and the image entries (each
  with a `prompt`, locale-neutral and text-free, plus localized `alt`, following the
  authoring skill's image rules).
- `worlds/<world>/stories/<story>/content/<locale>/`: `narration.simple.md`,
  `narration.rich.md`, `rules.md`, `puzzles.md`, `idea-bank.md`.
- For a new world: `worlds/<world>/world.yaml` and `worlds/<world>/canon/*.yaml`.

Image entries always include prompts. They do not require generated art.

## Step 6: pictures, optionally

Offer the author a choice, and respect it:

- **Prompts only (default, no key needed).** The maintainer illustrates the story
  after accepting it. Leave the `assets/` art empty.
- **Generate now with the author's own key.** If the author has their own
  `OPENAI_API_KEY` and wants to, run `python -m build generate-images --root .
  --world <world> --story <story>`. This uses the author's key, never the
  maintainer's.
- **Bring their own art.** The author drops their own original pictures into the
  story or world `assets/` as `<image-id>.png`.

If the author supplies art, remind them the PR will ask them to confirm it is
theirs to give.

## Step 7: advisory consistency check

Read the new story's use of canon against the existing canon descriptions and the
existing stories in the world, and surface any likely contradiction (for example
using a gentle creature as a villain, or giving a place a nature that clashes with
another story). Raise these for the author to resolve. This is advisory guidance,
not a hard gate.

## Step 8: validate, preview, and submit

Follow `references/submitting.md` exactly:

1. `python -m build validate --root .` and `python -m build lint --root .` (fix any
   errors; image-file warnings are expected for a prompts-only story).
2. `python -m build render ...` to build a preview kit the author can open, and
   `python -m build catalog --root . --out catalog.md` to refresh the catalogue.
3. Then either:
   - **Contribute:** create a branch, commit the content and any proposed art (but
     not built PDFs or anything under `dist/`), and open a **draft PR** with the
     template. Use the `gh` CLI or the GitHub MCP; if neither is authenticated,
     prepare the branch and print the exact steps for the author.
   - **Keep it for yourself:** stop here with a local kit.

## Quick checklist before you call it done

- The authoring-story-content rules were followed for all prose.
- en-GB and every required locale are present and complete.
- Every named thing is in canon with matching names; no existing entry was rewritten.
- `validate` passes and `lint` has no errors.
- The PR (if any) is a draft, carries no built PDFs, and the template is filled in.
- The maintainer's OpenAI key was never used.
