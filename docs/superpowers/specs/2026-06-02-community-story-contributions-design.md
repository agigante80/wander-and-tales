# Wits & Wonder: community story contributions

**Status:** design for review. Decomposes into three implementation plans (see the
end). The interactive brainstorming happened in a chat thread with the maintainer;
this document is the validated design, written for review before planning.

**Context:** The repository is built so that adding a world, story, or language is a
writing task, not a coding task. We want to let anyone author a new story (in an
existing world or a new one) through a guided Claude skill, and submit it as a
**pull request the maintainer reviews**. The maintainer keeps their own OpenAI key
private: contributors never use it, and it is spent only on stories the maintainer
has already accepted. Content quality stays human-gated; the machinery only removes
friction.

This design is shaped by four decisions reached with the maintainer:

1. Contributions arrive as **draft PRs for human review**, never auto-merged.
2. The contributor produces **text content and image prompts only**, no generated
   art and no built PDFs in the PR.
3. The maintainer's **OpenAI key is a repository secret**, used only on the trusted
   `main` branch through a manually triggered workflow, never by a contributor PR.
4. Image art and the final illustrated PDFs are produced **after acceptance**, by
   the maintainer's workflow.

## Goals

- A guided skill that walks any author through creating a complete, valid story:
  pick or create a world, choose or write a story idea, set the audience (age tier,
  reading levels), challenge mix, peril, players, play time, and any special
  requirements.
- Author the story in en-GB (canonical) and every other locale the project manages
  (es-ES today), reusing canon consistently and never redefining existing entries.
- Run the existing `validate` and `lint` before submitting, and build a text-only
  preview PDF so the author can see their kit.
- Open a draft PR containing only text (YAML and Markdown) plus image prompts.
- A CI check on every PR that validates, lints, and builds a preview, using no
  secrets, so the maintainer can review a fork PR safely and see a built kit.
- A maintainer-only workflow that generates the art and rebuilds the illustrated
  PDFs after merge, gated behind the private key.

## Non-goals (deferred or out of scope)

- Auto-merging contributions, or any automated acceptance. A human reviews every PR.
- Generating images or committing PDFs inside a contributor PR.
- Guaranteeing semantic canon consistency automatically (see the trust and quality
  section); the model offers an advisory check only.
- Verifying the quality of a language the maintainer does not read. Non-English text
  is machine-drafted and labelled for native review.
- A web UI. The skill runs in Claude Code.

## The trust boundary (the spine of the design)

GitHub already enforces the maintainer's constraint, and the design leans on it:

- **Secrets are never exposed to workflow runs triggered by `pull_request` events
  from forks.** So a contributor's PR cannot use the OpenAI key even if a workflow
  tried.
- **`workflow_dispatch` can only be triggered by users with write access.** So the
  art workflow can only be run by the maintainer.

Therefore the key lives as the `OPENAI_API_KEY` repository secret, and only the
maintainer-only workflow (running on `main`, triggered manually) reads it. The PR
validation workflow runs with no secrets at all. Contributors need no key.

## System overview

Three independent pieces, built and shipped separately:

```
Contributor (Claude Code + a GitHub account)
   |
   v
[1] create-story skill  ->  draft PR (text + image prompts only)
   |
   v
[2] PR validation CI (no secrets)  ->  validate + lint + preview PDF artifact
   |
   v
Maintainer reviews the prose and prompts, requests changes or merges
   |
   v
[3] maintainer art/build workflow (manual, uses the secret on main)
       ->  generate-images, rebuild illustrated PDFs, regenerate catalog, commit
```

## Part 1: the `create-story` skill

A new skill at `.claude/skills/create-story/` (SKILL.md plus references), following
the existing `authoring-story-content` layout. It is an **orchestrator**: it runs
the interview and the mechanical steps, and defers all voice, reading-level,
peril-tone, and canon-name rules to the existing `authoring-story-content` skill
rather than duplicating them.

### The guided flow

1. **Choose a world.** Three paths:
   - Use an existing world (list the worlds found under `worlds/`).
   - Start from a suggested new world (the skill offers a few on-brand seeds, for
     example a frozen island, a desert bazaar, a deep-sea reef).
   - Create a custom new world the author describes. A new world means scaffolding
     `world.yaml` (name, tone, palette, fonts, lore, `visual_style`) and an initial
     `canon/`.
2. **Choose a story idea.** Offer a few ideas fitted to the chosen world and
   audience, or let the author write their own. Ideas must fit the no-lose,
   clever-and-kind ethos and the world's peril level.
3. **Set the parameters.** Age tier (`early`/`young`/`older`), which reading levels
   to write (simple, rich, or both), the skill mix, peril, players, play time, and
   any special requirements the author states (a theme, a learning focus, a length).
   Sensible defaults make a one-line "just give me a gentle story for a six year
   old" path possible.
4. **Reuse canon, do not redefine it.** Before naming anything, the skill reads the
   world's `canon/` and the repo `lexicon/`. Existing entries are reused with their
   exact en-GB and es-ES names, and their `description` is treated as a contract
   (an existing creature keeps its disposition and nature). Genuinely new things get
   new canon entries. The skill never rewrites an existing entry.
5. **Write the content.** Draft en-GB first (the source of truth), then every other
   locale in `locales.REQUIRED_LOCALES` (es-ES today), translating for the target
   child's ear, not literally. Produce `story.yaml` (tags plus image prompts),
   `content/<locale>/` (the five Markdown files), and, for a new world, `world.yaml`
   and `canon/`. Image entries are **prompts only**; the skill never generates art.
6. **Advisory consistency check.** The skill reviews the new story's use of canon
   against the existing canon descriptions and existing story prose, and surfaces
   any likely contradiction (for example using a gentle creature as a villain) for
   the author to resolve. This is advisory, not a hard gate.
7. **Validate and preview.** Run `python -m build validate` and `python -m build
   lint`, fixing structural issues until clean (image-file warnings are expected and
   fine). Build a text-only kit PDF with `python -m build render` so the author sees
   their work, and regenerate `catalog.md`.
8. **Submit, or stop.** Two modes:
   - **Contribute:** create a branch, commit the text content (no art, no PDFs),
     and open a **draft PR** with a filled-in template (the quality checklist plus a
     note that non-English text is machine-drafted and needs native review). The
     skill uses the `gh` CLI or the GitHub MCP; if neither is authenticated it
     prepares the branch and prints the exact steps.
   - **Keep it for yourself:** stop after step 7 with a local kit. No PR.

### Inputs, interfaces, dependencies

- Depends on the existing toolchain (`validate`, `lint`, `render`, `catalog`,
  `prompts`) and the `authoring-story-content` skill. It adds no Python code; it
  drives the existing CLI and writes content files.
- The locale list comes from `build/locales.py` (`REQUIRED_LOCALES`), so adding a
  language later needs no skill change.
- References under `create-story/references/` hold the interview script, the
  new-world seed list, and the PR body template.

## Part 2: PR validation CI

A GitHub Actions workflow at `.github/workflows/validate-pr.yml`, triggered on
`pull_request`. It uses **no secrets**, so it runs safely on fork PRs.

Steps: check out, set up Python 3.11, install `libcairo2`, `pip install -e
".[dev,render]"`, then run `python -m pytest -q`, `python -m build validate --root
.`, and `python -m build lint --root .` (it fails on lint errors; image-file
warnings are allowed). It then builds the changed story's text-only kit PDFs and
uploads them as a workflow artifact, so the maintainer can download and eyeball a
real kit without building anything locally. Determining the "changed story" can be
as simple as building every story; with two stories this is cheap, and the workflow
notes if it ever needs narrowing.

This gives the maintainer an automated structural gate plus a one-click preview on
every PR, with zero key exposure.

## Part 3: maintainer art/build workflow

A GitHub Actions workflow at `.github/workflows/build-art.yml`, triggered by
`workflow_dispatch` (a manual button), so only a user with write access runs it,
and it runs on `main` where the secret is available. Default to manual rather than
"on every merge" so the maintainer's spend stays deliberate.

It takes a world and story as inputs, installs `pip install -e
".[dev,render,images]"`, writes the `OPENAI_API_KEY` secret into the environment,
runs `python -m build generate-images --root . --world <w> --story <s>`, rebuilds
that story's illustrated kit PDFs into `kits/`, regenerates `catalog.md`, and
commits the new art and PDFs to `main` with a clear message. The maintainer can
equally run these same commands locally; the workflow just makes it a button.

Because this is the only place the key is read, and it is unreachable from a fork
PR and runnable only by a writer, the key stays private and is spent only on
accepted content.

## Governance and quality

- **PR template** at `.github/pull_request_template.md`: the authoring quality
  checklist (nobody loses, bands not dice, canon-consistent names, associational
  claims, no dashes, reading level matches the file) plus a checkbox acknowledging
  that any non-English text is machine-drafted and needs native review.
- **CONTRIBUTING.md**: a short guide pointing contributors at the `create-story`
  skill and explaining the review-and-merge model and the trust boundary.
- **CODEOWNERS** (optional): routes review of `worlds/`, `guide/`, and `lexicon/`
  to the maintainer, making the human gate explicit.
- The maintainer is, by design, the editor-in-chief: every contribution is their
  review, including languages they cannot personally verify. The skill reduces the
  burden by guaranteeing structural validity before the PR opens and by flagging
  machine-translated text, but the taste and correctness call remains human.

## What a contributor needs (the minimum requirement)

- **Claude Code** (to run the `create-story` skill) and a **GitHub account** (to
  open the PR). That is the floor.
- **No OpenAI key.** Art is the maintainer's step. Text and a preview PDF do not
  need it.
- **Python locally is optional.** If the contributor has the toolchain installed,
  the skill validates and previews locally; if not, the PR validation CI does the
  validation and preview build for them. A contributor with only Claude Code and a
  GitHub account can still submit, relying on CI for the checks.

## Testing and verification

- The skill is process, not code; verify it by running it end to end against the
  real repo to produce a valid story that passes `validate` and `lint` and opens a
  well-formed draft PR.
- The PR validation workflow is verified by opening a test PR and confirming the
  checks run with no secret access and the preview artifact appears.
- The art workflow is verified by a manual dispatch on a branch with the secret set,
  confirming it generates art and rebuilds PDFs, and that it cannot be reached from
  a fork PR.
- No change to the existing pytest suite is required; the workflows reuse the
  existing CLI.

## Decomposition into implementation plans

1. **Plan A: the `create-story` skill** (the contributor experience). Largest piece;
   pure content and process, plus the PR template and CONTRIBUTING.md.
2. **Plan B: PR validation CI** (`validate-pr.yml`). Small, no secrets.
3. **Plan C: maintainer art/build workflow** (`build-art.yml`). Small, secret-gated,
   manual.

Build order: A then B (so PRs get checked), then C. A is usable on its own with the
maintainer validating locally; B and C harden and automate the loop.

## Decisions made for the maintainer to confirm

- Skill name `create-story`. Change if you prefer `contribute-a-story` or similar.
- Art workflow is **manual dispatch**, not automatic on merge, to keep spend
  deliberate. Switchable later.
- The PR carries **no PDFs and no art**, only text and prompts. Catalog.md is
  regenerated and included (it is text).
- The PR validation CI builds **every** story's preview rather than detecting the
  changed one, since there are only a few. Revisit if the library grows large.

## Future work (named, not built here)

- Narrow the PR preview build to only the changed story once the library is large.
- An automated, advisory semantic-consistency linter (LLM-assisted) as a PR comment.
- A "make it for yourself" packaging path that does not touch GitHub at all.
- Attaching built PDFs to GitHub Releases instead of committing them to `kits/`.
