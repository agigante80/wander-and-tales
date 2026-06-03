# Wits & Wonder: print presentation, a world PDF, and a full-page character sheet

**Status:** design for review, reached through a chat thread with the maintainer.
Decomposes into three implementation plans (see the end).

**Context:** The kits look good on screen but are not yet ideal for the thing they
are for, printing at home. The maintainer asked for: every PDF to be A4 as a hard
rule; a white page background so kits print cleanly and cheaply; a short world
paragraph at the start of each story; a separate, more comprehensive world PDF; and
a redesigned, full-page character sheet with room for three magics and the objects a
character carries. Kid-friendly character sheets favour clearly bordered boxes, a
portrait and name at the top, and an inventory area, which this design follows.

## Goals

1. **A4 everywhere.** Every page of every generated PDF is A4. Content, cover, the
   picture gallery, the glossary, the character sheet, and the world PDF are A4
   portrait; the map page is A4 landscape (a wide board). This is enforced in the
   renderers, not left to chance, and guarded by a test.
2. **White page background for print.** The page fill is white, not the cream tint,
   so kits print cleanly to a home printer's natural margin and use little ink. The
   coloured title banners, section headings, the dashed border, the map, and the
   illustrations stay in colour.
3. **A world paragraph at the start of each story.** Every kit opens with a front
   page that carries the story title, a short paragraph about the world (reusing the
   world's `lore_summary`), and the story cover image when one exists. This also
   gives a front page to a story that has no cover art yet.
4. **A world PDF.** A separate, more comprehensive per-world, per-locale PDF: the
   world cover, the world name and lore, the full who's-who glossary from canon
   (with portraits when art exists), and a list of the stories in that world.
5. **A full-page A4 character sheet** with a portrait and name at the top, a roomy
   magic area with three magic slots, an objects area ("What I carry") at the
   bottom, and the energy stars, filling the whole page.

## Non-goals (deferred)

- Generating the Greek world's art or a Greek map. The world paragraph, the world
  PDF, and the kits all work text-only; illustrations remain a separate, optional
  step the maintainer runs when they choose.
- Borderless ("full bleed") printing. We design for ordinary home printers with a
  white margin, which is why the background is white rather than a tint pushed to
  the edge.
- Per-world character-sheet labels (for example saying "hero quality" instead of
  "magic" in the non-magic Greek world). The sheet label stays generic; the Greek
  rules already bridge it. Revisit later if wanted.

## Part 1: print presentation (A4 hard rule and white background)

### A4 everywhere

- `build/render/pages.py` already builds A4 portrait pages; keep that, and make A4
  the only size for flowable pages (the `landscape_page` option stays only for any
  genuinely wide flowable page, currently none).
- `build/render/map.py` currently renders the map SVG at the SVG's own size. Change
  it so the map page is **A4 landscape** regardless of the source SVG's dimensions:
  render the SVG fit onto an A4 landscape page, preserving aspect (centre it, do not
  distort). A contributed map of any size then still produces an A4 landscape page.
- Add a test that builds a kit and asserts **every page** is A4, within a small
  tolerance, in one of the two orientations (210 by 297 mm portrait, or 297 by 210
  mm landscape). This makes "A4 always" a checked invariant.

### White page background

- `build/render/theme.py` `page_painter` currently fills the page with
  `theme.background` (the world's cream). Change the page fill to **white**. Keep the
  dashed border (light green) and everything coloured (banners via the `h1` style's
  `backColor`, headings, table headers, the map, the images).
- `build/render/sheets.py` currently fills the sheet background with
  `theme.background`; change that fill to white too.
- The map board keeps its own painted sky background (that is board art, not the
  page fill). The cover and scene images keep their own art. Only the page fill
  changes.
- `theme.Theme.background` stays on the model (worlds still declare a palette), but
  the printable page fill no longer uses it. A `palette[0]` is still meaningful for
  any future on-screen or tinted use; print simply ignores it.

## Part 2: the front page and the world paragraph

Today the kit's cover page renders only when the story has a cover image. Replace it
with a **front page that always renders**, built by a new helper in
`build/render/images.py` (or a small `frontpage` helper) and called first by the
kit:

- The story **title** as the `h1` banner.
- A short **world paragraph**: the world's `lore_summary[locale]`, rendered in the
  body or italic style. This is the "paragraph at the beginning of each story".
- The story **cover image** if `assets/<cover-id>.png` exists, scaled to fit the
  space left under the title and paragraph; omitted cleanly if there is no cover
  art.

So every kit, illustrated or not, opens with title plus a few sentences about the
world, and the cover art appears when it exists. The kit page order becomes: front
page, map (if any), narration, story-in-pictures (if any scenes), rules, puzzles,
idea bank, glossary, character sheet.

## Part 3: the world PDF

A new builder and CLI command produce one PDF per world per locale.

- New `build/render/world_pdf.py` with `build_world_pdf(root, world_id, locale,
  out_dir) -> Path`, reusing the existing cover, glossary, and flowable helpers.
- Contents, in order, on A4 portrait pages with the white background and the world's
  theme:
  1. **Cover**: the world name as the `h1` banner, the world cover image if it
     exists, and the world `lore_summary`.
  2. **Who's Who and What's What**: the full canon glossary
     (`glossary.glossary_flowables`) with portraits when world or story art exists.
  3. **Stories in this world**: a short list built from each `story.yaml` in the
     world, each line giving the story title (in the locale), the recommended age
     tier, and a one-line hook. The hook is the first sentence of the story's
     `narration.simple.md` opening, or a fixed fallback if absent.
- New CLI subcommand `python -m build render-world --root . --world <w> --locale
  <loc> [--out-dir <dir>]`, returning `<world>_<locale>.pdf`.
- Output name: `<world>_<locale>.pdf` (distinct from kit names, which carry a story
  and level).

## Part 4: the full-page A4 character sheet

Redesign `build/render/sheets.py` so the `young` and `older` tiers fill the whole A4
page with clearly bordered, colour-coded sections. `early` stays a large
draw-your-hero box plus a name, for the youngest children.

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
   treasures the character holds. This is present for `young` as well as `older`.
5. **Notes** (a couple of lines): `older` only.
6. **Footer**: the existing "here nobody loses" line.

New localized strings in `build/render/strings.py` (en-GB and es-ES), alongside the
existing sheet labels: `sheet_hero_type` ("I am a hero of" / "Soy un héroe de"),
`sheet_magics` ("My magics" / "Mis magias"), `sheet_magic_is` ("My magic is" / "Mi
magia es"), `sheet_magic_does` ("It can" / "Puede"), and `sheet_magic_symbol`
("draw it" / "dibújala"). Reuse the existing `sheet_title`, `sheet_name`,
`sheet_draw`, `sheet_energy`, `sheet_inventory` ("What I carry"), `sheet_notes`, and
`sheet_footer`. Drop the old single `sheet_magic` line in favour of `sheet_magics`
plus the per-slot helpers.

The sheet stays one A4 page per tier and keeps its existing test shape (each tier
renders one page; unknown tier raises; es-ES renders). The drawing uses the world's
accent colours for the section borders so the boxes are colour-coded.

A known limitation carried over: the sheet says "magic", which suits the magic
worlds; the non-magic Greek rules tell players to write their hero quality there.
Per-world sheet labels are deferred.

## Testing

- A new test asserts every page of a built kit is A4 (portrait or landscape).
- The white background is a visual change; verify by rasterising a page and
  confirming the page fill is white with the coloured elements intact.
- The front page renders for a story with no cover image (title plus world
  paragraph, no image) and for one with a cover image (title, paragraph, image), and
  the kit gains exactly one front page.
- `world_pdf.build_world_pdf` produces a valid multi-page A4 PDF for a world, with
  the glossary and the stories list present; tested against the sample repo and a
  fixture world.
- The character sheet renders one A4 page for `young` and `older` with the three
  magic rows and the "What I carry" grid; `early` still renders; es-ES renders.
- The full suite, `validate`, and `lint` stay green.

## Decomposition into implementation plans

1. **Plan 1: print presentation.** A4 hard rule (map to A4 landscape plus the
   page-size test) and the white background (painter and sheet fill). Small and
   self-contained; ship first so everything afterwards inherits it.
2. **Plan 2: front page, world paragraph, and the world PDF.** The always-on front
   page with the world paragraph, and the `render-world` command and `world_pdf.py`.
3. **Plan 3: the full-page character sheet.** The `sheets.py` redesign and the new
   strings.

After all three, rebuild the committed kits and the new world PDFs into `kits/` and
refresh the README links.

## Decisions made for the maintainer to confirm

- The world paragraph reuses the existing `lore_summary` rather than a new short
  field, for simplicity and no new authoring.
- The map page is landscape A4; everything else is portrait A4. A kit therefore
  mixes orientations, which is fine since both are A4.
- The page background is white; the cream `palette[0]` is no longer used for the
  printable page fill.
- The front page always renders (so a story with no cover art still gets a title and
  world paragraph), replacing the old cover-only-when-art behaviour.
- The character sheet has three magic slots and a six-slot "What I carry" grid; the
  generic "magic" label is kept.

## Future work (named, not built here)

- Generate the Greek world's art and a Greek map so its kit and world PDF are fully
  illustrated.
- Per-world character-sheet labels (for example "hero quality" for non-magic worlds).
- Attaching the world PDFs to GitHub Releases alongside the kits.
