---
name: authoring-story-content
description: >-
  Author or revise content for the Wits & Wonder children's story-kit library:
  story narration (simple and rich reading levels), world lore, canon registry
  entries, puzzles, idea banks, rules-page text, and the Guide for the Grown-Up,
  in British English (en-GB, canonical), Spanish from Spain (es-ES), and Italian
  (it-IT), the synced locales. Use this skill whenever you
  write, draft, translate, or edit any kid-facing or grown-up-facing prose or
  YAML content for Wits & Wonder (any world or story, including The Floating
  Isles / The Sleeping Garden and the Greek-myth world), even when the request
  only says "write the story", "draft the narration", "add a creature",
  "translate this to Spanish", or "write the grown-up guide". It encodes the
  no-lose, clever-and-kind ethos, the writing constraints (no em or en dashes),
  the associational (non-causal) claims rule, reading-level and peril-tone
  guidance, the en-GB-first then es-ES workflow, and canon-name discipline.
---

# Authoring Wits & Wonder story content

Wits & Wonder is a public, multilingual library of printable, cooperative,
adult-led story-adventure kits for kids (print-and-play PDFs played with simple
dice and household objects). The whole architecture rests on one bet: **content
is the unit of work**. Adding a world, a story, a language, or an age tier is a
writing task, not a coding task. This skill is how that writing stays consistent,
warm, and on-brand across every author, language, and session.

The wider system (architecture, conventions, and build pipeline) is described in
`CLAUDE.md` at the repository root. This skill covers how to *write the words*.

## The one thing to hold onto

Every kit teaches the same quiet lesson: **you win by being clever and kind.**
The games are cooperative (a grown-up and one or more children, together, on the same
side), and **nobody loses.** The grown-up is not a referee standing apart: they guide
the story and play along as a fellow adventurer, taking a hero of their own, helping
the children through, and letting themselves be surprised even though they have read
ahead. Write the rules and the Guide so a story works for two or more players (one
adult and one or more children), and never assume exactly two. A failed dice roll is
never a defeat; it is a detour to a different route. There
are no real villains in gentle and mild stories, and the "antagonist" usually
turns out to be lonely or misunderstood rather than wicked (in the first story it
is a sprite who only wanted a friend). Conflicts resolve through imagination,
care, and working things out together, never through force or elimination.

If a sentence you are writing would make a child feel they have failed, lost, or
been left out, rewrite it. The legacy kit's footer says it best: "here nobody
loses, you just look for another way."

This ethos is also the product's honest promise. Keep it intact in every piece,
from a puzzle hint to the world lore to the grown-up guide.

## Mechanical rules that are easy to break

These are small and unforgiving, so check them deliberately.

1. **Never use em dashes or en dashes, anywhere.** Use a hyphen only to connect
   words (`print-and-play`, `screen-free`). Do not use a hyphen as a stand-in for
   a dash. Rewrite with commas, parentheses, a colon, or two sentences. For
   number ranges write "3 to 5", not a dash. A `PreToolUse` hook blocks any file
   write that contains a dash, so this is enforced, but writing it correctly the
   first time saves a bounce.

2. **Claims about children must be associational, never causal.** This game does
   not "make kids smarter", "boost IQ", "improve grades", or "build" skills. It
   is "a way to practise" curiosity, imagination, problem-solving, and teamwork;
   shared screen-free time is "associated with" or "linked to" good outcomes, not
   a cause of them. Keep verbs soft: *practise, nurture, exercise, a chance to*,
   not *builds, boosts, increases, improves*. This rule comes straight from the
   evidence base; see `research/evidence-base/marketing-paragraph.md` for the exact
   phrasings that are cleared and the list of claims never to make. It governs all
   grown-up-facing copy (world intros, the Guide, any positioning text).

3. **Write British English (en-GB), Spanish from Spain (es-ES), and Italian
   (it-IT).** These are the synced locales, and they are specific: British spelling
   and idiom (colour, organise, maths, autumn, "have you got"); peninsular Spanish
   with "vosotros" for the players and full, correct accents; and natural Italian
   with "voi" for the players and full accents (the old font limit that dropped
   accents is gone). US English, Latin American Spanish, and other languages are
   **separate languages** that slot in later, each in its own content files, exactly
   like European versus Brazilian Portuguese, or French and German. Never quietly mix
   an Americanism into en-GB, a Latin American turn of phrase into es-ES, or a
   non-native turn into it-IT. See `references/voice-and-reading-levels.md`.

## Content types and where they live

| File | Audience | Reading level | Notes |
|---|---|---|---|
| `content/<locale>/narration.simple.md` | kid (read aloud by adult) | simple | covers `early` + `young` |
| `content/<locale>/narration.rich.md` | kid (read aloud or self) | rich | covers `older` |
| `content/<locale>/rules.md` | adult GM | adult | difficulty bands, the no-lose golden rule, the newcomer callout |
| `content/<locale>/puzzles.md` | adult GM | adult | the challenges and their solutions |
| `worlds/<world>/content/<locale>/idea-bank.md` | adult GM | adult | world-level improv prompts; one per world, shared by its stories |
| `worlds/<world>/world.yaml` | adult | adult | world name per language, tone, palette, lore summary |
| `worlds/<world>/canon/*.yaml` | system | both | the name registry (see below) |
| `worlds/<world>/heroes.yaml` | adult | both | four example heroes (2 young, 2 older) for the sample adventure sheets |
| `guide/<locale>/guide.md` | adult GM | adult | the generic Guide for the Grown-Up |
| `story.yaml` | system | n/a | tags and metadata only |

`<locale>` is always an explicit code: `en-GB` (canonical) and `es-ES` today, with
others like `en-US` or `es-419` added later as their own folders. The same codes
key the `title:` map in `story.yaml` and the `names:` map in canon.

Glossary appendices, map labels, and the catalog are **generated from canon**, so
you do not hand-write them; you keep canon correct and they follow.

The idea bank is world-level (one per world per locale), not per story; the narration,
rules, and puzzles remain per story. Version numbers, the colophon, and the licence are
added automatically at build time, so you never edit them.

## The authoring workflow

Follow this order. It is what keeps names consistent and translations faithful.

1. **Canon first.** Before naming any place, character, creature, item, or
   special term, check the world's `canon/` files and the repo-wide
   `lexicon/terms.yaml`. Use the canonical name for the language you are writing.
   If you are introducing something genuinely new, add a canon entry for it (see
   `references/canon-and-content-types.md`) before using it in prose. The point:
   prose follows canon, and a lightweight lint will flag any name in the text
   that is not in canon, or any case where EN and ES disagree for the same id.

2. **British English is canonical. Draft en-GB first.** It is the source of truth
   and the version a human reviews. Get it right before translating.

3. **European Spanish is synced, not literal.** Translate for a Spanish (Spain)
   child's ear, not word for word. Match meaning, warmth, and rhythm; use correct
   accents and the canon Spanish names. See
   `references/voice-and-reading-levels.md` for es-ES register and worked
   examples.

4. **Write to pass lint clean.** No name outside canon, no EN/ES name mismatch.
   When in doubt, fix canon, not the prose.

More locales slot in later the same way (canonical en-GB, then the new locale,
whether en-US, es-419, pt-PT, French, or German), with no code changes. Write so
that is true.

## Reading levels in one breath

Two narration levels per language. **simple** (for ages 3 to 8): short sentences,
concrete words, present-tense action, strong sensory hooks, easy to read aloud,
few subordinate clauses. **rich** (for ages 9 to 12): longer sentences, a wider
vocabulary, a little more interiority and suspense, while staying warm and clear.
Both tell the same story with the same beats; only the language grows up.

For detailed guidance, contrasts, and EN plus ES examples, read
`references/voice-and-reading-levels.md`.

## Peril and tone

A story's `peril` tag sets how much tension is allowed.

- **gentle**: nobody is hurt, no villains. Cozy and reassuring. The obstacle is a
  puzzle or a sad creature who needs help. (The Sleeping Garden is gentle.)
- **mild**: real obstacles and suspense, but nobody dies and no one is cruel. A
  bit more edge, still safe.
- **heroic**: higher stakes for an older audience; foes can be outwitted or
  "fall". The cooperative, no-elimination engine stays underneath, and cleverness
  and kindness still win. The Greek-myth world uses a non-magic framing (wits and
  courage rather than the four magics), and even a fearsome foe can be befriended
  rather than slain where the story allows.

Match vocabulary and intensity to the peril and the age tier. Heroic is braver,
not grim or violent.

## Talking about dice and difficulty

Rules and narration **never name a specific die.** They use difficulty bands:
**Easy, Normal, Hard.** A single reference table in each kit maps the bands onto
whatever dice a family owns, and every story must be playable with a single d6.
Write "this is a Normal challenge", not "roll a d20". The help mechanic and the
surprise table scale the same way. This keeps one story playable with any dice
set and avoids multiplying the build.

## Quality checklist before you call a piece done

- No em or en dashes; ranges written as "3 to 5".
- Nobody loses; failure reads as a detour, not a defeat.
- Every named thing exists in canon with matching EN and ES names.
- Any claim about children is associational, never causal.
- Reading level matches the file (simple vs rich) and the age tier.
- Tone matches the story's peril tag.
- Difficulty is expressed in bands, not specific dice.
- Spanish reads naturally to a native child and uses correct accents.
- Read narration aloud once: it should sound good in a grown-up's voice.

## Images and art prompts

When authoring a world, write its `visual_style` (one paragraph of art direction:
medium, mood, the world palette hexes, "nothing scary") and any world-level images
(a cover, key portraits). When authoring a story, write its `images`: a cover and a
scene per major beat or stop.

Rules for every image:

- The `prompt` is the subject only, in English, locale-neutral. The world's
  `visual_style` and a technical line are added automatically at export, so do not
  repeat the style in each prompt.
- The art must contain no text, letters, words, or numbers (so one image serves
  every language, like the maps). Never ask for captions or titles in the image.
- Keep it gentle and on-palette, in the no-lose, clever-and-kind spirit: nothing
  frightening, no real violence, friendly faces.
- Set `canon_ref` to the canon id when an image depicts a named place, character,
  or creature, so the export adds that entry's description and the art stays
  consistent with the bible.
- Write `alt` text in en-GB first, then es-ES, like all other prose, following the
  en-GB and es-ES conventions (British spelling, peninsular Spanish with accents).

## Reference files

- `references/voice-and-reading-levels.md`: simple vs rich with worked EN and ES
  examples, plus Spanish register and how to avoid translationese.
- `references/canon-and-content-types.md`: the canon entry shape, when to add an
  entry, what belongs in each content file, and the Guide for the Grown-Up
  contents checklist.
