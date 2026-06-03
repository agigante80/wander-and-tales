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

Each story comes as a **Story Pack** (what you play from, safe for a child to see), a
**Grown-up's Playbook** (the rules and the puzzle answers), and each world has a
**World Book** (its lore, who's who, and idea bank). The **Simple** Story Pack reads
aloud well for ages 3 to 8; the **Rich** one suits ages 9 to 12. Every PDF shows its
version on the last page, and the links below are generated automatically.

<!-- BEGIN KIT TABLE -->

| Story | World | Language | Ages | Story Pack | Grown-up's Playbook |
|---|---|---|---|---|---|
| The Sleeping Garden | The Floating Isles | English | 6 to 8 | [Simple](kits/en-GB/floating-isles/sleeping-garden/story-pack-simple-v7.pdf) · [Rich](kits/en-GB/floating-isles/sleeping-garden/story-pack-rich-v7.pdf) | [Open](kits/en-GB/floating-isles/sleeping-garden/playbook-v5.pdf) |
| El Jardín Dormido | Las Islas Flotantes | Español | 6 to 8 | [Simple](kits/es-ES/floating-isles/sleeping-garden/story-pack-simple-v7.pdf) · [Rich](kits/es-ES/floating-isles/sleeping-garden/story-pack-rich-v7.pdf) | [Open](kits/es-ES/floating-isles/sleeping-garden/playbook-v5.pdf) |
| The Singing Spring | The Sunlit Hills of Greece | English | 9 to 12 | [Simple](kits/en-GB/greek-myth/the-singing-spring/story-pack-simple-v4.pdf) · [Rich](kits/en-GB/greek-myth/the-singing-spring/story-pack-rich-v4.pdf) | [Open](kits/en-GB/greek-myth/the-singing-spring/playbook-v4.pdf) |
| La Fuente Cantarina | Las Colinas Soleadas de Grecia | Español | 9 to 12 | [Simple](kits/es-ES/greek-myth/the-singing-spring/story-pack-simple-v4.pdf) · [Rich](kits/es-ES/greek-myth/the-singing-spring/story-pack-rich-v4.pdf) | [Open](kits/es-ES/greek-myth/the-singing-spring/playbook-v4.pdf) |

### World books

- The Floating Isles: [English](kits/en-GB/floating-isles/world-book-v7.pdf) · [Español](kits/es-ES/floating-isles/world-book-v7.pdf)
- The Sunlit Hills of Greece: [English](kits/en-GB/greek-myth/world-book-v7.pdf) · [Español](kits/es-ES/greek-myth/world-book-v7.pdf)

**New to running a game like this?** Read the Guide for the Grown-Up: [English](kits/guides/Guide_for_the_Grown-Up_en-GB-v2.pdf) · [Español](kits/guides/Guide_for_the_Grown-Up_es-ES-v2.pdf).

<!-- END KIT TABLE -->

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

# build one printable Story Pack into dist/
python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple

python -m build render-playbook --root . --world floating-isles --story sleeping-garden --locale en-GB
python -m build render-world --root . --world floating-isles --locale en-GB
python -m build render-guide --root . --locale en-GB        # build the Guide PDF
python -m build rebuild --root .                            # build the whole library + refresh README
python -m build prompts --root .                            # export the image prompts
python -m build generate-images --root .                   # generate art (needs OPENAI_API_KEY)
```

### Where things live

- `worlds/<world>/` is a world: its `world.yaml`, a `canon/` name registry, an
  `assets/` folder for the map and art, and `stories/<story>/` with tags and the
  per-locale prose.
- `guide/<locale>/guide.md` is the generic Guide for the Grown-Up.
- `build/` is the importable toolchain: the content model and validation, and the
  layout-only PDF renderer in `build/render/`.
- `kits/` holds the built PDFs in a language-first tree:
  `kits/<locale>/<world>/world-book-v<n>.pdf` and
  `kits/<locale>/<world>/<story>/{story-pack-simple,story-pack-rich,playbook}-v<n>.pdf`,
  plus `kits/guides/`. `dist/` is the scratch build output and is not tracked.

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

## Licence

The **content** (everything under `worlds/`, `guide/`, and `lexicon/`, and the
generated PDFs in `kits/`) is licensed **CC BY-SA 4.0**: share and adapt it, even
commercially, with credit to Wits and Wonder, and keep derivatives under the same
licence. See [`LICENSE-CONTENT`](LICENSE-CONTENT) and
<https://creativecommons.org/licenses/by-sa/4.0/>.

The **code** (the `build/` package and `tests/`) is licensed **MIT**. See
[`LICENSE`](LICENSE).

By contributing, you agree to license your contribution under these same terms.

## The promise

This is an open project. Whatever you build with it, keep the promise the games
make: cooperative play, nobody left out, no losers, and the quiet lesson that you
get furthest by being clever and kind.
