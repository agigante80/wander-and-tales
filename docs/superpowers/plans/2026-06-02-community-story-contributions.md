# Community Story Contributions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let anyone author a story through a guided `create-story` skill and submit it as a draft PR the maintainer reviews, with a no-secret PR validation CI and a maintainer-only, manually triggered art/build workflow that keeps the OpenAI key private.

**Architecture:** Three independent pieces. (A) A new Claude skill at `.claude/skills/create-story/` that runs the interview and the mechanical steps and defers all voice/ethos rules to the existing `authoring-story-content` skill; plus governance files (PR template, CONTRIBUTING, CODEOWNERS). (B) `.github/workflows/validate-pr.yml`, triggered on `pull_request` with read-only permissions and no secrets. (C) `.github/workflows/build-art.yml`, triggered by `workflow_dispatch` only, using the `OPENAI_API_KEY` repo secret on `main`. The trust boundary is GitHub's own rule that fork-PR runs never see secrets and `workflow_dispatch` needs write access.

**Tech Stack:** Markdown (the skill and governance docs), GitHub Actions YAML, and the existing `build` CLI (`validate`, `lint`, `render`, `catalog`, `generate-images`). No new Python or dependencies.

This is content and configuration, not library code, so verification is "the file is valid and the existing checks still pass", not unit tests. Each task creates one focused file, verifies it, and commits.

---

## File structure

```
.claude/skills/create-story/SKILL.md                 # the orchestrator skill
.claude/skills/create-story/references/interview.md  # interview script + new-world seeds
.claude/skills/create-story/references/submitting.md # validate/preview/PR steps + PR body
.github/pull_request_template.md                     # the contributor checklist
.github/workflows/validate-pr.yml                    # PR CI: validate + lint + preview (no secrets)
.github/workflows/build-art.yml                      # maintainer art/build (manual, secret-gated)
CONTRIBUTING.md                                      # how to contribute + the trust model
CODEOWNERS                                           # route content review to the maintainer
```

---

## Part A: the create-story skill and governance

### Task A1: The create-story skill (SKILL.md)

**Files:**
- Create: `.claude/skills/create-story/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `.claude/skills/create-story/SKILL.md` with YAML frontmatter and the body. Frontmatter:

```markdown
---
name: create-story
description: Use when a user wants to create a new Wits & Wonder story or world and optionally open a pull request to contribute it. Guides choosing or creating a world, choosing or writing a story idea, setting the audience and challenges, authoring the content in every project locale (en-GB then es-ES) with image prompts, validating and previewing the kit, and opening a draft PR. Defers all voice, reading-level, peril-tone, and canon-name rules to the authoring-story-content skill.
---
```

The body must instruct the model to:

1. **Invoke `authoring-story-content` first** and follow its rules for all prose. This skill does not restate voice rules; it orchestrates.
2. **Run the interview** (see `references/interview.md`): choose a world (existing / suggested seed / custom new), choose or write a story idea, set age tier, reading levels, skill mix, peril, players, play time, and any special requirements. Offer sensible defaults so a one-line request works.
3. **Reuse canon, never redefine it.** Read the world's `canon/*.yaml` and `lexicon/terms.yaml` before naming anything; reuse exact en-GB and es-ES names; treat each entry's `description` as a contract; add new `canon/` entries for genuinely new things.
4. **Author the content.** Draft en-GB first, then every locale in `build/locales.py` `REQUIRED_LOCALES` (es-ES today). Produce `story.yaml` (tags plus image `prompts`), the five `content/<locale>/*.md` files, and for a new world the `world.yaml` (with `visual_style`) and `canon/`. Image entries always include prompts.
5. **Offer pictures (optional).** Prompts only (the maintainer illustrates later, no key needed), or generate now with the author's OWN OpenAI key via `python -m build generate-images`, or drop in the author's own original art. Never use the maintainer's key.
6. **Run the advisory consistency check.** Compare the new story's use of canon against existing canon descriptions and existing story prose; surface likely contradictions for the author to fix. Advisory, not a gate.
7. **Validate and preview** (see `references/submitting.md`): `python -m build validate --root .`, `python -m build lint --root .` (fix errors; image-file warnings are fine), `python -m build render ...` to preview, `python -m build catalog --root . --out catalog.md`.
8. **Submit or stop:** open a draft PR with the template (see `references/submitting.md`), committing text content and any proposed art but NOT built PDFs; or stop with a local kit.

Keep the body concise and instruction-shaped (numbered steps and short rules), in the same register as `authoring-story-content/SKILL.md`. No em dashes or en dashes.

- [ ] **Step 2: Verify the skill is well-formed**

Run:
```bash
python -c "
import re, pathlib
t = pathlib.Path('.claude/skills/create-story/SKILL.md').read_text(encoding='utf-8')
assert t.startswith('---'), 'missing frontmatter'
assert 'name: create-story' in t
assert 'description:' in t
print('frontmatter OK,', len(t), 'chars')
"
```
Expected: prints `frontmatter OK`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/create-story/SKILL.md
git commit -m "feat: create-story skill (orchestrates authoring and PR submission)"
git push origin main
```

### Task A2: The interview reference

**Files:**
- Create: `.claude/skills/create-story/references/interview.md`

- [ ] **Step 1: Write it**

Create `.claude/skills/create-story/references/interview.md` covering, as a guided script:

- **World choice** with three branches and what each needs: use an existing world (read `worlds/`); start from a suggested seed (offer a short list of on-brand worlds, for example a frozen island, a desert bazaar, a deep-sea reef, a cloud kingdom, each with a one-line tone and a peril fit); or create a custom world (then scaffold `world.yaml` with name, tone, palette of seven hex colours, `fonts.default`, `lore_summary`, `visual_style`, and an initial `canon/`).
- **Story idea**: offer three to five ideas fitted to the world and audience, or take the author's own; every idea must keep the no-lose, clever-and-kind ethos and match the world's peril.
- **Parameters** with their allowed values and defaults: age tier (`early`/`young`/`older`), reading levels (`simple`, `rich`, or both), skills (from `build/tags.py` `SKILLS`), peril (`gentle`/`mild`/`heroic`), players (min/max), play time, and free-form special requirements.
- A short "fast path" example showing the minimum a user must say.

No em dashes or en dashes.

- [ ] **Step 2: Verify and commit**

Run: `python -c "import pathlib; print('ok', len(pathlib.Path('.claude/skills/create-story/references/interview.md').read_text()))"`
Then:
```bash
git add .claude/skills/create-story/references/interview.md
git commit -m "docs: create-story interview reference"
git push origin main
```

### Task A3: The submitting reference (validate, preview, PR)

**Files:**
- Create: `.claude/skills/create-story/references/submitting.md`

- [ ] **Step 1: Write it**

Create `.claude/skills/create-story/references/submitting.md` with the exact mechanical steps:

- The validate/lint/preview/catalog commands (copy the four commands from the spec, with the note that image-file warnings are expected for a prompts-only story).
- The git steps: create a branch `story/<world>-<story>`, `git add` the content (`worlds/<world>/`, any `guide/` change) and any proposed art, regenerate and add `catalog.md`, but do NOT add built PDFs or anything under `dist/`.
- Opening a draft PR with the GitHub CLI: `gh pr create --draft --title "..." --body-file <body>` (or the GitHub MCP), and a fallback that prints the branch name and the exact `gh`/web steps if `gh` is not authenticated.
- The PR body template text: a short summary, the world and story, which locales were authored and that non-English text is machine-drafted, whether art is included and that it is the author's to give, and the quality checklist (mirror `.github/pull_request_template.md`).

No em dashes or en dashes.

- [ ] **Step 2: Verify and commit**

Run: `python -c "import pathlib; print('ok', len(pathlib.Path('.claude/skills/create-story/references/submitting.md').read_text()))"`
Then:
```bash
git add .claude/skills/create-story/references/submitting.md
git commit -m "docs: create-story submitting reference (validate, preview, draft PR)"
git push origin main
```

### Task A4: The PR template

**Files:**
- Create: `.github/pull_request_template.md`

- [ ] **Step 1: Write it**

Create `.github/pull_request_template.md`:

```markdown
## What is this?

A new or updated Wits & Wonder story or world.

- **World:**
- **Story:**
- **Locales authored:** en-GB (canonical), es-ES
- **Reading levels:** simple / rich

## Checklist

- [ ] I used the `create-story` skill, or followed the `authoring-story-content` rules.
- [ ] `python -m build validate --root .` passes.
- [ ] `python -m build lint --root .` reports no errors (image-file warnings are fine).
- [ ] Nobody loses: a failed roll reads as a detour, not a defeat; no real villains beyond the world's peril, and any foe is befriended or "falls" without cruelty.
- [ ] Difficulty is in bands (Easy/Normal/Hard), never named dice.
- [ ] Every named place, character, creature, item, and term is in the world's `canon/` with matching en-GB and es-ES names.
- [ ] Any claim about children is associational, not causal.
- [ ] No em dashes or en dashes anywhere.
- [ ] Reading level matches the file (simple vs rich).

## Translations

- [ ] The es-ES (and any other non-English) text is machine-drafted and needs a native review before it is considered final.

## Art (only if you included pictures)

- [ ] The images I added are mine to give (my own work, art I generated, or otherwise licensed for an open project).

I understand a maintainer will review this PR, may request changes, and may regenerate or replace the art.
```

- [ ] **Step 2: Commit**

```bash
git add .github/pull_request_template.md
git commit -m "feat: PR template with the contribution checklist"
git push origin main
```

### Task A5: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write it**

Create `CONTRIBUTING.md` covering: that contributions are story and world content; the easiest way is the `create-story` skill in Claude Code; the trust model (the maintainer reviews and merges every PR; your PR needs no OpenAI key; the maintainer's key is private and used only after acceptance); what a PR should contain (text, prompts, optionally your own art; never built PDFs); and a pointer to `CLAUDE.md` and the `authoring-story-content` rules. Keep it short. No em dashes or en dashes.

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: CONTRIBUTING guide and the contribution trust model"
git push origin main
```

### Task A6: CODEOWNERS

**Files:**
- Create: `CODEOWNERS`

- [ ] **Step 1: Write it**

Create `CODEOWNERS` routing content review to the maintainer (replace the handle if different):

```
# The maintainer reviews all content and toolchain changes.
*               @agigante80
/worlds/        @agigante80
/guide/         @agigante80
/lexicon/       @agigante80
/build/         @agigante80
```

- [ ] **Step 2: Commit**

```bash
git add CODEOWNERS
git commit -m "chore: CODEOWNERS routes content review to the maintainer"
git push origin main
```

---

## Part B: PR validation CI

### Task B1: validate-pr.yml

**Files:**
- Create: `.github/workflows/validate-pr.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/validate-pr.yml`:

```yaml
name: Validate PR

on:
  pull_request:
    paths:
      - 'worlds/**'
      - 'guide/**'
      - 'lexicon/**'
      - 'build/**'
      - 'tests/**'
      - 'pyproject.toml'

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Cairo
        run: sudo apt-get update && sudo apt-get install -y libcairo2
      - name: Install the toolchain
        run: pip install -e ".[dev,render]"
      - name: Run the test suite
        run: python -m pytest -q
      - name: Validate content
        run: python -m build validate --root .
      - name: Lint content
        run: python -m build lint --root .
      - name: Build preview kits
        run: |
          mkdir -p preview
          python - <<'PY'
          from pathlib import Path
          from build import content
          from build.render import kit
          for story_yaml in sorted(Path("worlds").glob("*/stories/*/story.yaml")):
              story = content.load_story(story_yaml)
              world = story_yaml.parents[2].name
              for locale in ("en-GB", "es-ES"):
                  kit.build_kit(Path("."), world, story.id, locale, "simple", out_dir=Path("preview"))
          PY
      - uses: actions/upload-artifact@v4
        with:
          name: preview-kits
          path: preview/*.pdf
```

Note: `permissions: contents: read` and no `secrets` reference, so this is safe on fork PRs. `build lint` exits non-zero on errors, failing the job.

- [ ] **Step 2: Verify the YAML parses**

Run:
```bash
python -c "import yaml; d=yaml.safe_load(open('.github/workflows/validate-pr.yml')); assert d['jobs']['validate']; assert d['permissions']=={'contents':'read'}; print('valid, read-only')"
```
Expected: `valid, read-only`.

- [ ] **Step 3: Confirm the preview build script runs locally (sanity)**

Run the embedded Python locally to confirm it builds previews against the real repo:
```bash
mkdir -p preview && python - <<'PY'
from pathlib import Path
from build import content
from build.render import kit
n=0
for story_yaml in sorted(Path("worlds").glob("*/stories/*/story.yaml")):
    story = content.load_story(story_yaml); world = story_yaml.parents[2].name
    for locale in ("en-GB","es-ES"):
        kit.build_kit(Path("."), world, story.id, locale, "simple", out_dir=Path("preview")); n+=1
print(n,"preview kits built")
PY
rm -rf preview
```
Expected: `4 preview kits built` (two stories times two locales).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/validate-pr.yml
git commit -m "ci: validate, lint, and preview kits on every PR (no secrets)"
git push origin main
```

---

## Part C: maintainer art/build workflow

### Task C1: build-art.yml

**Files:**
- Create: `.github/workflows/build-art.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/build-art.yml`:

```yaml
name: Generate art and rebuild kits

on:
  workflow_dispatch:
    inputs:
      world:
        description: "World id (folder under worlds/)"
        required: true
      story:
        description: "Story id (folder under worlds/<world>/stories/)"
        required: true

permissions:
  contents: write

jobs:
  art:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Cairo
        run: sudo apt-get update && sudo apt-get install -y libcairo2
      - name: Install the toolchain with the images extra
        run: pip install -e ".[dev,render,images]"
      - name: Generate the missing art
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python -m build generate-images --root . --world "${{ inputs.world }}" --story "${{ inputs.story }}"
      - name: Rebuild kits and the catalogue
        run: |
          python - <<'PY'
          import os
          from pathlib import Path
          from build import catalog, content
          from build.render import kit
          world = os.environ["WORLD"]; story = os.environ["STORY"]
          for locale in ("en-GB", "es-ES"):
              for level in ("simple", "rich"):
                  kit.build_kit(Path("."), world, story, locale, level, out_dir=Path("kits"))
          catalog.write_catalog(list(content.iter_stories(Path("worlds"))), Path("catalog.md"))
          PY
        env:
          WORLD: ${{ inputs.world }}
          STORY: ${{ inputs.story }}
      - name: Commit the art and kits
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add worlds kits catalog.md
          git commit -m "art: generate illustrations and rebuild kits for ${{ inputs.world }}/${{ inputs.story }}" || echo "nothing to commit"
          git push
```

Note: `workflow_dispatch` only (manual, write-access users only), `permissions: contents: write` to commit the art and PDFs, and the key read only here via `secrets.OPENAI_API_KEY`. The world/story are passed to the inline Python through the environment rather than string interpolation, to avoid quoting issues.

- [ ] **Step 2: Verify the YAML parses and is dispatch-only**

Run:
```bash
python -c "
import yaml
d = yaml.safe_load(open('.github/workflows/build-art.yml'))
assert list(d['on'].keys()) == ['workflow_dispatch'], d['on']
assert d['permissions'] == {'contents':'write'}
print('valid, manual dispatch only, write perms')
"
```
Expected: `valid, manual dispatch only, write perms`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build-art.yml
git commit -m "ci: maintainer-only manual workflow to generate art and rebuild kits"
git push origin main
```

---

## Part D: final verification

### Task D1: Confirm nothing regressed and the boundary holds

- [ ] **Step 1: Run the suite and content checks**

Run:
```bash
python -m pytest -q
python -m build validate --root .
python -m build lint --root . >/dev/null; echo "lint exit $?"
```
Expected: suite green, validate OK, lint exit 0 (warnings only).

- [ ] **Step 2: Confirm the trust boundary in the workflows**

Run:
```bash
echo "validate-pr must NOT reference secrets:"; grep -n "secrets" .github/workflows/validate-pr.yml || echo "  none (good)"
echo "build-art must be workflow_dispatch only:"; grep -n "pull_request\|push:" .github/workflows/build-art.yml || echo "  no PR/push trigger (good)"
```
Expected: validate-pr references no secrets; build-art has no `pull_request` or `push` trigger.

- [ ] **Step 3: Dash sweep over the new files**

Run:
```bash
grep -rlP '[\x{2013}\x{2014}]' .claude/skills/create-story .github CONTRIBUTING.md CODEOWNERS 2>/dev/null && echo "DASHES (fix)" || echo "no dashes (good)"
```
Expected: `no dashes (good)`.

- [ ] **Step 4: Commit any final touch-ups, then done**

If steps 1 to 3 surfaced fixes, make them and commit. Otherwise the feature is complete.

---

## Self-review

**Spec coverage:**
- The create-story skill (interview, canon reuse, multi-locale authoring, prompts, optional art, advisory check, validate/preview, draft PR, both modes): Tasks A1, A2, A3. Covered.
- PR template, CONTRIBUTING, CODEOWNERS (governance, art provenance, machine-translation flag): Tasks A4, A5, A6. Covered.
- PR validation CI (no secrets, validate/lint/preview): Task B1. Covered.
- Maintainer art/build workflow (manual, secret-gated, on main): Task C1. Covered.
- Trust boundary (no secrets on PR runs; dispatch-only art): enforced by B1 `permissions: contents: read` + no secrets, and C1 `workflow_dispatch` only; checked in D1 Step 2.
- Minimum contributor requirement (Claude Code + GitHub account; key optional; Python optional via CI): documented in CONTRIBUTING (A5) and realised by B1 doing the checks.

**Placeholder scan:** the config and governance files have complete content; the skill and reference docs (A1 to A3) specify exact sections, branches, and commands to author, which is the appropriate granularity for authoring a skill (the prose is written during execution, not a TODO).

**Consistency:** the four CLI commands (`validate`, `lint`, `render`, `catalog`, `generate-images`) are used identically across tasks; the workflow inputs `world`/`story` match `generate-images --world/--story`; `CODEOWNERS` handle `@agigante80` matches the git remote owner; locales come from `REQUIRED_LOCALES` (en-GB, es-ES).

---

## Execution handoff

Plan complete. Three parts (A: skill + governance, B: PR CI, C: art workflow) plus a final check, build order A, B, C, D.

Two execution options:

1. **Subagent-Driven (recommended):** a fresh subagent per task with review between tasks.
2. **Inline Execution:** execute the tasks in this session with checkpoints.

Which approach?
