# The create-story interview

A guided script for taking an author from "I want to make a story" to a complete
set of parameters. Ask conversationally, offer defaults, and do not overwhelm. A
confident author can answer most of this in a sentence or two; a hesitant one
should be offered choices.

## Fast path

If the author gives a one-line brief ("a gentle story about sharing for a five year
old, in the Floating Isles"), fill the rest with sensible defaults and confirm them
in one summary rather than asking every question. Only stop to ask when a choice
genuinely changes the story.

## 1. The world

Offer three branches.

### Use an existing world
List the folders under `worlds/` with each world's en-GB name and tone (read
`world.yaml`). The new story will share that world's canon, palette, font, and
peril feel. This is the easiest path and keeps the library coherent.

### Start from a suggested seed
Offer a few on-brand new worlds and let the author pick and tweak one. Each seed is
warm, has a clear look, and fits the no-lose ethos. Examples to offer:

- **A frozen island** in the Floating Isles sky: snow, ice lanterns, friendly seals,
  gentle peril, cool blues and whites.
- **A desert bazaar**: warm sand, striped awnings, talking camels and lamp spirits,
  mild peril, ochre and turquoise.
- **A deep-sea reef**: sunbeams underwater, kind octopuses and lantern fish, gentle
  peril, teal and coral.
- **A cloud kingdom**: floating staircases, wind sprites, sky whales, gentle to mild
  peril, lilac and gold.
- **A mountain village of clockwork**: cosy workshops, tin owls, a shy automaton,
  mild peril, brass and pine green.

### Create a custom world
The author describes their setting. Scaffold `world.yaml` with: `name` (en-GB and
es-ES), `tone` (a short phrase), `palette` (seven hex colours: a light background
first, then a primary and five accents), `fonts.default` (a registered family, see
`build/fontspec.py`, today `dejavu-sans` or `dejavu-serif`), `lore_summary` (a warm
paragraph per locale), and `visual_style` (one paragraph of art direction with the
palette hexes and "nothing scary"). Then create an initial `canon/` with the named
places, characters, creatures, items, and any world-flavour terms the setting needs.

## 2. The story idea

Offer three to five ideas fitted to the chosen world and audience, or take the
author's own. A good idea here is small, has two to four "stops" or beats, and
resolves through cleverness and kindness. Confirm the idea keeps the ethos: nobody
loses, no real villains beyond the world's peril, and any fearsome thing turns out
lonely or misunderstood, or is outwitted without cruelty.

## 3. The parameters

Gather these (allowed values in brackets; pick a default when the author is unsure):

- **Age tier** [`early` (3 to 5), `young` (6 to 8), `older` (9 to 12)]. Default
  `young`.
- **Reading levels** [`simple`, `rich`, or both]. Default both. `simple` serves
  `early` and `young`; `rich` serves `older`.
- **Skills** [from `build/tags.py` `SKILLS`: vocabulary, logic, maths, memory,
  spatial, observation, social-emotional]. Pick two to four that fit the puzzles.
- **Peril** [`gentle`, `mild`, `heroic`]. Match it to the world and age; default
  `gentle` for young, `heroic` only for older.
- **Players** [min and max]. Default 2 and 2 (an adult and a child).
- **Play time** [minutes]. Default 30, a little more for older.
- **Special requirements** [free text]. A theme, a learning focus, a named
  character, a length, anything the author asks for.

## 4. Confirm before authoring

Summarise the world, the idea, and the parameters in a few lines and get a yes
before you write. Then proceed to author the content (en-GB first, then every
required locale) following the authoring-story-content rules.
