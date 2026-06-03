# Wits & Wonder: print presentation, the three-PDF split, versioning, and a full-page character sheet

**Status:** design for review, reached through a chat thread with the maintainer.
Decomposes into six implementation plans (see the end). The per-story grown-up
document is named the **Grown-up's Playbook**. Content is licensed **CC BY-SA 4.0**
and the code **MIT**.

**Context:** The kits look good on screen but are not yet ideal for the thing they
are for, printing at home and running at the table. The maintainer asked for: every
PDF to be A4 as a hard rule; a white page background so kits print cleanly and
cheaply; a short world paragraph at the start of each story; a redesigned full-page
character sheet; to split the single combined kit (after researching how published
adventures are structured) into three printable artifacts so a child never holds the
puzzle answers and the grown-up's material is not duplicated across reading levels; a
language-first output tree that scales to roughly 7 worlds, 10 stories each, and 3 or
more languages; an automatic version on every PDF (in the file and in its name, with
nothing to maintain by hand); and a colophon end page on every PDF carrying the
project link and licence.

The split follows the standard adventure structure (a player book, a game-master
guide, and a setting or world book, plus components like character sheets and maps),
adapted to this project's gentle, grown-up-and-child shape.

## The three artifacts

For each story, in each locale, the build produces:

1. **Story Pack** (per story, per locale, per reading level): the child-safe play
   material the family reads from. Front page (story title, the world paragraph, the
   cover art when it exists), the narration for that reading level, the map, and the
   character sheet. Contains no puzzle answers.
2. **Grown-up's Playbook** (per story, per locale, one adult level): the grown-up's
   private prep. How to run this story (its rules and difficulty bands) and the
   puzzles together with their solutions. This is the only place a solution appears,
   so a child reading the Story Pack never meets an answer.
3. **World Book** (per world, per locale, one adult level): the world reference,
   shared by every story in that world. The world cover and lore, the full Who's Who
   and What's What glossary built from canon, the world-level idea bank (improv
   fuel), and a list of the stories in the world.

The existing generic **Guide for the Grown-Up** (how to run any kit, for newcomers)
is unchanged and separate from the per-story Grown-up's Playbook above.

Why this split:

- **A child never holds the answers.** Puzzle solutions live only in the Grown-up's
  Playbook. The narration still presents every obstacle to players (read aloud); only
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
   Playbook, World Book, the generic Guide, the character sheet) is A4. Content pages
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
   (child-safe), the Grown-up's Playbook (rules and answers), and the World Book (world
   reference and idea bank), with the idea bank moved to the world level.
5. **A full-page A4 character sheet** with a portrait and name at the top, a roomy
   magic area with three magic slots, an objects area ("What I carry") at the bottom,
   and the energy stars, filling the whole page. The sheet is a Story Pack component.
6. **A language-first output tree** under `kits/` (and `dist/`) that scales to many
   worlds, stories, and languages, with each builder writing its own nested path.
7. **Automatic versioning.** Every PDF carries a version derived at build time from
   git history over its own source files, shown both in the file (colophon and
   metadata) and in its filename. Nothing is bumped by hand.
8. **A colophon and licensing.** Every PDF ends with a colophon page (project link,
   licence, version, and a QR to the latest version); the content is licensed CC BY-SA
   4.0 and the code MIT, recorded in `LICENSE` and `LICENSE-CONTENT` and on the
   colophon.
9. **A per-page footer.** Every page carries a discreet footer in the bottom margin
   with the kit identity, locale, version, and `page x of y`, stamped in a final pass
   over the merged PDF.

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
  Grown-up's Playbook and the World Book once those builders exist.

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
Grown-up's Playbook (Part 3); the glossary and idea bank go to the World Book (Part 4).
The narration still presents every obstacle to the players; only the answers leave.

Output path (see "The kits folder structure" below): `<out_dir>/<locale>/<world>/
<story>/story-pack-<level>-v<version>.pdf`, where `<version>` is the automatic build
version from Part 6.

## Part 3: the Grown-up's Playbook (per story)

A new builder and CLI command produce one Grown-up's Playbook per story per locale, at a
single adult reading level (not per reading level).

- New `build/render/playbook.py` with `build_playbook(root, world, story,
  locale, out_dir) -> Path`, reusing the flowable and prose helpers.
- Contents, in order, on A4 portrait pages with the white background and the world's
  theme:
  1. **Title**: "Grown-up's Playbook" plus the story title (in the locale) as the `h1`
     banner.
  2. **How to run this story**: the story's `rules.md` (difficulty bands, the no-lose
     golden rule, the newcomer callout).
  3. **Puzzles and answers**: the story's `puzzles.md`, the challenges together with
     their solutions. A short note at the top reminds the grown-up this is the only
     part not meant for the child's eyes.
- New CLI subcommand `python -m build render-playbook --root . --world <w> --story <s>
  --locale <loc> [--out-dir <dir>]`.
- Output path: `<out_dir>/<locale>/<world>/<story>/playbook-v<version>.pdf`.

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
- Output path: `<out_dir>/<locale>/<world>/world-book-v<version>.pdf`.

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

## Part 6: automatic versioning

Every generated PDF carries a version, and **nothing about it is manual**. The
version is computed at build time from git history over exactly the source files that
compose that PDF. Authors never edit a version field; the version simply reflects how
many times the relevant content has changed and when it last changed.

A new module `build/render/version.py` provides:

- `version_info(root, paths) -> VersionInfo`, where `VersionInfo` has `number: int`
  and `updated: str` (an ISO `YYYY-MM-DD` date). It runs git over the given paths:
  `number` is the count of commits that touched any of those paths
  (`git -C <root> log --format=%H -- <paths>` line count), and `updated` is the date
  of the most recent such commit (`git -C <root> log -1 --format=%cs -- <paths>`).
- A per-artifact input-path helper so each builder asks for the version of *its own*
  inputs. The input sets are:
  - **Story Pack** (world, story, locale, level): `story.yaml`, the story's
    `content/<locale>/narration.<level>.md`, `world.yaml`, and the map and cover asset
    files it actually resolves.
  - **Grown-up's Playbook** (world, story, locale): `story.yaml`, the story's
    `content/<locale>/rules.md` and `content/<locale>/puzzles.md`, and `world.yaml`.
  - **World Book** (world, locale): `world.yaml`, the world `canon/*.yaml`, the
    world-level `content/<locale>/idea-bank.md`, every story's `story.yaml`, and each
    story's `content/<locale>/narration.simple.md` (used for the hook).
  - **Guide for the Grown-Up** (locale): `guide/<locale>/guide.md`.

Scoping the version to the exact inputs makes it correct per locale and per level for
free: if only the en-GB narration changes, the it-IT Story Pack's version does not
move, but a change to the shared map or `world.yaml` bumps every artifact that uses
it. That answers the "one language is ahead of another" case without any manual
bookkeeping.

Edge cases:

- **Uncommitted inputs.** If any input file has uncommitted changes (a local working
  build before commit), `version_info` appends a `+` to the displayed label (for
  example `v7+`) and uses `number` as the last committed count. This keeps a
  work-in-progress build honestly distinct from the released one. The committed
  library is always built from a clean tree, so its filenames never carry the `+`.
- **No git or no history.** `version_info` falls back to `number = 0` and
  `updated = "unreleased"`. For tests, `version_info` is injectable (the builders take
  an optional `VersionInfo` so a fixture can pass a fixed value and keep PDFs
  byte-stable), so the suite never depends on the repository's real history.

Where the version surfaces:

1. In the **filename** as a `-v<number>` suffix on every leaf (see the folder tree).
2. On the **colophon** end page (Part 7), as `Version <number>, updated <updated>`.
3. In the **PDF metadata** set on the final merged file (via pypdf): `/Title` (story
   or world name, artifact type, locale, version), `/Author` ("Wits and Wonder"),
   `/Subject` (artifact and version and date), `/Keywords` (world, story, locale,
   level, version). Metadata text uses commas as separators, never a dash.

Because the version lives in the filename, the committed `kits/` tree holds only the
latest edition of each artifact: a `rebuild` step builds the whole library, then
prunes any `*-v<old>.pdf` that the build did not just write, and regenerates the
catalogue and the README download block (Part 5's "The README" section). `rebuild` is
a new CLI subcommand, `python -m build rebuild --root . [--out-dir kits]`, and is what
the art-and-release workflow calls instead of an inline per-kit loop.

## Part 7: the colophon (end page) and licensing

Every artifact (Story Pack, Grown-up's Playbook, World Book, and the generic Guide)
ends with a **colophon page**: a calm, single A4 page on the white background and the
world theme, drawn by a new helper `build/render/colophon.py`
`colophon_flowables(theme, locale, version_info, artifact_label) -> list`. It carries:

- The project name, **Wits and Wonder**, and the project link,
  `https://github.com/agigante80/wits-and-wonder`.
- The licensing line: **content is CC BY-SA 4.0**
  (`https://creativecommons.org/licenses/by-sa/4.0/`), with a short "share it, keep it
  open, credit Wits and Wonder" gloss. The colophon states the content licence, since
  that is what governs the PDF; the code licence (MIT) is documented in the repo, not
  on the kit.
- The version line, `Version <number>, updated <updated>, <locale>`.
- A **QR code** that links to the latest version of this artifact. A printed kit is
  frozen at the version it was printed at, so the QR is how a reader gets the current
  one or finds the project. It encodes the artifact's directory on GitHub, which always
  shows the newest versioned file:
  - Story Pack and Playbook:
    `https://github.com/agigante80/wits-and-wonder/tree/main/kits/<locale>/<world>/<story>`
  - World Book: `.../tree/main/kits/<locale>/<world>`
  - Guide: `.../tree/main/kits/guides`
  A short caption sits under it ("Scan for the latest version"). The QR is generated
  with `segno` (a pure-Python, dependency-light QR library added to the `render`
  extra), rendered to an SVG or PNG and embedded like any other image.
- The promise line already used on the character sheet ("here nobody loses, you just
  look for another way").

The colophon's words are localized, so `build/render/strings.py` gains
`colophon_project`, `colophon_licence`, `colophon_version`, `colophon_qr_caption`, and
`colophon_promise` in en-GB and es-ES (and it-IT when that locale lands). The licence
code ("CC BY-SA 4.0"), the URLs, and the QR image itself are locale-neutral and not
translated.

Two licence files are added at the repository root, and the README documents the dual
licence:

- `LICENSE` holds the **MIT** licence for the code (the `build/` package and the
  tests), with the copyright line for the maintainer.
- `LICENSE-CONTENT` holds the **CC BY-SA 4.0** licence (its full text or the canonical
  deed link plus a short statement) for everything under `worlds/`, `guide/`,
  `lexicon/`, and the generated PDFs in `kits/`.

The README gains a short **Licence** section naming both: content under CC BY-SA 4.0,
code under MIT, with the two links. Contributors agree, by opening a PR, that their
contribution is offered under these same terms; a line to that effect goes in
`CONTRIBUTING.md` and the PR template.

## Part 8: the per-page footer

Every page of every artifact carries a discreet footer in the bottom margin, so a
loose printed page can always be identified and re-found. Because each artifact is
assembled from several independently built sub-PDFs (narration from reportlab, the map
from cairosvg, the sheet from a canvas) and merged with pypdf, the footer is applied in
a **final stamping pass over the merged PDF**, which is the only point where the total
page count is known and where both portrait and landscape pages can be handled
uniformly. A new helper `build/render/footer.py` `stamp_footers(pdf_path, label,
version_info, locale)` reads each page's size, builds a matching reportlab overlay, and
merges it onto that page with pypdf. Every builder calls it as its last step.

The footer is one thin line, small and grey, with two ends:

- **Left, the identity:** `Wits and Wonder` then the artifact and its title, for
  example `Wits and Wonder . Story Pack . The Sleeping Garden` (middle dots, never a
  dash). A readable label is used rather than the raw filename, because the filename is
  generic and versioned; the label plus the version below identify the file, and the
  exact path is one tap away through the colophon QR.
- **Right, the locator:** `<locale> . v<version> . page <x> of <y>`.

The footer is drawn on the map and character-sheet pages too (in the white bottom
margin, clear of the art), so `page x of y` is continuous and honest across the whole
document. The colophon page carries it as well.

## The kits folder structure (built output)

The library is heading for roughly 7 worlds, 10 stories each, and 3 or more
languages (en-GB and es-ES today, it-IT next). That is on the order of 650 PDFs, so
the output is a **language-first tree**, not a flat folder. Every builder writes into
this tree under its `out_dir` (which is `kits/` for the committed library and `dist/`
for scratch builds); the builders compute the nested subpath, callers only pass the
root `out_dir`.

```
kits/
  <locale>/
    <world>/
      world-book-v<version>.pdf
      <story>/
        story-pack-simple-v<version>.pdf
        story-pack-rich-v<version>.pdf
        playbook-v<version>.pdf
  guides/
    Guide_for_the_Grown-Up_<locale>-v<version>.pdf
```

A worked example (versions differ per artifact because they track different files):

```
kits/
  it-IT/
    floating-isles/
      world-book-v4.pdf
      sleeping-garden/
        story-pack-simple-v7.pdf
        story-pack-rich-v7.pdf
        playbook-v3.pdf
  en-GB/
    floating-isles/
      ...
  guides/
    Guide_for_the_Grown-Up_it-IT-v2.pdf
```

Notes on this layout:

- **Language is the top level**, so all of one language's material sits together (a
  reader can grab everything Italian at once), and a new language is a new top-level
  folder with no churn to the others.
- **Leaf filenames are type plus version** (`story-pack-rich-v7.pdf`,
  `playbook-v3.pdf`, `world-book-v4.pdf`): the path already says the language, world,
  and story, so the leaf only adds the artifact type and its automatic version (Part
  6). A downloaded file is therefore named generically apart from the version; the
  README link text carries the rest of the context.
- The **World Book** sits at `kits/<locale>/<world>/world-book-v<version>.pdf`,
  beside the world's story folders.
- The generic **Guide for the Grown-Up** stays in `kits/guides/` with the locale and
  version in its filename, since it is world-agnostic and lives outside any one
  language's world tree.
- **Only the latest version of each artifact is kept.** Because the version is in the
  filename, a content change produces a new leaf name; the rebuild (Part 6) deletes
  the superseded `*-v<old>.pdf` for that artifact so the tree never accumulates stale
  editions. History stays in git, not as a pile of PDFs.
- `dist/` (scratch, gitignored) uses the identical structure, so a single render and
  the committed library never disagree on where a file goes.

The `find_map` and asset-resolution paths under `worlds/` are unaffected; only the
**output** tree changes.

## The README download section is generated

Because the version is in the filename, every content change renames a file, so the
README download links cannot be hand-maintained. The **rebuild generates them**. The
download block lives between two HTML-comment markers in `README.md`:

```
<!-- BEGIN KIT TABLE -->
... generated rows ...
<!-- END KIT TABLE -->
```

`rebuild` (Part 6) walks the built `kits/` tree and rewrites everything between the
markers, leaving the rest of the README (prose, how-to-run, contributing) untouched.
The generated block contains:

- A story table: columns for Story, World, Ages, the **Story Pack** links (Simple and
  Rich) in each language, and the **Grown-up's Playbook** link in each language. As
  languages grow past three, the generator emits per-language rows rather than ever
  wider columns, to keep the table readable.
- A **World books** subsection: one line per world, linking its World Book in each
  language.
- The existing **Guide for the Grown-Up** callout, regenerated with current versions.

Outside the markers, the README also gains (hand-written, one time): the one or two
sentence note explaining the split (the Story Pack is what you play from and is safe
for the child to see; the Grown-up's Playbook holds the answers; the World Book is the
world's lore and ideas), and the licensing section from Part 7.

## Testing

- A new test asserts every page of a built Story Pack is A4 (portrait or landscape);
  extended to the Grown-up's Playbook and the World Book.
- The white background is a visual change; verify by rasterising a page and confirming
  the page fill is white with the coloured elements intact.
- The front page renders for a story with no cover image (title plus world paragraph,
  no image) and for one with a cover image (title, paragraph, image), and the Story
  Pack gains exactly one front page.
- The Story Pack no longer contains the rules, puzzles, idea bank, or glossary
  (assert those sections are absent from its flowables).
- `playbook.build_playbook` produces a valid A4 PDF containing the rules and
  the puzzles-and-answers for a story; tested against the sample repo and a fixture.
- The idea-bank relocation: the loader reads the world-level idea bank; the lint
  accepts a world whose idea bank is world-level and flags a world missing it;
  `validate` and `lint` stay green after the two real idea banks are moved.
- `world_pdf.build_world_pdf` produces a valid multi-page A4 PDF for a world, with the
  glossary, the idea bank, and the stories list present; tested against the sample
  repo and a fixture world.
- The character sheet renders one A4 page for `young` and `older` with the three magic
  rows and the "What I carry" grid; `early` still renders; es-ES renders.
- `version_info` returns the commit count and last-changed date for a set of paths in
  a small fixture git repo, marks a dirty input with `+`, and falls back cleanly when
  there is no history. Builders accept an injected `VersionInfo` so PDF tests stay
  byte-stable and do not depend on the real repository history.
- Every artifact's filename ends with `-v<number>.pdf`, and its last page is the
  colophon carrying the project link, the CC BY-SA 4.0 licence line, the version line,
  and a QR code. The colophon renders in es-ES as well as en-GB.
- After stamping, every page (portrait and landscape) carries the footer, the `page x
  of y` count matches the document's page total, and `y` is identical on every page.
- `rebuild` builds the whole library into a tmp `out_dir`, writes only versioned leaf
  files, prunes a planted stale `*-v<old>.pdf`, regenerates the catalogue, and
  rewrites only the text between the README markers (asserting the surrounding README
  is untouched).
- `LICENSE` (MIT) and `LICENSE-CONTENT` (CC BY-SA 4.0) exist at the repo root.
- The full suite, `validate`, and `lint` stay green.

## Impact on skills, scripts, and docs

Beyond the new and changed render modules, these existing files change. The plans
below own them; this list is the checklist.

- **`build/__main__.py` (CLI).** `render` now builds the Story Pack
  (`build_story_pack`). Add `render-playbook` (world, story, locale), `render-world`
  (world, locale), and `rebuild` (build the whole library, prune stale versions,
  regenerate the catalogue, rewrite the README block). `render-guide` now writes under
  `<out_dir>/guides/` with the version suffix. Update the module docstring's command
  list.
- **`build/render/kit.py`.** `build_kit` becomes `build_story_pack`: strips rules,
  puzzles, idea bank, and glossary; adds the front page and the colophon; sets PDF
  metadata; stamps the footer; writes the versioned, nested path.
- **`build/render/pages.py`.** `render_guide` gains the colophon, the footer, metadata,
  and the versioned filename.
- **`pyproject.toml`.** Add `segno` to the `render` extra for the colophon QR.
- **`build/content.py`.** Load the idea bank from the world-level path.
- **`build/lint.py`.** Drop `idea-bank.md` from the per-story required set; add a
  per-world, per-locale check that the world idea bank exists.
- **`build/catalog.py`.** Optionally add a version column (the Story Pack version per
  story and locale); at minimum, keep working after the idea-bank move.
- **`.github/workflows/validate-pr.yml`.** Rename `build_kit` to `build_story_pack`;
  set `fetch-depth: 0` on checkout so `version_info` can read history; build the Story
  Pack preview (the versioned path is fine in `preview/`).
- **`.github/workflows/build-art.yml`.** Set `fetch-depth: 0`; replace the inline
  per-kit loop with `python -m build rebuild --root . --out-dir kits`; commit the
  nested tree, the catalogue, and the regenerated README block.
- **`.claude/skills/authoring-story-content/SKILL.md`.** In the content-types table,
  move `idea-bank.md` to the world level and mark its audience; note that a kit is now
  three artifacts; note that version, colophon, and licence are automatic so authors
  never touch them.
- **`.claude/skills/create-story/SKILL.md` and `references/`.** Step 5 authors the
  idea bank once per world (and, for an existing world, reuses it); the preview step
  may also build the Playbook and World Book; note the automatic version, colophon,
  and licence; state in `submitting.md` that contributors still never commit PDFs and
  that opening a PR offers the work under CC BY-SA 4.0.
- **`README.md`.** The generated download block between markers; the split note; the
  new Licence section; the updated command list (`render-playbook`, `render-world`,
  `rebuild`).
- **`CONTRIBUTING.md` and `.github/pull_request_template.md`.** A line that
  contributions are offered under CC BY-SA 4.0 (content) and MIT (code).
- **New root files.** `LICENSE` (MIT) and `LICENSE-CONTENT` (CC BY-SA 4.0).

## Decomposition into implementation plans

1. **Plan 1: print presentation.** A4 hard rule (map to A4 landscape plus the
   page-size test) and the white background (painter and sheet fill). Small and
   self-contained; ship first so everything afterwards inherits it.
2. **Plan 2: versioning, colophon, footer, and licences (foundation).** Add
   `build/render/version.py` (git-based `version_info` plus the per-artifact input-path
   helpers), `build/render/colophon.py` and its strings (including the `segno` QR),
   `build/render/footer.py` (the merged-PDF footer-stamping pass), a PDF-metadata
   helper, the `segno` dependency in the `render` extra, and the `LICENSE` and
   `LICENSE-CONTENT` files. Wire the colophon, footer, metadata, and versioned filename
   into the two builders that exist today (the kit and the guide) so the whole
   page-furniture convention is proven before the new artifacts adopt it.
3. **Plan 3: the Story Pack.** Rename `build_kit` to `build_story_pack`, add the
   always-on front page with the world paragraph, remove the rules, puzzles, idea
   bank, and glossary, and write the language-first versioned path
   (`<out_dir>/<locale>/<world>/<story>/story-pack-<level>-v<version>.pdf`). Update the
   CLI and the two workflows. The output-tree convention lands here; Plan 4's builders
   follow the same pattern.
4. **Plan 4: the Grown-up's Playbook and the World Book.** Move the idea bank to the
   world level (content move, loader, lint), then build `playbook.py`
   (`render-playbook`) and `world_pdf.py` (`render-world`), each with its colophon,
   metadata, and version. Update the authoring and create-story references for the
   world-level idea bank.
5. **Plan 5: the full-page character sheet.** The `sheets.py` redesign and the new
   strings.
6. **Plan 6: rebuild, README generation, and docs.** The `rebuild` CLI subcommand
   (build all, prune superseded versions, regenerate the catalogue, rewrite the README
   block), the README Licence section and split note, the `CONTRIBUTING.md` and PR
   template licence line, and the final library rebuild into `kits/`.

After all six, the committed `kits/` holds the three versioned artifacts per story
plus the World Books and Guides, the catalogue and README block are regenerated, and
the old flat kit files are removed in the same rebuild commit.

## Decisions made for the maintainer to confirm

- The combined kit splits into three artifacts: **Story Pack** (child-safe play
  material), **Grown-up's Playbook** (rules and puzzle answers, per story), and **World
  Book** (lore, glossary, idea bank, per world). No merged "everything" PDF is built.
- The **idea bank moves to the world level** (`worlds/<world>/content/<locale>/
  idea-bank.md`) and is shared by the world's stories.
- Puzzle **answers appear only in the Grown-up's Playbook**; the Story Pack presents
  obstacles through narration but holds no solutions.
- Output is a **language-first tree** under `kits/` (and `dist/`):
  `<locale>/<world>/world-book-v<n>.pdf` and `<locale>/<world>/<story>/
  {story-pack-simple,story-pack-rich,playbook}-v<n>.pdf`, with the generic Guide in
  `kits/guides/`. Leaf names are type plus version (the path carries the language,
  world, and story). The per-story Grown-up's Playbook is distinct from the generic
  Guide for the Grown-Up.
- **Versioning is automatic and git-derived**, per artifact, from that artifact's own
  source files: `version` is the commit count, `updated` is the last-changed date.
  Nothing is bumped by hand, and a different language being behind does not bump the
  others. The version shows in the filename, on the colophon, and in PDF metadata; only
  the latest version of each artifact is kept in `kits/`.
- Every PDF ends with a **colophon page** carrying the project link
  (`github.com/agigante80/wits-and-wonder`), the content licence, the version line, and
  a **QR code** to that artifact's GitHub directory (its latest version). The QR target
  is the per-artifact folder rather than the repo root, so a scan lands on the current
  file; confirm if you would rather it point at the repo root or a Releases page.
- Every page carries a **discreet footer** with the kit identity, locale, version, and
  `page x of y`, stamped over the merged PDF. The identity is a readable label (project,
  artifact, title), not the raw versioned filename; confirm if you would rather the
  exact filename appear there.
- **Licences:** content (worlds, guide, lexicon, generated PDFs) under **CC BY-SA
  4.0** (`LICENSE-CONTENT`); code (the `build/` package and tests) under **MIT**
  (`LICENSE`). Contributions are offered under the same terms.
- Because versioned filenames change on every content edit, the **README download
  block is generated** by `rebuild` between markers, not hand-maintained.
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
