# Canon discipline and content types

This file covers two practical things: how the name registry (canon) works and
when to add to it, and what belongs in each content file you might be asked to
write.

## Canon: the name registry

Two layers keep names consistent across stories and languages:

- **`lexicon/terms.yaml` (repo-wide):** system vocabulary shared by every world,
  such as "Game Master", the difficulty band names (Easy, Normal, Hard), dice
  names, and "energy star". Use these exact terms everywhere.
- **`worlds/<world>/canon/*.yaml` (per world):** the world bible, split into
  `places.yaml`, `characters.yaml`, `creatures.yaml`, `items.yaml`, and
  `terms.yaml` (world-flavour vocabulary, such as the four magics of the Floating
  Isles). Each file stays small and focused.

### Why this matters

Canon is the **source of truth for names**. Authors and translators write natural
prose by hand, but the names in that prose must come from canon. A lightweight
lint warns when a name in the text is not in canon, or when English and Spanish
disagree for the same id. Structured outputs (the per-kit glossary appendix, map
labels, the idea bank, the catalog) generate directly from canon, so they can
never contradict it. Keep canon correct and these follow for free.

### Entry shape

```yaml
# worlds/floating-isles/canon/creatures.yaml
- id: mist-cat              # stable, language-neutral key (kebab-case)
  names:
    en-GB: Mist Cat
    es-ES: Gato de Niebla
  kind: creature            # place | character | creature | item | term
  disposition: friendly     # optional, where it helps
  description:
    en-GB: A gentle cat made of fog who gives hints.
    es-ES: Un gato amable hecho de niebla que da pistas.
  first_seen: sleeping-garden
```

### When to add an entry

Add a canon entry **before** you use a new named thing in prose, whenever you
introduce a place, character, creature, item, or special term that a reader could
reasonably expect to be named consistently later. Give it a stable kebab-case
`id`, both language names, a `kind`, a short bilingual `description`, and the
`first_seen` story id.

You do **not** need a canon entry for ordinary scenery (a passing butterfly, a
generic flower) that carries no proper name and will not recur. Canon is for the
named, reusable furniture of a world, not every noun.

If a name already in canon reads awkwardly in a sentence, change the canon entry
(and anything generated from it), rather than quietly using a different name in
the prose. Consistency beats a one-off nicer phrasing.

## What belongs in each content file

### narration.simple.md / narration.rich.md

The story as the grown-up tells it, scene by scene, following the map's stops.
Two reading levels, same beats. See `voice-and-reading-levels.md`. Narration sets
the scene and hands moments to the child; it does not spell out puzzle solutions
(those live in puzzles.md, for the adult's eyes).

### rules.md

The adult-facing rules page for this story. Includes: setup, the difficulty
**bands** (never specific dice; the kit's reference table maps bands to dice),
the **golden rule that nobody loses** (a failed roll means spend a star to retry
or combine abilities, never a defeat), the help mechanic, the surprise table, and
the **newcomer callout**: a small note pointing first-time grown-ups to the Guide
for the Grown-Up. Keep it scannable; an adult reads this once before play.

### puzzles.md

The challenges and their solutions, for the adult GM. Each puzzle states its
difficulty band, what the players need to figure out or do, and the intended
solution, plus gentle fallbacks so a stuck child still moves forward. Remember
that more than one approach should work; reward good ideas and kindness.

### idea-bank.md

Improv fuel for the adult: lists of powers, items, friendly creatures, magical
places, mini-challenges, and happy rewards they can pull from when a child goes
off-script. Much of this is drawn from or consistent with canon. This is the
single best defence against a session stalling, so keep it generous and playful.

### world.yaml

The world's name per language, its tone, its colour palette, and a short lore
summary. This is metadata plus a paragraph or two of setting, not a story.

## The Guide for the Grown-Up (`guide/<locale>/guide.md`)

A generic, system-wide guide (shared across all worlds, not per world) for an
adult who may never have played a tabletop role-playing game. It is adult-facing,
so it has a single reading level. It ships as a standalone "Start Here" PDF per
language, and each kit's rules page points to it.

Aim for about one to two pages, covering:

- What this kind of game is, and that no experience is needed.
- The grown-up's three jobs: narrator, gentle referee, biggest fan.
- The golden rule "Yes, and": never just say no; build on the child's idea.
- Handling impossible or silly answers, with ready-to-use scripts.
- Captivating young kids: do voices, hand them the dice, offer choices, keep
  scenes short, follow their excitement, take breaks.
- Helping when they are stuck: a friendly hint, lower the difficulty, combine
  abilities, or simply let them succeed.
- The no-lose ethos: turn a failed roll into a fun detour, not a defeat.
- Pacing and length: stop early, skip a puzzle, play across several sittings.
- A handful of ready-to-use phrases.

Keep the claims rule in mind here especially: this is grown-up-facing copy, so any
mention of benefits to children stays associational and soft (a chance to
practise curiosity and teamwork, screen-free time together), never a promise that
the game makes a child smarter. See `research/evidence-base/marketing-paragraph.md`.
