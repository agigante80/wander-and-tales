# Design: A multilingual, multi-world printable story-kit library

Date: 2026-06-01
Status: Draft for review

## 1. Summary

**Project name: Wits & Wonder** (repo slug `wits-and-wonder`).

Turn the existing single Spanish print-and-play kit ("El Jardin Dormido") into a
public, multilingual **library** of printable, cooperative, adult-led story kits
for kids. Content lives as data (text files plus metadata); a layout-only build
renders printable PDFs per language and per reading level. Adding a new world,
story, language, or age tier is a content task, not a coding task.

English is the primary (canonical) language; Spanish is kept in sync. The design
is built so more languages slot in later with no code changes.

## 2. Goals and non-goals

### Goals
- Publish publicly so anyone can download and play (free, print-and-play).
- English-first, Spanish second, structured for more languages later.
- Multiple worlds, each holding multiple stories, with consistent names and lore.
- Per-story tags so a parent can pick the right adventure at a glance.
- Playable with as little as a single d6, or with a richer dice set.
- Age-appropriate character sheets and reading levels.
- A canonical name registry per world so translations and future stories stay
  consistent.

### Non-goals (deliberately deferred, YAGNI)
- A digital / web / mobile version of the game.
- Space and Japanese-mythology worlds (the schema must allow them; we do not
  build them now).
- A marketing landing page.
- Printable creature cards, sticker/reward sheets, physical puzzle cards.
- Additional stories beyond the two authored in this effort.

## 3. Key decisions (resolved during brainstorming)

| Topic | Decision |
|---|---|
| Project name | "Wits & Wonder" (repo slug `wits-and-wonder`). |
| Medium | Stays a printable PDF kit (not digital). |
| Distribution | Public GitHub repo; PDFs via GitHub Releases. |
| Primary language | English (canonical). Spanish kept in sync. |
| Translation workflow | Claude drafts EN; user reviews. EN is source of truth. |
| Scope of this effort | Build the full system + migrate the Garden story + author one new Greek-myth story. |
| First story name | "The Sleeping Garden" / "El Jardin Dormido". |
| Home world | "The Floating Isles" / "Las Islas Flotantes". |
| Second world | Greek mythology (heroic peril, older tier, non-magic ruleset). |
| Architecture | Content files + language-agnostic layout-only builders. |
| Dice | Abstract difficulty bands mapped to whatever dice a family owns; 1d6 always works. |
| Age model | 3 age-tiered character sheets + a difficulty dial + 2 narration reading levels per language. |
| Newcomer guide | A generic "Guide for the Grown-Up" for first-time game masters: standalone PDF per language, with a small callout in each kit. |
| Name registry | Per-world canon files + a repo-wide shared lexicon; "authoritative + lint" binding. |
| Fonts | Embed a Unicode font (e.g. DejaVu Sans) so accents render; swappable per language. |

## 4. World model

The content hierarchy is `world -> story`, with cross-cutting tags.

- A **world** is a setting with shared tone, lore, look, and a canonical name
  registry. It holds many stories.
- A **story** is one self-contained adventure inside a world.

### The Floating Isles (home world)
Islands adrift in the sky, in a realm where magic only ever helps (it grows,
heals, transforms, and speaks; it never harms). On the **home island**, the
**House of the Little Mages** (the school) sits at the highest point, and the
**city where the families live** spreads below it. The **Great Garden** is within
the school grounds.

This shape gives every future adventure a natural home: another floating island
of a different type (stormy, frozen, jungle), or the open sky and landscape
between islands. Those are locations within future stories, not separate worlds.

- Story 1: **The Sleeping Garden**, set in the school-grounds garden. Migrated
  from the existing content. Peril: `gentle` (nobody is hurt, no real villains;
  the "antagonist" is a lonely sprite who only wanted company).

### Greek mythology (second world)
A separate world in the schema, authored now to stress-test it against a higher
peril level, an older audience, a vocabulary/logic puzzle mix, and a non-magic
ruleset. One short adventure, peril `heroic` (foes can be outwitted or "fall",
but the cooperative, no-player-elimination engine stays underneath).

## 5. Repository layout

```
lexicon/                         # repo-wide game vocabulary shared by all worlds
  terms.yaml                     # "Game Master", difficulty band names, dice names, "energy star"...

guide/                           # generic "Guide for the Grown-Up" (newcomer GM guide)
  en/guide.md                    # adult-facing, single reading level, localized
  es/guide.md

worlds/
  floating-isles/
    world.yaml                   # world name (per lang), tone, palette, lore summary
    canon/                       # the world bible / name registry (see section 9)
      places.yaml
      characters.yaml
      creatures.yaml
      items.yaml
      terms.yaml                 # world-flavor vocabulary (e.g. the four magics)
    assets/                      # shared art (map base SVG, icons)
    stories/
      sleeping-garden/
        story.yaml               # tags / metadata (see section 6)
        content/
          en/
            narration.simple.md
            narration.rich.md
            rules.md
            puzzles.md
            idea-bank.md
          es/
            (same set, Spanish)
  greek-myth/
    world.yaml
    canon/ ...
    assets/
    stories/
      <first-greek-story>/
        story.yaml
        content/en/... es/...

templates/                       # layout templates
  character-sheet.early.*
  character-sheet.young.*
  character-sheet.older.*
  rules-page.*
  dice-band-table.*

build/                           # language-agnostic Python builders (layout only)
catalog.md                       # generated index of all stories with their tags
dist/                            # built PDFs (also attached to GitHub Releases)
docs/superpowers/specs/          # this spec and future ones
```

## 6. Story metadata schema (`story.yaml`)

```yaml
world: floating-isles
id: sleeping-garden
title:
  en: The Sleeping Garden
  es: El Jardin Dormido
age:
  recommended: young        # one of: early (3-5), young (6-8), older (9-12)
  also_works_for: [early, older]
skills:                     # multi-select
  - vocabulary
  - logic
  - social-emotional
peril: gentle               # gentle | mild | heroic
adult_gm: true              # always shown as a prominent badge; kept as a tag
dice:
  minimum: 1d6              # the floor; every story must be playable with one d6
  recommended: d20-set      # optional richer set the story is tuned for
players:
  min: 2
  max: 2
play_time_minutes: 30
```

`catalog.md` is generated from every `story.yaml`, giving parents a filterable
table (world, title, age, skills, peril, dice, players, time).

### Tag vocabularies
- **age tiers**: `early` (3-5), `young` (6-8), `older` (9-12).
- **skills**: `vocabulary`, `logic`, `maths`, `memory`, `spatial`,
  `observation`, `social-emotional`.
- **peril**: `gentle` (nobody hurt, no villains), `mild` (tension/obstacles,
  nobody dies), `heroic` (foes can be defeated or "fall").

## 7. Dice and rules engine

Rules never name a specific die. They use **difficulty bands**: Easy, Normal,
Hard. A single reference table in each kit maps the bands onto whatever dice a
family owns. Examples:

| Band | 1d6 only | d20 set (current) |
|---|---|---|
| Easy | 3+ | 6+ |
| Normal | 4+ | 10+ |
| Hard | 5+ | 14+ |

- The **help mechanic** and the **surprise table** scale the same way (a 6-row
  surprise table for d6, a 10-row table for d10).
- Dice flexibility is therefore a single in-document table, not a separate build
  per dice type, so it does not multiply output.
- The Greek world may use the same band system with a non-magic framing (skill
  checks, wits, courage) instead of "magic numbers".

## 8. Age and reading levels

- **Character sheets**: three age-tiered templates.
  - `early`: mostly pictures, minimal writing.
  - `young`: light writing, simple fields.
  - `older`: stats, inventory, notes.
- **Difficulty dial**: each story declares a default band; the adult GM can step
  it up or down.
- **Narration**: two reading levels per language, `simple` (covers early +
  young) and `rich` (older). So per story per language the build renders a simple
  kit and a rich kit.

This keeps the output matrix bounded: per story we render
`languages x reading-levels` narration kits, plus the three character-sheet
templates; dice and difficulty are in-document, not build axes.

## 9. Canon registry and shared lexicon

Two layers keep names consistent across stories and languages:

- **`lexicon/` (repo-wide)**: system vocabulary shared by every world (e.g.
  "Game Master", "Easy/Normal/Hard", dice names, "energy star").
- **`worlds/<world>/canon/` (per world)**: the world bible, split by category
  (`places`, `characters`, `creatures`, `items`, `terms`) so each file stays
  small and focused.

### Entry shape

```yaml
# worlds/floating-isles/canon/creatures.yaml
- id: mist-cat              # stable, language-neutral key
  names:
    en: Mist Cat
    es: Gato de Niebla
  kind: creature
  disposition: friendly
  description:
    en: A gentle cat made of fog who gives hints.
    es: Un gato amable hecho de niebla que da pistas.
  first_seen: sleeping-garden
```

### Binding: "authoritative + lint"
- Canon is the source of truth for names.
- Authors and translators write natural prose by hand but follow canon names.
- A lightweight **lint** check warns when a name used in story text is not in
  canon, or when EN and ES use inconsistent names for the same `id`.
- **Structured outputs generate directly from canon**: the per-kit **glossary
  appendix** ("who's who / what's what"), map labels, the idea bank, and the
  catalog. These can never disagree with canon.

## 10. Guide for the Grown-Up (for first-time game masters)

A system-wide, generic guide for the adult running the game, written for people
who may never have played a tabletop role-playing game. It is the single best
safeguard against a session stalling when a child goes off-script.

- **Scope**: generic and shared across all worlds (not per world). Lives at
  `guide/<lang>/guide.md`, localized like everything else (EN canonical, ES
  synced). It is adult-facing, so it has a single reading level (no simple/rich
  split).
- **Delivery**: a standalone "Start Here" PDF per language (for example
  `Guide_for_the_Grown-Up_EN.pdf`). Each kit's rules page carries a small callout
  ("New to this? Read the Guide for the Grown-Up first") rather than reprinting
  the whole guide in every kit.
- **Contents** (about one to two pages): what this kind of game is and that no
  experience is needed; the grown-up's three jobs (narrator, gentle referee,
  biggest fan); the golden rule "Yes, and" (never just say no); handling
  impossible or silly answers with ready scripts; captivating young kids (do
  voices, hand them the dice, offer choices, keep scenes short, follow their
  excitement, take breaks); helping when they are stuck (a friendly hint, lower
  the difficulty, combine magic, or let them succeed); the no-lose ethos (turn a
  failed roll into a fun detour, not a defeat); pacing and length (stop early,
  skip a puzzle, play across several sittings); and a handful of ready-to-use
  phrases.
- **Optional per-world note (deferred, YAGNI)**: `world.yaml` may later carry a
  short optional "grown-up note" for tone differences (for example, reassuring
  kids during scarier Greek moments). Not built now.

## 11. Build pipeline and i18n

- Builders are **layout-only** and take `(world, story, language, reading_level)`.
  They load the relevant content files plus canon and render the kit PDF to
  `dist/`. The current hardcoded `/mnt/user-data/outputs/` paths are removed.
- Toolchain stays the proven one: `reportlab` for layout, `cairosvg` for the
  SVG map, `pypdf` to merge pages into one printable kit.
- **Embed a Unicode font** (e.g. DejaVu Sans) so Spanish accents and future
  scripts render correctly. The current kit avoids accents due to font limits;
  this fixes that. The font is selectable per language, so a future
  Japanese world can plug in a CJK font without touching layout code.
- A per-kit build produces: the story narration kit (map + rules + narration +
  puzzles + glossary), and the relevant character sheets. The rules page includes
  the newcomer callout pointing to the Guide for the Grown-Up.
- The build also renders the standalone **Guide for the Grown-Up** PDF per
  language from `guide/<lang>/guide.md`.
- **Optional, recommended**: a GitHub Action that builds all kits on release and
  attaches the PDFs to the GitHub Release.

## 12. What we author in this effort

1. **System**: schema, tag vocabularies, dice bands, age-tiered sheet templates,
   canon/lexicon structure, lint, layout-only builders, catalog generation,
   Unicode font embedding.
2. **The Floating Isles / The Sleeping Garden**: world lore rewritten for the
   floating-island setting; existing adventure migrated into the schema; EN
   drafted by Claude for review; ES restored from existing text with accents;
   simple + rich narration; canon populated; three character sheets.
3. **Greek myth / one new story**: world lore, one short heroic-peril adventure,
   canon populated, EN drafted then ES, simple + rich narration.
4. **Guide for the Grown-Up**: draft the generic newcomer guide content (EN
   canonical, then ES), wire its standalone PDF build, and add the rules-page
   callout that points to it.

## 13. Testing and verification

- **Lint**: canon coverage and EN/ES name consistency pass with no warnings for
  the authored stories.
- **Build**: every authored `(story, language, reading_level)` combination builds
  a PDF without error, output lands in `dist/`.
- **Guide**: the standalone Guide for the Grown-Up builds for each language, and
  the newcomer callout appears on the rules page of each kit.
- **Visual check**: rasterize each built PDF to PNG and eyeball it (accents
  render, layout intact, map merges correctly) before declaring done.
- **Catalog**: `catalog.md` regenerates from `story.yaml` files and lists both
  stories with correct tags.

## 14. Open items (to settle during spec review or implementation)

- **Which Greek myth** the first Greek adventure draws on. Proposed kid-friendly
  seed: a gentle Labyrinth tale where the heroes use Ariadne's thread as a logic
  puzzle and **befriend** rather than slay the Minotaur, keeping the cooperative
  "win by being clever and kind" engine while the `heroic` tag covers the higher
  stakes.
- **Final reading-level mapping** confirmation (simple = early+young, rich =
  older) once we see the first migrated text.
