# Wits & Wonder: print presentation, the three-PDF split, and a full-page character sheet

**Status:** design for review, reached through a chat thread with the maintainer.
Decomposes into four implementation plans (see the end).

**Context:** The kits look good on screen but are not yet ideal for the thing they
are for, printing at home and running at the table. The maintainer asked for: every
PDF to be A4 as a hard rule; a white page background so kits print cleanly and
cheaply; a short world paragraph at the start of each story; a redesigned full-page
character sheet; and, after researching how published adventures are structured, to
split the single combined kit into three printable artifacts so a child never holds
the puzzle answers and the grown-up's material is not duplicated across reading
levels.

The split follows the standard adventure structure (a player book, a game-master
guide, and a setting or world book, plus components like character sheets and maps),
adapted to this project's gentle, grown-up-and-child shape.

## The three artifacts

For each story, in each locale, the build produces:

1. **Story Pack** (per story, per locale, per reading level): the child-safe play
   material the family reads from. Front page (story title, the world paragraph, the
   cover art when it exists), the narration for that reading level, the map, and the
   character sheet. Contains no puzzle answers.
2. **Grown-up's Guide** (per story, per locale, one adult level): the grown-up's
   private prep. How to run this story (its rules and difficulty bands) and the
   puzzles together with their solutions. This is the only place a solution appears,
   so a child reading the Story Pack never meets an answer.
3. **World Book** (per world, per locale, one adult level): the world reference,
   shared by every story in that world. The world cover and lore, the full Who's Who
   and What's What glossary built from canon, the world-level idea bank (improv
   fuel), and a list of the stories in the world.

The existing generic **Guide for the Grown-Up** (how to run any kit, for newcomers)
is unchanged and separate from the per-story Grown-up's Guide above.

Why this split:

- **A child never holds the answers.** Puzzle solutions live only in the Grown-up's
  Guide. The narration still presents every obstacle to players (read aloud); only
  the solution is held back.
- **No duplication across reading levels.** Rules and puzzles are a single adult
  level, so they are built once per locale instead of being copied into both the
  simple and the rich kit. The idea bank is world-level, built once per world per
  locale, instead of being copied into every story and every level.
- **The World Book is the comprehensive world PDF** the maintainer already wanted;
  it now also carries the idea bank, since the idea bank is world-generic improv fuel
  reused across the world's stories.

## Goals

1. **A4 everywhere.** Every page of every generated PDF (Story Pack, Grown-up's
   Guide, World Book, the generic Guide, the character sheet) is A4. Content pages
   are A4 portrait; the map page is A4 landscape (a wide board). Enforced in the
   renderers, not left to chance, and guarded by a test.
2. **White page background for print.** The page fill is white, not the cream tint,
   so kits print cleanly to a home printer's natural margin and use little ink. The
   coloured title banners, section headings, the dashed border, the map, and the
   illustrations stay in colour.
3. **A world paragraph at the start of each Story Pack.** Every Story Pack opens with
   a front page carrying the story title, a short paragraph about the world (reusing
   the world's `lore_summary`), and the story cover image when one exists. This also
   gives a front page to a story that has no cover art yet.
4. **The three-artifact split.** The single combined kit becomes the Story Pack
   (child-safe), the Grown-up's Guide (rules and answers), and the World Book (world
   reference and idea bank), with the idea bank moved to the world level.
5. **A full-page A4 character sheet** with a portrait and name at the top, a roomy
   magic area with three magic slots, an objects area ("What I carry") at the bottom,
   and the energy stars, filling the whole page. The sheet is a Story Pack component.

## Non-goals (deferred)

- Generating the Greek world's art or a Greek map. The world paragraph, all three
  artifacts, and the character sheet work text-only; illustrations remain a separate,
  optional step the maintainer runs when they choose.
- Borderless ("full bleed") printing. We design for ordinary home printers with a
  white margin, which is why the background is white rather than a tint pushed to the
  edge.
- Per-world character-sheet labels (for example saying "hero quality" instead of
  "magic" in the non-magic Greek world). The sheet label stays generic; the Greek
  rules already bridge it. Revisit later if wanted.
- Story-specific idea banks. The idea bank moves to the world level and is shared by
  the world's stories. If a story ever needs its own improv prompts, that is future
  work; today each world has one story, so the move is a clean relocation.
- A combined "everything" PDF. Anyone who wants one file can print the three together;
  we do not also build a merged kit.

## Part 1: print presentation (A4 hard rule and white background)

### A4 everywhere

- `build/render/pages.py` already builds A4 portrait pages; keep that, and make A4
  the only size for flowable pages (the `landscape_page` option stays only for any
  genuinely wide flowable page, currently none).
- `build/render/map.py` currently renders the map SVG at the SVG's own size. Change
  it so the map page is **A4 landscape** regardless of the source SVG's dimensions:
  render the SVG fit onto an A4 landscape page, preserving aspect (centre it, do not
  distort). A contributed map of any size then still produces an A4 landscape page.
- Add a test that builds a Story Pack and asserts **every page** is A4, within a
  small tolerance, in one of the two orientations (210 by 297 mm portrait, or 297 by
  210 mm landscape). This makes "A4 always" a checked invariant. Extend it to the
  Grown-up's Guide and the World Book once those builders exist.

### White page background

- `build/render/theme.py` `page_painter` currently fills the page with
  `theme.background` (the world's cream). Change the page fill to **white**. Keep the
  dashed border (light green) and everything coloured (banners via the `h1` style's
  `backColor`, headings, table headers, the map, the images).
- `build/render/sheets.py` currently fills the sheet background with
  `theme.background`; change that fill to white too.
- The map board keeps its own painted sky background (that is board art, not the page
  fill). The cover and scene images keep their own art. Only the page fill changes.
- `theme.Theme.background` stays on the model (worlds still declare a palette), but
  the printable page fill no longer uses it. A `palette[0]` is still meaningful for
  any future on-screen or tinted use; print simply ignores it.

## Part 2: the Story Pack (front page, world paragraph, child-safe play material)

The combined kit becomes the **Story Pack**. The builder is the existing
`build/render/kit.py`, renamed in intent to building the Story Pack; the public
function becomes `build_story_pack(root, world, story, locale, reading_level,
out_dir) -> Path` (the old `build_kit` name is updated at its call sites: the CLI,
the two GitHub workflows, and the tests).

Front page (always renders), built by a small helper in `build/render/images.py` (or
a `frontpage` helper) and called first:

- The story **title** as the `h1` banner.
- A short **world paragraph**: the world's `lore_summary[locale]`, in the body or
  italic style. This is the "paragraph at the beginning of each story".
- The story **cover image** if `assets/<cover-id>.png` exists, scaled to fit the
  space under the title and paragraph; omitted cleanly if there is no cover art.

Story Pack page order: front page, map (A4 landscape, if the world has one),
narration for the chosen reading level, story-in-pictures gallery (if the story has
scene art), character sheet.

What the Story Pack **no longer contains** (these move out): the rules, the puzzles
and answers, the idea bank, and the Who's Who glossary. Rules and puzzles go to the
Grown-up's Guide (Part 3); the glossary and idea bank go to the World Book (Part 4).
The narration still presents every obstacle to the players; only the answers leave.

Output name: `<world>_<story>_<locale>_<level>.pdf` (unchanged from today, so the
Story Pack keeps the current kit filenames and the existing README links still
resolve to the play material).

## Part 3: the Grown-up's Guide (per story)

A new builder and CLI command produce one Grown-up's Guide per story per locale, at a
single adult reading level (not per reading level).

- New `build/render/grownup_guide.py` with `build_grownup_guide(root, world, story,
  locale, out_dir) -> Path`, reusing the flowable and prose helpers.
- Contents, in order, on A4 portrait pages with the white background and the world's
  theme:
  1. **Title**: "Grown-up's Guide" plus the story title (in the locale) as the `h1`
     banner.
  2. **How to run this story**: the story's `rules.md` (difficulty bands, the no-lose
     golden rule, the newcomer callout).
  3. **Puzzles and answers**: the story's `puzzles.md`, the challenges together with
     their solutions. A short note at the top reminds the grown-up this is the only
     part not meant for the child's eyes.
- New CLI subcommand `python -m build render-grownup --root . --world <w> --story <s>
  --locale <loc> [--out-dir <dir>]`.
- Output name: `<world>_<story>_<locale>_grownup.pdf`.

This is distinct from the generic, world-agnostic **Guide for the Grown-Up**
(`render-guide`, `Guide_for_the_Grown-Up_<locale>.pdf`), which stays as is and
teaches a newcomer how to run any kit.

## Part 4: the World Book (per world) and moving the idea bank to the world level

A new builder and CLI command produce one World Book per world per locale.

### Moving the idea bank to the world level

The idea bank is world-generic improv fuel, so it moves from the story to the world.

- New content location: `worlds/<world>/content/<locale>/idea-bank.md` (a world-level
  prose file), replacing the per-story
  `worlds/<world>/stories/<story>/content/<locale>/idea-bank.md`.
- `build/render/content.py` (the loader) reads the idea bank from the world-level
  path. The per-story `idea-bank.md` is no longer required for a story to be
  complete; the lint's "required content file" check drops `idea-bank.md` from the
  per-story, per-locale set and gains a per-world, per-locale check that the
  world-level idea bank exists for every required locale.
- Migrate the two existing idea banks (Floating Isles, Greek myth) from their story
  folders to the new world-level path. Each world has one story today, so this is a
  move, not a merge.
- The `authoring-story-content` skill and the `create-story` skill references are
  updated so the idea bank is authored once per world, not per story.

### The World Book builder

- New `build/render/world_pdf.py` with `build_world_pdf(root, world_id, locale,
  out_dir) -> Path`, reusing the existing cover, glossary, and flowable helpers.
- Contents, in order, on A4 portrait pages with the white background and the world's
  theme:
  1. **Cover**: the world name as the `h1` banner, the world cover image if it
     exists, and the world `lore_summary`.
  2. **Who's Who and What's What**: the full canon glossary
     (`glossary.glossary_flowables`) with portraits when world or story art exists.
  3. **Idea bank**: the world-level idea bank prose.
  4. **Stories in this world**: a short list built from each `story.yaml` in the
     world, each line giving the story title (in the locale), the recommended age
     tier, and a one-line hook (the first sentence of the story's
     `narration.simple.md`, or a fixed fallback if absent).
- New CLI subcommand `python -m build render-world --root . --world <w> --locale
  <loc> [--out-dir <dir>]`.
- Output name: `<world>_<locale>.pdf`.

## Part 5: the full-page A4 character sheet

Redesign `build/render/sheets.py` so the `young` and `older` tiers fill the whole A4
page with clearly bordered, colour-coded sections. `early` stays a large
draw-your-hero box plus a name, for the youngest children. The sheet is a Story Pack
component.

Layout for `young` and `older`, top to bottom, filling the page:

1. **Title banner** (full width): "My Adventure Sheet".
2. **Identity row**: a bordered **portrait box** ("Draw your hero") on the left, and
   on the right "My name", "I am a hero of", and beneath them the five **energy
   stars** labelled "My energy stars".
3. **My magics** box (bordered, the world primary colour): three magic slots. Each
   slot has a square on the left to draw the magic's symbol, and two lines to its
   right, "My magic is" and "It can". So three magics, each split across two lines.
4. **What I carry** box (bordered, a world accent colour) at the bottom: six labelled
   slots (a two-column, three-row grid of writing lines) for the objects, bricks, or
   treasures the character holds. Present for `young` as well as `older`.
5. **Notes** (a couple of lines): `older` only.
6. **Footer**: the existing "here nobody loses" line.

New localized strings in `build/render/strings.py` (en-GB and es-ES), alongside the
existing sheet labels: `sheet_hero_type` ("I am a hero of" / "Soy un heroe de"),
`sheet_magics` ("My magics" / "Mis magias"), `sheet_magic_is` ("My magic is" / "Mi
magia es"), `sheet_magic_does` ("It can" / "Puede"), and `sheet_magic_symbol`
("draw it" / "dibujala"). Reuse the existing `sheet_title`, `sheet_name`,
`sheet_draw`, `sheet_energy`, `sheet_inventory` ("What I carry"), `sheet_notes`, and
`sheet_footer`. Drop the old single `sheet_magic` line in favour of `sheet_magics`
plus the per-slot helpers.

The sheet stays one A4 page per tier and keeps its existing test shape (each tier
renders one page; unknown tier raises; es-ES renders). The drawing uses the world's
accent colours for the section borders so the boxes are colour-coded.

A known limitation carried over: the sheet says "magic", which suits the magic
worlds; the non-magic Greek rules tell players to write their hero quality there.
Per-world sheet labels are deferred.

## The README and the kits folder

After the builders exist, rebuild `kits/` to hold the three artifacts and refresh the
README. The download section gains, per story, the Story Pack links (by reading
level) and the Grown-up's Guide link, with a separate short "World books" list giving
one World Book per world per locale.

Proposed download layout (the maintainer may rename the artifacts):

- A story table: columns for Story, World, Ages, the **Story Pack** links (Simple and
  Rich) in English and in Spanish, and the **Grown-up's Guide** link in each language.
- A **World books** subsection: one line per world, linking the World Book in English
  and in Spanish.
- The existing **Guide for the Grown-Up** callout, unchanged.

A note explains the split in one or two sentences: the Story Pack is what you play
from and is safe for the child to see; the Grown-up's Guide holds the answers; the
World Book is the world's lore and ideas.

## Testing

- A new test asserts every page of a built Story Pack is A4 (portrait or landscape);
  extended to the Grown-up's Guide and the World Book.
- The white background is a visual change; verify by rasterising a page and confirming
  the page fill is white with the coloured elements intact.
- The front page renders for a story with no cover image (title plus world paragraph,
  no image) and for one with a cover image (title, paragraph, image), and the Story
  Pack gains exactly one front page.
- The Story Pack no longer contains the rules, puzzles, idea bank, or glossary
  (assert those sections are absent from its flowables).
- `grownup_guide.build_grownup_guide` produces a valid A4 PDF containing the rules and
  the puzzles-and-answers for a story; tested against the sample repo and a fixture.
- The idea-bank relocation: the loader reads the world-level idea bank; the lint
  accepts a world whose idea bank is world-level and flags a world missing it;
  `validate` and `lint` stay green after the two real idea banks are moved.
- `world_pdf.build_world_pdf` produces a valid multi-page A4 PDF for a world, with the
  glossary, the idea bank, and the stories list present; tested against the sample
  repo and a fixture world.
- The character sheet renders one A4 page for `young` and `older` with the three magic
  rows and the "What I carry" grid; `early` still renders; es-ES renders.
- The full suite, `validate`, and `lint` stay green.

## Decomposition into implementation plans

1. **Plan 1: print presentation.** A4 hard rule (map to A4 landscape plus the
   page-size test) and the white background (painter and sheet fill). Small and
   self-contained; ship first so everything afterwards inherits it.
2. **Plan 2: the Story Pack.** Rename `build_kit` to `build_story_pack`, add the
   always-on front page with the world paragraph, and remove the rules, puzzles, idea
   bank, and glossary from the pack. Update the CLI, the two workflows, and the tests.
3. **Plan 3: the Grown-up's Guide and the World Book.** Move the idea bank to the
   world level (content move, loader, lint), then build `grownup_guide.py`
   (`render-grownup`) and `world_pdf.py` (`render-world`). Update the authoring and
   create-story references for the world-level idea bank.
4. **Plan 4: the full-page character sheet.** The `sheets.py` redesign and the new
   strings.

After all four, rebuild `kits/` with the three artifacts per story plus the World
Books, regenerate the catalogue, and refresh the README links and the split note.

## Decisions made for the maintainer to confirm

- The combined kit splits into three artifacts: **Story Pack** (child-safe play
  material), **Grown-up's Guide** (rules and puzzle answers, per story), and **World
  Book** (lore, glossary, idea bank, per world). No merged "everything" PDF is built.
- The **idea bank moves to the world level** (`worlds/<world>/content/<locale>/
  idea-bank.md`) and is shared by the world's stories.
- Puzzle **answers appear only in the Grown-up's Guide**; the Story Pack presents
  obstacles through narration but holds no solutions.
- Filenames: Story Pack keeps `<world>_<story>_<locale>_<level>.pdf`; the Grown-up's
  Guide is `<world>_<story>_<locale>_grownup.pdf`; the World Book is
  `<world>_<locale>.pdf`. The per-story Grown-up's Guide is distinct from the generic
  Guide for the Grown-Up.
- The world paragraph reuses the existing `lore_summary` rather than a new short
  field, for simplicity and no new authoring.
- The map page is landscape A4; everything else is portrait A4. A Story Pack therefore
  mixes orientations, which is fine since both are A4.
- The page background is white; the cream `palette[0]` is no longer used for the
  printable page fill.
- The front page always renders (so a story with no cover art still gets a title and
  world paragraph), replacing the old cover-only-when-art behaviour.
- The character sheet has three magic slots and a six-slot "What I carry" grid; the
  generic "magic" label is kept.

## Future work (named, not built here)

- Generate the Greek world's art and a Greek map so its Story Pack and World Book are
  fully illustrated.
- Per-world character-sheet labels (for example "hero quality" for non-magic worlds).
- Attaching the three PDFs to GitHub Releases alongside the kits.
- Optional story-specific idea-bank additions layered on top of the world idea bank.
