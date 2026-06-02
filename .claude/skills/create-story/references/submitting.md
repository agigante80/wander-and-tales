# Validating, previewing, and submitting a story

The mechanical steps once the content is authored. Run them from the repository
root with the project virtualenv active (or prefix with `.venv/bin/`).

## 1. Validate and lint

```bash
python -m build validate --root .
python -m build lint --root .
```

`validate` must say OK. `lint` must report no `[error]` lines; `[warning]` lines
are fine. For a prompts-only story you will see image-file warnings ("image ... has
no generated file"), which are expected and not a problem: the maintainer
illustrates after acceptance.

## 2. Preview the kit

Build a kit so the author can open it:

```bash
python -m build render --root . \
  --world <world> --story <story> \
  --locale en-GB --reading-level simple
```

The PDF lands in `dist/` (gitignored). Build other locales or the `rich` level the
same way. Then refresh the catalogue (it is text and belongs in the PR):

```bash
python -m build catalog --root . --out catalog.md
```

## 3a. Keep it for yourself

If the author does not want to contribute, stop here. They have a local kit in
`dist/`. Nothing is pushed.

## 3b. Open a draft pull request

Create a branch and commit only the content (and any art the author chose to
include), never built PDFs or anything under `dist/`:

```bash
git checkout -b story/<world>-<story>
git add worlds/<world> catalog.md        # plus guide/ if the guide changed
# include proposed art only if the author made it themselves:
#   git add worlds/<world>/**/assets/*.png   (or *.jpg)
git status   # confirm: no dist/, no stray files
git commit -m "story: <Story Title> in <World>"
git push -u origin story/<world>-<story>
```

Open the PR as a **draft** with the body below. Use the GitHub CLI:

```bash
gh pr create --draft \
  --title "story: <Story Title> in <World>" \
  --body-file <(cat <<'BODY'
<paste the filled PR body here>
BODY
)
```

If `gh` is not authenticated (run `gh auth status` to check), or the GitHub MCP is
not available, do not guess. Print the branch name and tell the author to either
run `gh auth login` and retry, or open the PR in the web UI from their pushed
branch. The PR template in `.github/pull_request_template.md` will pre-fill the
checklist in the web UI.

## The PR body

Fill the repository PR template (`.github/pull_request_template.md`). At minimum
state: the world and story; which locales were authored, and that any non-English
text is machine-drafted and needs a native review; whether art is included and, if
so, that it is the author's to give; and tick the quality checklist (nobody loses,
bands not dice, canon-consistent names, associational claims, no dashes, reading
level matches the file). Note that a maintainer will review, may request changes,
and may regenerate or replace the art.
