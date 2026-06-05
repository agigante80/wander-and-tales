# Landscape comparison and ideas to improve Wander & Tales

This is the synthesis of the landscape scan. It compares the two corners of the
wider field, the digital tools that generate children's stories
(`digital-story-generators.md`) and the printed or purchasable story-adventure kits
and games (`printed-and-purchasable-kits.md`), against where Wander & Tales sits
today, and turns the findings (including the hands-on PDF teardowns in
`sample-teardowns.md`) into a prioritised set of improvements. These are kindred
projects, not competitors; the point is to learn what each does best and borrow it
honestly.

Wander & Tales is a free, multilingual library of printable, cooperative, adult-led
story-adventure kits for kids, played with a single die and household objects, with a
no-lose ethos. Each story ships as a Story Pack (the child-safe play material), a
Grown-up's Playbook (rules and answers), and a World Book (lore, who's who, idea
bank), in en-GB and es-ES today with it-IT next, at two reading levels (simple, rich)
across three age tiers (early, young, older).

## Where the field sits, in one table

| Dimension | Digital story generators | Printed and purchasable kits | Wander & Tales today | The opportunity |
|---|---|---|---|---|
| Access and price | Mostly freemium or subscription; credits, auto-renew, hardware stacking | One-off purchase, boxed components, or subscription; some free print-and-play | Free, downloadable PDF, no account | Keep it free and say plainly that the subscription and shipping pains do not apply |
| Personalisation | Strong: child as hero, name, family, theme, in seconds | Weak in play kits; strong in personalised printed books (Wonderbly, Hooray Heroes) | Light: name and draw your hero on the sheet | Bake "child is the hero" into the prose and sheet without a database |
| Age and reading level | Usually a vague age field or a hidden parent slider; rarely a real ladder | Best-in-class do layered same-table complexity (No Thank You, Evil!); many ship one fixed band that ages out | Two reading levels plus three age tiers plus three peril tiers | Make leveling explicit and calibrated, and playable across ages at one table |
| Cooperative and no-lose | Mostly solo consumption; co-play bolted on | A proven, sought category (Peaceable Kingdom); failure-forward narration (Amazing Tales) | Native: adult and child, nobody loses | Lead with cooperative no-lose as the headline, not a footnote |
| Output and format | Web or app read, AI audio, auto-illustration, sometimes PDF | Book, cards, board, dice, or printable PDF | A4 print-first PDFs, themed, illustrated | Sharpen print craft (layout by level, read-aloud cues, keepsake feel) |
| Languages | Wide but shallow ("74 languages" counts) | Mostly single-language, weak localisation | Deep en-GB and es-ES parity, it-IT planned | Own true multilingual parity with a consistent voice |
| Trust and safety | Hallucination risk; serious failures at the open-ended edge (AI Dungeon, character.ai) | Human-authored, safe, but variable quality | Human-authored, canon-checked, associational claims only | Turn "no AI in the child's path" into an explicit trust feature |
| Replayability | Infinite but disposable | Varies; escape boxes are low, single-use components disliked | Reusable, reprintable, idea bank for variation | Make reuse and "play it again differently" an explicit virtue |

## What each corner does best

**The digital corner** wins on instant, infinite personalisation (the child becomes
the hero in seconds), on free multimodal output (read-aloud audio and matching
illustrations bundled in), on wide language reach with one click, and, in the
education-shaped tools (Storywizard, Book Creator, WriteReader), on genuine
scaffolding: proficiency settings, progress tracking, and letting children author
rather than only consume. It also proves families will pay 20 to 40 USD for a single
personalised printed keepsake (Wonderbly, Hooray Heroes), and that none of that
requires AI. Full detail and sources in `digital-story-generators.md`.

**The printed corner** wins on no-lose cooperative play as a real, sought category
(Peaceable Kingdom built a brand on it), on failure-forward narration that keeps young
players engaged without stress (Amazing Tales: "you cling to the cliff, you do not
fall, what now?"), on read-aloud storybook immersion (Stuffed Fables, Mice and
Mystics), on layered same-table complexity for mixed ages (No Thank You, Evil!), and,
in the education corner, on explicit reading-level ladders that build parent trust
(Reading A-Z, Goosebumps Lexile bands). Print-and-play distribution is normal and
respected here. Full detail and sources in `printed-and-purchasable-kits.md`.

**The sample teardowns** show concretely how the best leveled readers shape a story by
age: level is signalled three ways at once (a named badge, a words-per-page ceiling,
and a layout shift from full-bleed art to a corner motif), the youngest levels break
text one idea per line and lean on a fixed sentence frame plus a refrain, read-aloud
cues are baked into the type (bold-caps onomatopoeia, a lone centred beat line), the
grown-up is handed both a two-minute version and the exact words to say, and the same
page template carries English and Spanish with only the text swapped. Full detail in
`sample-teardowns.md`.

## The defensible space for Wander & Tales

Almost nobody combines all of these at once: free and printable (no monetisation
traps, no screen), cooperative and no-lose, human-authored and canon-checked (no AI in
the child's path), with explicit reading-level leveling, strong guidance for non-gamer
parents, and true multilingual parity in a consistently-voiced, curated world. The
digital corner has the leveling and personalisation instincts but lives on a screen
and charges; the printed corner has the no-lose and read-aloud strengths but rarely
levels by reading age, rarely localises well, and often costs or ages out. Our space
is the honest intersection: borrow the leveling and personalisation from the digital
side and the no-lose, failure-forward, read-aloud craft from the printed side, while
keeping the things that make us different (free, offline, multilingual, no-lose,
human-authored).

## Ideas to improve the project, prioritised

Each idea names the lesson, the corner or source it comes from (full links live in the
sibling notes), and the concrete place it would land in this repo.

### Quick wins (content and small render or lint changes)

1. **Put a plain reading-level and age badge on every kit front page.** Both corners
   show that naming a concrete level builds trust (Goosebumps Lexile, Reading A-Z;
   most AI tools hide it). Add a short label such as "read-aloud (ages 3 to 5)",
   "early-reader (ages 6 to 8)", "confident reader (ages 9 to 12)" derived from the
   age tier and reading level we already tag. Lands on the Story Pack front page
   (`build/render/kit.py`, `images.frontpage_flowables`) and the catalogue
   (`build/catalog.py`); guidance in the `authoring-story-content` skill.

2. **Surface the estimated play time on the kit front.** Long runtime is the most
   common complaint in boxed narrative games; we already store `play_time_minutes`.
   Show it on the front page beside the badge so a grown-up can choose for the time
   they have. Same touch points as idea 1.

3. **Script failure-forward "yes, but" outcomes in the rules and idea bank.** Amazing
   Tales' failure-forward narration is the cleanest no-lose engine in the field, and
   it also defuses the dice-frustration complaint. Add explicit "if the roll is low,
   the story bends like this" prompts to `rules.md` and the world idea bank, and a
   rule in the `authoring-story-content` skill that every challenge names a
   bend-the-story outcome, never a dead end.

4. **Give read-aloud cues a first-class typographic role.** The teardowns show a
   bold-caps emphasis word ("GULP!") and a lone centred line marking the beat to
   pause. Add a markdown-to-PDF style for an emphasis word and for a standalone "stop
   and decide" or peril beat line, so the adult reading aloud can see where to pause
   (`build/render/markdown.py`, `theme.py`, `pages.py`).

5. **Add a "make it yours" opening to each story.** The digital magnet is "the child
   is the hero." In print we can capture it cooperatively: a short opening that invites
   the players to name their hero, choose a magic (or a hero quality in non-magic
   worlds), and pick a household object as a treasure, all of which the character sheet
   already supports. Lands in the narration opening and the `authoring-story-content`
   skill; it is a content pattern, not code.

6. **State the reuse and ink-light virtue plainly.** Destroy-it boxes (adult EXIT) are
   disliked; B&W ink-saving printables (Hero Kids) are praised, and we already print on
   a white background. Note in the README and Guide that a kit resets for free and
   prints cleanly in black and white, and consider an explicit ink-light note on the
   kit.

### Medium (content model, builders, or guide)

7. **Ship a two-minute quickstart, and print the adult's lines as ready-to-say
   prompts.** The teardowns and the best kids' RPGs hand the grown-up both a short
   version and the exact words to read. Add a two-minute quickstart box at the top of
   the Grown-up's Playbook (`build/render/playbook.py`) and format read-aloud passages
   in the narration as italic ready-to-read prompts rather than instructions.

8. **Let the layout shift by reading level.** Leveled readers move from full-bleed art
   and one-idea-per-line at the easiest level to denser text with spot art at the
   hardest. Our builders already take `reading_level`, so this is a `theme.py` and
   `pages.py` decision: larger type, shorter lines, and more illustration room for
   simple; tighter leading and denser prose for rich.

9. **Add a "scale it at the table" sidebar per story.** No Thank You, Evil!'s
   same-table layered complexity is the most praised age feature in the field. Give
   each story a short note on making it gentler for a younger child or richer for an
   older one, so mixed-age siblings can play together (one on the simple track, one on
   rich). Lands in the Playbook and the `authoring-story-content` skill.

10. **Calibrate a words-per-page budget per (age tier, reading level), and consider
    linting it.** African Storybook caps roughly 11 words per page at the easiest and
    up to about 150 at the read-aloud end. Map our `early`/`young`/`older` and
    `simple`/`rich` onto a similar ladder, document it in the authoring skill, and
    optionally add a soft check to `build/lint.py` the way it already enforces
    structure.

11. **Make the Guide for the Grown-Up carry concrete table-management moves.**
    Quarterbacking and attention-wander are documented co-op problems. Add specific
    moves to the Guide (group turns, handle impatience, soften peril live, redirect a
    dominant child, let the youngest decide first) so a non-gamer parent runs it well.

### Bigger bets (new capability or positioning)

12. **Lead the whole project on cooperative, no-lose, no-screen, no-AI-in-the-loop.**
    The loudest anxieties in the digital corner are screen time, hallucination, cost,
    and safety (AI Dungeon, character.ai). Position Wander & Tales explicitly as the
    around-the-table, human-authored, nobody-loses answer, and keep any AI we use in
    our own authoring or image pipeline behind the curtain and human-reviewed. This is
    marketing plus a discipline, not a feature to build.

13. **Own multilingual parity as the headline, not a count.** The field is either wide
    and shallow ("74 languages") or single-language. Lead with genuinely good British
    English and peninsular Spanish (and Italian next), consistently voiced across a
    curated world. This is already our direction; make it a stated promise.

14. **Add keepsake and collectable touches for free.** Families pay for a printed
    keepsake; we can give the feeling at no cost: a cover to colour, a small sticker or
    badge sheet, and a cross-kit "adventurer's passport" or binder that grows as a
    family plays more stories. Mostly content and a little render work.

15. **Offer an optional, parent-voiced read-aloud, not an app.** Audio is where print
    is genuinely weaker. Our analogue is the read-aloud script the grown-up voices
    (free, no screen). If audio is ever wanted, keep it optional and off the child's
    screen (a parent-played track or community recordings), never an AI chatbot in the
    child's hands.

## What to avoid (the field's cautionary tales)

- **Branching sprawl.** CYOA generators impress briefly but balloon. Keep the
  dice-driven, single-d6, always-finishable structure.
- **Rules creep.** Stuffed Fables shows story-age and rules-age diverging hurts. Keep
  rules featherweight so the story tier, not the mechanics, gates the age.
- **A single fixed difficulty.** It ages out in both directions. Keep the age tiers,
  peril tiers, and difficulty bands, and make them work together.
- **Win-or-lose stress and destructible components.** Both are disliked. Stay no-lose
  and reusable.
- **Shallow language breadth and AI in the child's path.** Both erode trust. Stay deep
  and human-authored.

## Honesty caveats

- Much of the digital-corner detail comes from vendor pages and app-store listings,
  which can be promotional or stale; prices and feature claims shift and are marked in
  the source note.
- The "generic plots" criticism of AI generators is a widely repeated impression, not
  a single cited verdict; treat it as such.
- The sample teardowns are a small, opportunistic set of free and legally downloadable
  PDFs (heavy on CC-licensed Pratham and African Storybook plus the Amazing Tales
  quickstart); several intended sources (Quest, Cairn, Mausritter, Hero Kids) could not
  be fetched legally or technically and are listed in `sample-teardowns.md` for a later
  pass.
- These are ideas, not commitments. Each should be weighed against the no-lose ethos,
  the associational-claims rule, and the project's deliberate simplicity before it is
  built.

## The three source notes

- `digital-story-generators.md` the digital corner, tool by tool, with feedback and
  sources.
- `printed-and-purchasable-kits.md` the printed and purchasable corner, with a priority
  section on age and reading-level handling, feedback, and sources.
- `sample-teardowns.md` close reads of real sample PDFs for concrete layout and
  reading-level lessons.
