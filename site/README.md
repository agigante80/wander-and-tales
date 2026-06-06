# Site content manifest

`manifest.json` is a machine-readable snapshot of the whole library for a website to
ingest: every world and story with titles, tags, lore, beat headings, image paths, and
PDF links, in every supported language. PDF filenames carry no version (stable URLs);
each PDF entry is `{path, version, updated}` instead, so the site can show the version.
It is generated from the repo content, so it is derived data; regenerate it rather than
editing it by hand.

## Regenerate

`python -m build rebuild` refreshes this file automatically as its last step, so a
normal publish keeps it current. To regenerate it on its own (without rebuilding the
PDFs), run from the repo root with the project virtualenv:

```bash
.venv/bin/python -m build manifest --root .
```

Both read the built kits under `kits/`, so the PDF links always point at the current,
stable (unversioned) filenames. The generator lives in `build/render/manifest.py`.

## Shape

- `site`: name, tagline (per locale), domain, repo, the language list and endonyms,
  level labels, the licence block (content CC BY-SA 4.0, code MIT, AI-illustration and
  font notes), analytics placeholder, cookie-consent flag, GitHub-issues contact, the
  "create your own with Claude" block, the shared Guide and How to Play PDFs, and
  counts.
- `worlds[]`: id, name (per locale), tone, `hero_powers`, palette, lore (per locale),
  visual style, world images, canon (with per-locale names and descriptions and a
  portrait path where one exists), example heroes, the world-level PDFs, and `stories`.
- `worlds[].stories[]`: id, title (per locale), tags (age, skills, peril, players,
  time, dice), `beats` (the ordered `##` headings per locale, which double as the
  reader's chapter chips and align with the scene images), `content_paths` (the
  markdown to render: kid-facing `simple` and `rich`; `rules` and `puzzles` are
  grown-up only), the ordered `images`, the `map` (almost always `generated`), and the
  per-locale `tale_simple` / `tale_rich` / `atlas` PDFs, each a `{path, version, updated}`
  object (the world-level `world_book` / `example_heroes` and the shared `guide` /
  `how_to_play` follow the same shape).

## Paths

All file paths are repo-relative. Prepend `site.repo_raw_base`
(`https://raw.githubusercontent.com/agigante80/wander-and-tales/main/`) to fetch any
image, markdown, or PDF directly, or serve the files from your own host.
