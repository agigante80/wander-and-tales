# Wits & Wonder

A free, multilingual library of printable, cooperative story-adventure kits for a
grown-up and a child to play together. You print a kit, grab a die and a few
household bits, and share a gentle story-and-puzzle adventure. There is no app and
no screen. **Nobody competes, and nobody loses:** you win by being clever and kind.

Every kit comes ready to play in British English, Spanish from Spain, and Italian, at
two reading levels. It is a lovely excuse for unhurried, screen-free time together, and
a way to practise imagination, problem-solving, and teamwork. Adding a world, a
story, or a language is a writing task, not a coding task.

## Print a ready-made kit

Each story comes as a **Story Pack** (what you play from, safe for a child to see), a
**Grown-up's Playbook** (the rules and the puzzle answers), and each world has a
**World Book** (its lore, who's who, and idea bank). The **Simple** Story Pack reads
aloud well for ages 3 to 8; the **Rich** one suits ages 9 to 12. Every PDF shows its
version on the last page, and the links below are generated automatically.

<!-- BEGIN KIT TABLE -->

Every story is cooperative and no-lose, for two or more (a grown-up and one or
more children), and playable with a single ordinary die.

| Story | World | Ages | Skills | Peril | Time | Get the kit |
|---|---|---|---|---|---|---|
| The Sleeping Garden | The Floating Isles | 6 to 8 | vocabulary, logic, social-emotional | gentle | 30 min | English: [Simple](kits/en-GB/floating-isles/sleeping-garden/story-pack-simple-v7.pdf) · [Rich](kits/en-GB/floating-isles/sleeping-garden/story-pack-rich-v7.pdf) · [Playbook](kits/en-GB/floating-isles/sleeping-garden/playbook-v5.pdf)<br>Español: [Sencillo](kits/es-ES/floating-isles/sleeping-garden/story-pack-simple-v7.pdf) · [Completo](kits/es-ES/floating-isles/sleeping-garden/story-pack-rich-v7.pdf) · [Cuaderno](kits/es-ES/floating-isles/sleeping-garden/playbook-v5.pdf) |
| The Singing Spring | The Sunlit Hills of Greece | 9 to 12 | logic, vocabulary, spatial, social-emotional | heroic | 40 min | English: [Simple](kits/en-GB/greek-myth/the-singing-spring/story-pack-simple-v5.pdf) · [Rich](kits/en-GB/greek-myth/the-singing-spring/story-pack-rich-v5.pdf) · [Playbook](kits/en-GB/greek-myth/the-singing-spring/playbook-v4.pdf)<br>Español: [Sencillo](kits/es-ES/greek-myth/the-singing-spring/story-pack-simple-v5.pdf) · [Completo](kits/es-ES/greek-myth/the-singing-spring/story-pack-rich-v5.pdf) · [Cuaderno](kits/es-ES/greek-myth/the-singing-spring/playbook-v4.pdf) |

### World books

- The Floating Isles: [English](kits/en-GB/floating-isles/world-book-v7.pdf) · [Español](kits/es-ES/floating-isles/world-book-v7.pdf)
- The Sunlit Hills of Greece: [English](kits/en-GB/greek-myth/world-book-v8.pdf) · [Español](kits/es-ES/greek-myth/world-book-v8.pdf)

**New to running a game like this?** Read the Guide for the Grown-Up: [English](kits/guides/Guide_for_the_Grown-Up_en-GB-v2.pdf) · [Español](kits/guides/Guide_for_the_Grown-Up_es-ES-v2.pdf).

<!-- END KIT TABLE -->

The table above is generated; it lists every story with its tags and the download
links for each language.

## Create your own story

The whole point of this project is that you can write your own adventure and print it.
The easiest way is in Claude Code with the **`create-story`** skill, which interviews
you, writes the content, makes (or prompts for) the pictures, and builds your printable
PDFs. You do not need to be a programmer.

**1. Clone the repository.**

```bash
git clone https://github.com/agigante80/wits-and-wonder.git
cd wits-and-wonder
```

**2. Set up the toolchain** (Python 3.11 or newer; on Debian or Ubuntu you also need
`libcairo2` for the maps, usually already installed).

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,render]"
```

For generated pictures, also add the optional `images` extra and put your own OpenAI
key in a local `.env` (see `.env.example`): `pip install -e ".[images]"`. This is
optional (see step 4).

**3. In Claude Code, ask to "create a story".** The `create-story` skill walks you
through choosing or inventing a world, the idea, the audience, and the challenges,
writes it in British English, Spanish from Spain, and Italian, and builds your kit. It follows
the project's gentle, no-lose voice for you. You can also author the files by hand.

**4. Pictures, your choice.** The skill can generate them with your own OpenAI key, or
just write the prompts so you paste them into any image generator you like and drop the
PNGs in, or you can skip art and play text-only. None of this is required to get a
playable kit.

**5. Print and play.** Your kit (the Story Pack, the Grown-up's Playbook, and the World
Book, in all three languages) is built into `dist/`. Print it, grab a die and a few
household bits, and play.

Kits are multilingual by design (British English, Spanish from Spain, and Italian), so
your story is written and built in all three.

## Share your story (optional)

If you have a GitHub account and would like your story added to the public library, you
can open a pull request. In Claude Code, ask to **"contribute my story"** (the
`contribute-story` skill), or follow [`CONTRIBUTING.md`](CONTRIBUTING.md) by hand. A
maintainer reviews every pull request and, if it is accepted, illustrates and publishes
it. You keep your own copy regardless; sharing is entirely optional, and you do not
commit built PDFs (the pull request carries your text and image prompts, and optionally
pictures you made yourself).

## For developers: the toolchain

`build/` is an importable Python package (the content model, validation, and the
layout-only PDF renderer in `build/render/`), driven by a small CLI.

```bash
python -m pytest                              # run the test suite
python -m build validate --root .             # load and validate all content
python -m build lint --root .                 # structural lint (exit 1 on error)

# build one printable Story Pack into dist/
python -m build render --root . \
  --world floating-isles --story sleeping-garden \
  --locale en-GB --reading-level simple

python -m build render-playbook --root . --world floating-isles --story sleeping-garden --locale en-GB
python -m build render-world --root . --world floating-isles --locale en-GB
python -m build render-guide --root . --locale en-GB        # build the Guide PDF
python -m build prompts --root .                            # export the image prompts
python -m build generate-images --root .                   # generate art (needs your OpenAI key)
python -m build rebuild --root .                            # maintainer: rebuild the library + README
```

### Where things live

- `worlds/<world>/` is a world: its `world.yaml`, a `canon/` name registry, an
  `assets/` folder for the map and art, and `stories/<story>/` with tags and the
  per-locale prose.
- `guide/<locale>/guide.md` is the generic Guide for the Grown-Up.
- `build/` is the importable toolchain: the content model and validation, and the
  layout-only PDF renderer in `build/render/`.
- `kits/` holds the maintainer-published library in a language-first tree; `dist/` is
  your own scratch build output and is not tracked.

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
