---
name: authoring-story-content
description: >-
  Author or revise content for the Wander & Tales children's story-kit library:
  story narration (simple and rich reading levels), world lore, canon registry
  entries, puzzles, idea banks, rules-page text, and the Guide for the Grown-Up,
  in British English (en-GB, canonical) and the synced locales kept in step with it
  (defined in build/locales.py REQUIRED_LOCALES; currently Spanish from Spain es-ES,
  Italian it-IT, and European Portuguese pt-PT). Use this skill whenever you
  write, draft, translate, or edit any kid-facing or grown-up-facing prose or
  YAML content for Wander & Tales (any world or story, including The Floating
  Isles / The Sleeping Garden and the Greek-myth world), even when the request
  only says "write the story", "draft the narration", "add a creature",
  "translate this to Spanish", or "write the grown-up guide". It encodes the
  no-lose, kind-and-imaginative ethos, the writing constraints (no em or en dashes),
  the associational (non-causal) claims rule, reading-level and peril-tone
  guidance, the en-GB-first then es-ES workflow, and canon-name discipline.
---

# Authoring Wander & Tales story content

Wander & Tales is a public, multilingual library of printable, cooperative,
adult-led story-adventure kits for kids (print-and-play PDFs played with simple
dice and household objects). The whole architecture rests on one bet: **content
is the unit of work**. Adding a world, a story, a language, or an age tier is a
writing task, not a coding task. This skill is how that writing stays consistent,
warm, and on-brand across every author, language, and session.

The wider system (architecture, conventions, and build pipeline) is described in
`CLAUDE.md` at the repository root. This skill covers how to *write the words*.

## The one thing to hold onto

Every kit teaches the same quiet lesson: **there are no wrong answers, and you win by being kind and full of ideas.**
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

3. **Write every locale in `build/locales.py` `REQUIRED_LOCALES`** (read that file
   for the live set; the project gains languages over time). Each is a specific
   locale with its own register:
   - **British English (en-GB)**, canonical: British spelling and idiom (colour,
     organise, maths, autumn, "have you got").
   - **Spanish from Spain (es-ES)**: peninsular Spanish, "vosotros" for the players,
     full correct accents. Never Latin American Spanish.
   - **Italian (it-IT)**: natural, warm Italian, "voi" for the players, full accents.
   - **European Portuguese (pt-PT)**: natural Portugal Portuguese, "vocês" for the
     players (and "tu" when a prompt speaks to one child), full accents. Never
     Brazilian Portuguese. The two traps a non-native writer falls into are the
     archaic **"vós" register** (use "vocês" with 3rd person plural verbs: "Leiam",
     "São", "fizeram", never "Lede", "Sois", "fizestes") and Brazilian **gerunds**
     (use "a + infinitivo": "está a dormir", never "está dormindo"). For pt-PT,
     follow the **`pt-pt-quality`** skill, which holds the full register guide and a
     scanner; run it whenever you write or review Portuguese.
   US English, Latin American Spanish, Brazilian Portuguese, and other languages are
   **separate languages** that slot in later, each in its own content files, exactly
   like European versus Brazilian Portuguese, or French and German. Never quietly mix
   an Americanism into en-GB, a Latin American turn of phrase into es-ES, a non-native
   turn into it-IT, or a Brazilianism into pt-PT. See
   `references/voice-and-reading-levels.md`. Adding a new language to the project is
   the **`add-language`** skill, which also extends this register list.

4. **Use plain, everyday words a parent can relay to a child, especially when
   describing the game itself.** A grown-up reads the description and then has to
   explain it to their child in the moment; if the wording is elaborate, the parent is
   left hunting for the right words. So describe the game in words a six-year-old would
   understand. Avoid jargon and abstract labels, even correct ones: do not call it
   "cooperative" (say "you play together, on the same side"), a "narrator" (say "you
   read the story aloud"), or a "puzzle" where "a little challenge" works. Lead with
   the fun and what you actually do, not the category. This governs the Guide, the
   one-page How to Play, world intros, and any copy a parent reads aloud or paraphrases.

5. **Refer to children and players inclusively, never defaulting to the masculine.**
   When you mean kids in general (not a specific named character), use gender-neutral
   or inclusive wording. In en-GB this is easy: "a child", "the children", "they/them",
   "a grown-up and a child"; avoid defaulting to "he", "boy", or "his". The synced
   locales have grammatical gender, so each one's quality guide gives the natural
   inclusive form to use (es-ES "peque/peques" or "niña y niño"; pt-PT "criança", which
   is already neutral; it-IT "bambina e bambino" or a recast). Follow it. A named
   character of course keeps their own gender; this rule is only about generic
   references. Use only each language's accepted inclusive forms, never non-standard
   spellings ("niñe/niñx", the schwa "bambinə", "l@s").

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

`<locale>` is always an explicit code: `en-GB` (canonical) plus the rest of
`REQUIRED_LOCALES` (today `es-ES`, `it-IT`, `pt-PT`), with others like `en-US` or
`es-419` added later as their own folders. The same codes key the `title:` map in
`story.yaml` and the `names:` map in canon.

Glossary appendices, hand-drawn map labels, and the catalog are **generated from
canon**, so you do not hand-write them; you keep canon correct and they follow.

Every story also gets a **generated trail map** when it has no hand-drawn one: the
build reads your `## Stop N: Name` headings (and the ending heading) and draws a
START, the numbered stops, and a GOAL on a winding path, in each language straight
from your headings. So the stop headings are not just structure: they become the map's
waypoint labels. Name each stop after the **place or landmark** it happens at (`The
Vine Gate`, `The Foggy Square`, `Milo's Kitchen`), short enough to sit beside a marker
(about two to four words), and give the final `##` an ending that names where the
journey lands. There is nothing extra to author: a good set of stop names is a good
map. An author may later drop in a bespoke `assets/map.svg` to override the generated
one, but it is never required.

The stop headings are load-bearing in one more place: the **website reader** pairs each
stop's grown-up solution to its question by matching the `## Stop N: Name` heading in
`puzzles.md` to the same heading in the narration, and it shows each stop's scene image
inline. So keep the headings identical between `narration.simple.md`,
`narration.rich.md`, and `puzzles.md` (the puzzles file may add a band suffix like
`(Easy)`, which is fine), and order the `images:` so the scenes follow the stops (a
cover, then one scene per stop, then the ending). Matching headings keep the printed
kit and the website in step.

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
  "fall". The cooperative, no-elimination engine stays underneath, and good ideas
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
- Stop headings name a place or landmark and are short: they become the map's labels.
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
- Keep it gentle and on-palette, in the no-lose, kind-and-imaginative spirit: nothing
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
