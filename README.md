# Wits & Wonder

A free, multilingual library of printable, cooperative story-adventure kits for a
grown-up and a child to play together. You print a kit, grab a die and a few
household bits, and share a gentle story-and-puzzle adventure. There is no app and
no screen. **Nobody competes, and nobody loses:** you win by being clever and kind.

Every kit comes ready to play in British English and in Spanish from Spain, at two
reading levels. It is a lovely excuse for unhurried, screen-free time together, and
a way to practise imagination, problem-solving, and teamwork. Adding a world, a
story, or a language is a writing task, not a coding task.

## Download a kit

Each kit is a single printable PDF. The **Simple** version reads aloud well for
ages 3 to 8; the **Rich** version suits ages 9 to 12. Click a link to view or
download.

| Story | World | Ages | English | Español |
|---|---|---|---|---|
| The Sleeping Garden | The Floating Isles | 6 to 8 | [Simple](kits/floating-isles_sleeping-garden_en-GB_simple.pdf) · [Rich](kits/floating-isles_sleeping-garden_en-GB_rich.pdf) | [Sencillo](kits/floating-isles_sleeping-garden_es-ES_simple.pdf) · [Completo](kits/floating-isles_sleeping-garden_es-ES_rich.pdf) |
| The Singing Spring | The Sunlit Hills of Greece | 9 to 12 | [Simple](kits/greek-myth_the-singing-spring_en-GB_simple.pdf) · [Rich](kits/greek-myth_the-singing-spring_en-GB_rich.pdf) | [Sencillo](kits/greek-myth_the-singing-spring_es-ES_simple.pdf) · [Completo](kits/greek-myth_the-singing-spring_es-ES_rich.pdf) |

**New to running a game like this?** Read the one-page **Guide for the Grown-Up**
first: [English](kits/Guide_for_the_Grown-Up_en-GB.pdf) ·
[Español](kits/Guide_for_the_Grown-Up_es-ES.pdf). It explains everything in about
five minutes.

The full, filterable list of stories and their tags lives in
[`catalog.md`](catalog.md).

## How to run this project

You only need the toolchain if you want to build the PDFs yourself or add your own
content. Players just download a kit above.

### Requirements

- Python 3.11 or newer.
- A Cairo system library for the SVG maps (on Debian or Ubuntu this is `libcairo2`,
  which is usually already installed).

### Set up

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,render]"
```

The core install needs only `pydantic` and `PyYAML`. The `render` extra adds
`reportlab`, `cairosvg`, and `pypdf` for the PDF build. A further `images` extra
(`pip install -e ".[images]"`) adds `openai` and `python-dotenv` for generating the
illustration art from prompts; put your key in a local `.env` (see `.env.example`).

### Everyday commands

```bash
python -m pytest                              # run the test suite

python -m build validate --root .             # load and validate all content
python -m build lint --root .                 # structural lint (exit 1 on error)
python -m build catalog --root . --out catalog.md   # regenerate the catalogue

# build one printable kit into dist/
python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple

python -m build render-guide --root . --locale en-GB   # build the Guide PDF
python -m build prompts --root .                       # export the image prompts
python -m build generate-images --root .               # generate art (needs OPENAI_API_KEY)
```

### Where things live

- `worlds/<world>/` is a world: its `world.yaml`, a `canon/` name registry, an
  `assets/` folder for the map and art, and `stories/<story>/` with tags and the
  per-locale prose.
- `guide/<locale>/guide.md` is the generic Guide for the Grown-Up.
- `build/` is the importable toolchain: the content model and validation, and the
  layout-only PDF renderer in `build/render/`.
- `kits/` holds the built PDFs linked above. `dist/` is the scratch build output and
  is not tracked.
- `docs/superpowers/specs/` and `docs/superpowers/plans/` hold the design specs and
  implementation plans.

## Contributing a story

This library grows through contributions, and adding a world or a story is a writing
task, not a coding task.

The easiest way is the **`create-story` skill** in Claude Code: ask to "create a
story" and it guides you through choosing or creating a world, picking or writing an
idea, setting the audience and challenges, writing the content in British English and
Spanish from Spain, validating it, previewing the kit, and opening a draft pull
request. It follows the project's voice and ethos rules for you. You can also author
the files by hand if you prefer.

A few things worth knowing, with the rest in [`CONTRIBUTING.md`](CONTRIBUTING.md):

- A maintainer reviews and merges every pull request.
- You do **not** need an OpenAI key. A prompts-only story is illustrated by the
  maintainer after it is accepted; their key is never used by a contributor. If you
  want to, you may include pictures you made yourself or generated with your own key.
- Please do not commit built PDFs; continuous integration validates your PR and
  builds a preview kit you can download.
- British English is the source of truth; non-English text is treated as
  machine-drafted and may get a native-speaker review.

The voice, reading-level, peril-tone, and canon rules live in `CLAUDE.md` and the
`authoring-story-content` guidance.

## The promise

This is an open project. Whatever you build with it, keep the promise the games
make: cooperative play, nobody left out, no losers, and the quiet lesson that you
get furthest by being clever and kind.
