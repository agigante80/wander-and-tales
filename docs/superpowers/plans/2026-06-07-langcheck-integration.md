# LanguageTool check-lang Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared `build check-lang --locale <code>` subcommand that checks a locale's authored prose against the self-hosted LanguageTool server, and wire it into the `pt-pt-quality` skill as a second mechanical candidate finder.

**Architecture:** One layout-agnostic module (`build/langcheck.py`) finds a locale's Markdown (mirroring the pt-pt scanner), strips Markdown to plain text while preserving character offsets, POSTs it to a LanguageTool server over stdlib HTTP, and returns normalized findings with line numbers. The server URL comes from `--url`, then `$LANGUAGETOOL_URL` (loaded from `.env`), then a localhost default. The deterministic grammar, spelling, and accent layer is shared across all four locales; the register and judgment layer stays in the per-locale quality skills, which call this subcommand.

**Tech Stack:** Python 3.11, argparse (existing CLI), stdlib `urllib`/`json`/`re` (no new dependency), `python-dotenv` (already an optional dep), pytest with the existing `sample_repo` fixture.

---

## Background and decisions

This plan implements Option B from the design discussion: a single shared subcommand rather than a curl baked into each skill. Reasons: the LanguageTool call is identical for all four locales, the URL lives in exactly one place (`.env`), and the retry and Markdown handling are written once.

Why these choices:

- **stdlib `urllib`, not `requests`/`httpx`.** The project has no HTTP client in its core or render dependencies. A self-hosted form POST is trivial with `urllib`, so we add no dependency.
- **The URL is configuration, not a secret, but goes in `.env` as the user requested.** `.env` is gitignored; `.env.example` is committed as documentation. The code still defaults to `http://localhost:18010` so it runs with no `.env` at all.
- **`language` code per locale.** Portuguese uses its true European variant `pt-PT`; Spanish maps to generic `es` and Italian to `it`, because LanguageTool has no peninsular or regional rule set for those. Register for es-ES and it-IT stays with their quality skills, not with LanguageTool.
- **Offset-preserving Markdown strip.** LanguageTool would otherwise flag `#`, `*`, `|`, and link syntax as errors. We replace Markdown syntax with equal-length spaces so the text length and every newline position are unchanged, which means a returned offset maps straight back to the source line and column. This is simpler and more robust than the annotated-text JSON API for a first version.
- **Candidate finder, not a gate.** Like `scan.sh`, the subcommand prints findings and exits 0. It exits non-zero only when the server cannot be reached, so a down NAS is loud and a clean run is quiet. The transient empty-body blip we observed is absorbed by a single retry.

## File Structure

- **Create:** `build/langcheck.py` (around 110 lines). One responsibility: turn a locale plus a server URL into a list of `Finding`s. No CLI, no printing, no I/O beyond reading content files and the HTTP POST. Pure and unit-testable.
- **Create:** `tests/test_langcheck.py`. Unit tests with the HTTP call monkeypatched, plus the offset-preservation invariant and the line/column mapping.
- **Modify:** `build/__main__.py`. Register the `check-lang` subparser and add its handler block, following the exact pattern of the existing `generate-images` command (graceful dotenv load, then lazy import).
- **Modify:** `.env.example`. Document `LANGUAGETOOL_URL` with the localhost default.
- **Modify:** `.env` (gitignored, not committed). Add the real NAS URL so the user's local runs target the Synology.
- **Modify:** `.claude/skills/pt-pt-quality/SKILL.md`. Extend Pass 1 to run `check-lang` next to `scan.sh`, and explain that the two finders cover different problems.

The sibling es-ES and it-IT quality skills are deliberately out of scope for this plan; see "Follow-up: per-locale quality skills" at the end.

---

## Task 1: Document the server URL in .env and .env.example

**Files:**
- Modify: `.env.example`
- Modify: `.env` (gitignored; create the entry if missing)

- [ ] **Step 1: Add the variable to the committed template**

Append to `.env.example`:

```bash

# Used by `python -m build check-lang` to reach a self-hosted LanguageTool
# server (see /mnt/ds220p/docker/project/LanguageTool on the Synology). The
# command defaults to http://localhost:18010 if this is unset.
LANGUAGETOOL_URL=http://localhost:18010
```

- [ ] **Step 2: Set the real URL in the local .env (not committed)**

Add to `.env` (the gitignored file):

```bash
LANGUAGETOOL_URL=http://synologyds220p.duevite.eu:18010
```

- [ ] **Step 3: Verify .env is still ignored**

Run: `git check-ignore .env`
Expected: prints `.env` (so the real URL is never committed).

- [ ] **Step 4: Commit the template only**

```bash
git add .env.example
git commit -m "chore: document LANGUAGETOOL_URL in .env.example"
```

---

## Task 2: langcheck core — locale-to-language map and file discovery

**Files:**
- Create: `build/langcheck.py`
- Test: `tests/test_langcheck.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_langcheck.py
from pathlib import Path

from build import langcheck


def test_locale_language_map_covers_required_locales():
    from build.locales import REQUIRED_LOCALES
    for loc in REQUIRED_LOCALES:
        assert loc in langcheck.LOCALE_LANGUAGE
    assert langcheck.LOCALE_LANGUAGE["pt-PT"] == "pt-PT"
    assert langcheck.LOCALE_LANGUAGE["es-ES"] == "es"
    assert langcheck.LOCALE_LANGUAGE["it-IT"] == "it"
    assert langcheck.LOCALE_LANGUAGE["en-GB"] == "en-GB"


def test_iter_locale_files_finds_pt_pt_by_path_segment(tmp_path: Path):
    f1 = tmp_path / "worlds" / "w" / "stories" / "s" / "content" / "pt-PT" / "rules.md"
    f2 = tmp_path / "worlds" / "w" / "stories" / "s" / "content" / "es-ES" / "rules.md"
    f3 = tmp_path / "guide" / "pt-PT" / "guide.md"
    for f in (f1, f2, f3):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x", encoding="utf-8")
    found = langcheck.iter_locale_files(tmp_path, "pt-PT")
    assert f1 in found and f3 in found
    assert f2 not in found
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.langcheck'`

- [ ] **Step 3: Write the minimal implementation**

```python
# build/langcheck.py
"""Check authored locale content against a self-hosted LanguageTool server.

Layout-agnostic: find a locale's Markdown (mirroring the pt-pt scanner), strip
Markdown to plain text while preserving character offsets, POST it to a
LanguageTool server, and return normalized findings with line numbers. This is a
candidate finder for the locale-quality skills, not an auto-fixer.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# LanguageTool's `language` code per project locale. Portuguese keeps its true
# European variant; Spanish and Italian have no peninsular or regional rule set,
# so they map to the generic code (register stays with the locale-quality skill).
LOCALE_LANGUAGE = {
    "en-GB": "en-GB",
    "es-ES": "es",
    "it-IT": "it",
    "pt-PT": "pt-PT",
}

DEFAULT_URL = "http://localhost:18010"


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    col: int
    rule_id: str
    message: str
    context: str
    suggestions: tuple[str, ...]


def iter_locale_files(root: Path, locale: str) -> list[Path]:
    """Every Markdown file whose path carries the locale code, under worlds/ and guide/."""
    out: list[Path] = []
    for base in ("worlds", "guide"):
        base_dir = root / base
        if not base_dir.is_dir():
            continue
        for p in base_dir.rglob("*.md"):
            if locale in p.parts:
                out.append(p)
    return sorted(out)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add build/langcheck.py tests/test_langcheck.py
git commit -m "feat: langcheck locale-language map and file discovery"
```

---

## Task 3: Offset-preserving Markdown strip

**Files:**
- Modify: `build/langcheck.py`
- Test: `tests/test_langcheck.py`

- [ ] **Step 1: Write the failing test**

```python
def test_markdown_to_text_preserves_length_and_newlines():
    md = "# Stop 1: The Gate\n\nThe *cat* walks to [home](http://x).\n\n| a | b |\n"
    out = langcheck.markdown_to_text(md)
    assert len(out) == len(md)
    # newline positions identical, so line numbers map straight back
    assert [i for i, c in enumerate(out) if c == "\n"] == [i for i, c in enumerate(md) if c == "\n"]
    # heading marker and emphasis markers are gone (blanked), prose survives
    assert "Stop 1: The Gate" in out
    assert "cat" in out
    assert "#" not in out and "*" not in out
    # the table row is blanked to spaces
    assert "a | b" not in out
    # the visible link text survives, the target does not
    assert "home" in out
    assert "http://x" not in out
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py::test_markdown_to_text_preserves_length_and_newlines -q`
Expected: FAIL with `AttributeError: module 'build.langcheck' has no attribute 'markdown_to_text'`

- [ ] **Step 3: Write the minimal implementation**

Add to `build/langcheck.py`:

```python
def _blank(m: "re.Match[str]") -> str:
    return " " * len(m.group())


_TABLE = re.compile(r"^[ \t]*\|.*$", re.M)
_FENCE = re.compile(r"^[ \t]*```.*$", re.M)
_HEAD = re.compile(r"^[ ]{0,3}#{1,6}[ ]", re.M)
_BLOCKQUOTE = re.compile(r"^[ ]{0,3}>[ ]?", re.M)
_BULLET = re.compile(r"^[ ]{0,3}([-*+]|\d+\.)[ ]", re.M)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_EMPH = re.compile(r"[*_`]")


def markdown_to_text(md: str) -> str:
    """Replace Markdown syntax with equal-length spaces, preserving length and
    every newline position, so a LanguageTool offset maps straight back to the
    source line and column."""
    out = _TABLE.sub(_blank, md)
    out = _FENCE.sub(_blank, out)
    out = _HEAD.sub(_blank, out)
    out = _BLOCKQUOTE.sub(_blank, out)
    out = _BULLET.sub(_blank, out)

    def _link(m: "re.Match[str]") -> str:
        text = m.group(1)
        # keep the visible text, blank the brackets and target; same total length
        return " " + text + " " * (len(m.group()) - len(text) - 1)

    out = _LINK.sub(_link, out)
    out = _EMPH.sub(" ", out)
    assert len(out) == len(md)
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add build/langcheck.py tests/test_langcheck.py
git commit -m "feat: offset-preserving Markdown strip for langcheck"
```

---

## Task 4: HTTP check_text with one retry

**Files:**
- Modify: `build/langcheck.py`
- Test: `tests/test_langcheck.py`

- [ ] **Step 1: Write the failing test**

```python
def test_check_text_returns_matches_and_retries_on_blank(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, fields):
        calls["n"] += 1
        assert url.endswith("/v2/check")
        assert fields["language"] == "pt-PT"
        if calls["n"] == 1:
            raise json.JSONDecodeError("empty", "", 0)  # the transient blank body
        return {"matches": [{"rule": {"id": "X"}, "offset": 0, "message": "m",
                             "replacements": [{"value": "y"}], "context": {"text": "t"}}]}

    import json
    monkeypatch.setattr(langcheck, "_post_json", fake_post)
    matches = langcheck.check_text("Os menino", "pt-PT", url="http://h:1")
    assert calls["n"] == 2  # retried once after the blank body
    assert matches[0]["rule"]["id"] == "X"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py::test_check_text_returns_matches_and_retries_on_blank -q`
Expected: FAIL with `AttributeError: ... has no attribute '_post_json'`

- [ ] **Step 3: Write the minimal implementation**

Add to `build/langcheck.py`:

```python
def _post_json(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_text(text: str, language: str, *, url: str = DEFAULT_URL) -> list[dict]:
    """POST text to the server's /v2/check and return its matches. Retries once
    on a blank or non-JSON body (the server can do that on a cold request)."""
    endpoint = url.rstrip("/") + "/v2/check"
    last_err: Exception | None = None
    for _ in range(2):
        try:
            payload = _post_json(endpoint, {"language": language, "text": text})
            return payload.get("matches", [])
        except (json.JSONDecodeError, ValueError) as exc:
            last_err = exc
    raise RuntimeError(f"LanguageTool returned no JSON from {endpoint}: {last_err}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add build/langcheck.py tests/test_langcheck.py
git commit -m "feat: langcheck HTTP check_text with one retry"
```

---

## Task 5: Line/column mapping and check_file

**Files:**
- Modify: `build/langcheck.py`
- Test: `tests/test_langcheck.py`

- [ ] **Step 1: Write the failing test**

```python
def test_check_file_maps_offsets_to_line_and_col(tmp_path, monkeypatch):
    md = "# Title\n\nOs menino vai.\n"
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "narration.simple.md"
    f.parent.mkdir(parents=True)
    f.write_text(md, encoding="utf-8")
    # offset of "menino" in the stripped text (heading blanked, same length as md)
    off = langcheck.markdown_to_text(md).index("menino")

    def fake_check_text(text, language, *, url):
        assert language == "pt-PT"
        return [{"rule": {"id": "AGREEMENT"}, "offset": off, "message": "concordancia",
                 "replacements": [{"value": "meninos"}], "context": {"text": "Os menino vai."}}]

    monkeypatch.setattr(langcheck, "check_text", fake_check_text)
    findings = langcheck.check_file(f, "pt-PT", url="http://h:1", root=tmp_path)
    assert len(findings) == 1
    fnd = findings[0]
    assert fnd.line == 3 and fnd.col == 4   # "menino" starts at column 4 of line 3
    assert fnd.rule_id == "AGREEMENT"
    assert fnd.suggestions == ("meninos",)
    assert fnd.file.endswith("narration.simple.md")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py::test_check_file_maps_offsets_to_line_and_col -q`
Expected: FAIL with `AttributeError: ... has no attribute 'check_file'`

- [ ] **Step 3: Write the minimal implementation**

Add to `build/langcheck.py`:

```python
def _line_col(text: str, offset: int) -> tuple[int, int]:
    head = text[:offset]
    line = head.count("\n") + 1
    col = offset - (head.rfind("\n") + 1) + 1
    return line, col


def check_file(path: Path, locale: str, *, url: str = DEFAULT_URL,
               root: Path | None = None) -> list[Finding]:
    language = LOCALE_LANGUAGE[locale]
    src = path.read_text(encoding="utf-8")
    plain = markdown_to_text(src)
    rel = str(path.relative_to(root)) if root else str(path)
    findings: list[Finding] = []
    for m in check_text(plain, language, url=url):
        line, col = _line_col(src, m["offset"])
        ctx = m.get("context", {}).get("text", "")
        reps = tuple(r["value"] for r in m.get("replacements", [])[:5])
        findings.append(Finding(rel, line, col, m["rule"]["id"], m["message"], ctx, reps))
    return findings


def check_locale(root: Path, locale: str, *, url: str = DEFAULT_URL,
                 files: list[Path] | None = None) -> list[Finding]:
    paths = files if files is not None else iter_locale_files(root, locale)
    out: list[Finding] = []
    for p in paths:
        out.extend(check_file(p, locale, url=url, root=root))
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add build/langcheck.py tests/test_langcheck.py
git commit -m "feat: langcheck line/column mapping and check_file/check_locale"
```

---

## Task 6: Wire the check-lang CLI subcommand

**Files:**
- Modify: `build/__main__.py`
- Test: `tests/test_langcheck.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_check_lang_prints_findings_and_exits_zero(tmp_path, monkeypatch, capsys):
    from build import __main__ as cli
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "rules.md"
    f.parent.mkdir(parents=True)
    f.write_text("Os menino vai.\n", encoding="utf-8")

    monkeypatch.setattr(
        "build.langcheck.check_text",
        lambda text, language, *, url: [
            {"rule": {"id": "AGREEMENT"}, "offset": 0, "message": "concordancia",
             "replacements": [{"value": "O menino"}], "context": {"text": "Os menino vai."}}
        ],
    )
    rc = cli.main(["check-lang", "--root", str(tmp_path), "--locale", "pt-PT"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "AGREEMENT" in out
    assert "1 candidate finding" in out


def test_cli_check_lang_exits_nonzero_when_server_unreachable(tmp_path, monkeypatch):
    from build import __main__ as cli
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "rules.md"
    f.parent.mkdir(parents=True)
    f.write_text("texto\n", encoding="utf-8")

    def boom(text, language, *, url):
        raise RuntimeError("no JSON")

    monkeypatch.setattr("build.langcheck.check_text", boom)
    rc = cli.main(["check-lang", "--root", str(tmp_path), "--locale", "pt-PT"])
    assert rc == 2
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -k cli -q`
Expected: FAIL (argparse exits 2 with "invalid choice: 'check-lang'")

- [ ] **Step 3: Add the import, the subparser, and the handler**

In `build/__main__.py`, add the locales import near the top:

```python
from build.locales import REQUIRED_LOCALES
```

Register the subparser (place it next to `generate-images`):

```python
    check_parser = sub.add_parser(
        "check-lang", help="check a locale's prose against a LanguageTool server"
    )
    _add_root(check_parser)
    check_parser.add_argument("--locale", required=True, choices=REQUIRED_LOCALES)
    check_parser.add_argument("--world", default=None)
    check_parser.add_argument("--story", default=None)
    check_parser.add_argument(
        "--url", default=None,
        help="LanguageTool base URL (default: $LANGUAGETOOL_URL or http://localhost:18010)",
    )
    check_parser.add_argument("paths", nargs="*", type=Path,
                              help="optional explicit Markdown files to check")
```

Add the handler block (before the final `return 2`):

```python
    if args.command == "check-lang":
        try:
            from dotenv import load_dotenv

            load_dotenv(args.root / ".env")
        except ImportError:
            pass

        from build import langcheck

        url = args.url or os.environ.get("LANGUAGETOOL_URL") or langcheck.DEFAULT_URL

        files = list(args.paths) or None
        if files is None and args.world:
            base = args.root / "worlds" / args.world
            if args.story:
                base = base / "stories" / args.story
            files = [p for p in base.rglob("*.md") if args.locale in p.parts]

        try:
            findings = langcheck.check_locale(args.root, args.locale, url=url, files=files)
        except (RuntimeError, OSError) as exc:
            print(f"could not reach LanguageTool at {url}: {exc}")
            return 2

        by_file: dict[str, list] = {}
        for fnd in findings:
            by_file.setdefault(fnd.file, []).append(fnd)
        for fname in sorted(by_file):
            print(f"\n## {fname}")
            for fnd in by_file[fname]:
                sug = ", ".join(fnd.suggestions) or "(no suggestion)"
                print(f"  {fnd.line}:{fnd.col} [{fnd.rule_id}] {fnd.message} -> {sug}")

        print(f"\n{len(findings)} candidate finding(s) for {args.locale}. "
              "Candidates, not auto-fixes;")
        print("read each in context and apply the locale-quality skill.")
        return 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_langcheck.py -q`
Expected: PASS (7 tests)

- [ ] **Step 5: Run the whole suite to confirm nothing else broke**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (all existing tests plus the 7 new ones)

- [ ] **Step 6: Commit**

```bash
git add build/__main__.py tests/test_langcheck.py
git commit -m "feat: build check-lang subcommand (shared LanguageTool check)"
```

---

## Task 7: Live smoke test against the Synology

**Files:** none (manual verification)

- [ ] **Step 1: Confirm the server is reachable and run a real check**

```bash
LANGUAGETOOL_URL=http://synologyds220p.duevite.eu:18010 \
  .venv/bin/python -m build check-lang --root . --locale pt-PT \
  --world floating-isles --story sleeping-garden
```

Expected: a grouped list of candidate findings (or "0 candidate finding(s)"), exit code 0. The canon names (for example invented place names) may appear as spelling candidates; that is expected and is what the future custom-dictionary mount or the judgment pass handles.

- [ ] **Step 2: Confirm the unreachable path is loud**

```bash
.venv/bin/python -m build check-lang --root . --locale pt-PT --url http://127.0.0.1:1
echo "exit: $?"
```

Expected: a "could not reach LanguageTool" line and `exit: 2`.

---

## Task 8: Wire check-lang into the pt-pt-quality skill

**Files:**
- Modify: `.claude/skills/pt-pt-quality/SKILL.md`

- [ ] **Step 1: Extend Pass 1 to run both finders**

Replace the `### Pass 1: scan` section so it runs `check-lang` next to `scan.sh`, and explain the split. The two finders cover different problems and do not overlap:

```markdown
### Pass 1: scan (two finders, different jobs)

Run both. They catch almost entirely different problems, so use them together.

```bash
# A. Project register, vocabulary, tone (things LanguageTool cannot see):
bash .claude/skills/pt-pt-quality/scan.sh                 # all pt-PT content
bash .claude/skills/pt-pt-quality/scan.sh worlds/<world>/stories/<story>/content/pt-PT/*.md

# B. Grammar, spelling, accents (things scan.sh cannot see), via the
#    self-hosted LanguageTool server (URL from .env: LANGUAGETOOL_URL):
.venv/bin/python -m build check-lang --root . --locale pt-PT
.venv/bin/python -m build check-lang --root . --locale pt-PT --world <world> --story <story>
```

`scan.sh` finds the archaic "vos" register, Brazilian gerunds, pt-BR vocabulary,
dashes, and no-lose tone slips. `check-lang` finds spelling, accent, and
agreement errors. Both are candidate finders, not auto-fixers; some false
positives are expected (canon names will show up as spelling candidates). The
judgment pass decides.
```

- [ ] **Step 2: Note the server in the skill so it is discoverable**

Add one line under `## Scope and siblings` (or near the scan section):

```markdown
The `check-lang` finder needs the self-hosted LanguageTool server reachable at
`$LANGUAGETOOL_URL` (see `.env.example`). If it is down, `check-lang` exits
non-zero and prints the URL it tried; `scan.sh` still runs without it.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/pt-pt-quality/SKILL.md
git commit -m "docs: pt-pt-quality Pass 1 also runs build check-lang"
```

---

## Task 9: Document self-hosting LanguageTool in the main README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a check-lang line to the developer command block**

In the `## For developers: the toolchain` code block, after the `generate-images`
line, add:

```bash
python -m build check-lang --root . --locale pt-PT          # check a locale against LanguageTool
```

- [ ] **Step 2: Add a short subsection explaining the optional server**

After the toolchain command block (before `### Where things live`), add a
subsection telling a contributor they can spin up their own LanguageTool and run
a check against it. It must state: the server is optional, it is self-hosted
(Docker), the URL comes from `LANGUAGETOOL_URL` in `.env`, and the check is a
candidate finder (strong for pt-PT and en-GB grammar, an accent net for es-ES and
it-IT) whose register judgement stays with the locale-quality skills. See Step 2
content in Task 9 of this plan body for the exact prose to paste.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README note on self-hosting LanguageTool for check-lang"
```

The prose to paste in Step 2:

```markdown
### Optional: check translations with LanguageTool

The locale-quality skills can cross-check prose against a self-hosted
[LanguageTool](https://languagetool.org) server (open-source, runs in Docker).
It is optional: nothing in the build needs it. To use it, run the server (for
example `docker run -d -p 18010:8010 erikvl87/languagetool`), set its URL in
`.env` as `LANGUAGETOOL_URL` (see `.env.example`), then:

```bash
python -m build check-lang --root . --locale pt-PT
python -m build check-lang --root . --locale es-ES --world floating-isles --story sleeping-garden
```

It prints candidate findings (spelling, accents, grammar) with line numbers and
exits 0; it exits non-zero only if the server cannot be reached. Treat the output
as candidates, not auto-fixes: coverage is strong for pt-PT and en-GB grammar and
a useful accent net for es-ES and it-IT, but regional register (peninsular
Spanish, European Portuguese, warm Italian) stays with the locale-quality skills
and a native reviewer.
```

---

## Task 10: Create the es-ES quality skill

**Files:**
- Create: `.claude/skills/es-es-quality/SKILL.md`
- Create: `.claude/skills/es-es-quality/references/es-es-guide.md`
- Create: `.claude/skills/es-es-quality/scan.sh`

- [ ] **Step 1: Write the Spanish register guide**

Model it on `references/pt-pt-guide.md`, but for peninsular Spanish. Sections:
register (vosotros for the group, tu for one child, address the grown-up as tu;
never address the players as ustedes, which is Latin-American or over-formal for
Spain); voseo is wrong (vos, tenes, queres); pt-style note removed; a
Latin-Americanism vocabulary table (coche not carro, ordenador not computadora,
movil not celular, zumo not jugo, patata not papa, coger/apanhar usage, vale not
okay, mola/guay not chevere/padre); seseo and yeismo spellings to avoid in
writing; the shared project rules (no losing: no derrota or perder as failure;
warmth; no dashes, ranges as "3 a 5"; canon names; plain words; associational
claims); a reviewer checklist.

- [ ] **Step 2: Write the scanner**

Copy `pt-pt-quality/scan.sh` and replace the pt-PT patterns with es-ES ones:
address-as-ustedes (`\bustedes\b`, `\busted\b`), voseo (`\b(vos|tenés|querés|sos|podés|hacés)\b`),
Latin-American vocabulary (`\b(carro|computadora|celular|jugo|papa|frijoles|chévere|padrísimo|ahorita|platicar|tomá|mirá)\b`),
dashes (`[\x{2013}\x{2014}]`), no-lose tone (`\b(derrota\w*|fracas\w+|perder|perdiste|perdéis|pierden)\b`).
Change the find default to `-path '*es-ES*'` and the closing pointer to the
es-es-guide. Keep it a candidate finder with the same false-positive caveat.

- [ ] **Step 3: Write SKILL.md**

Model on `pt-pt-quality/SKILL.md`. The description triggers on "check the
Spanish", "review es-ES", "is this peninsular Spanish", "fix the Spanish
register", "before publishing Spanish". Pass 1 runs both `scan.sh` and
`build check-lang --root . --locale es-ES`; Pass 2 is judgment against the guide.
Same "after fixing: validate, lint, pytest, rebuild in foreground" block. State
that LanguageTool covers Spanish spelling and accents but NOT peninsular register,
so the register call is this skill's job.

- [ ] **Step 4: Make the scanner executable and sanity-check it**

```bash
chmod +x .claude/skills/es-es-quality/scan.sh
bash .claude/skills/es-es-quality/scan.sh | tail -5
```

Expected: it runs and prints a candidate count (likely low), no shell error.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/es-es-quality
git commit -m "feat: es-ES quality skill (peninsular register guide + scanner + check-lang)"
```

---

## Task 11: Create the it-IT quality skill

**Files:**
- Create: `.claude/skills/it-it-quality/SKILL.md`
- Create: `.claude/skills/it-it-quality/references/it-it-guide.md`
- Create: `.claude/skills/it-it-quality/scan.sh`

- [ ] **Step 1: Write the Italian register guide**

Model on the pt-PT guide, for natural, warm Italian. Sections: register (address
the group of players as "voi"; one child as "tu"; the grown-up as "tu"; do NOT
use the formal "Lei" for players, it reads cold and bureaucratic); warmth (this is
the maintainer's stated preference: warm colloquial Italian over textbook
stiffness, reach for "coccole", "dolcezza", "tenero", "gentile"); avoid
anglicisms where a natural Italian word exists (gioco not "game", squadra not
"team"); the shared project rules (no losing: no "sconfitta", "perdere",
"fallimento" as failure, use "un'altra strada"; no dashes, ranges as "da 3 a 5";
canon names; plain words; associational claims); a reviewer checklist. Note that
LanguageTool's Italian is spelling and accents only, so this skill and a native
reviewer carry the grammar and register weight.

- [ ] **Step 2: Write the scanner**

Copy the scanner shape. it-IT patterns: formal-Lei addressing the players
(`\b(Lei|La vostra signoria)\b` is noisy, so scan for the polite imperative and
"Lei" pronoun carefully and mark as candidates), anglicisms
(`\b(game|team|level|player|score|win|loser)\b`), dashes (`[\x{2013}\x{2014}]`),
no-lose tone (`\b(sconfitt\w+|falliment\w+|perdere|perdi|perde|hai perso)\b`).
Change the find default to `-path '*it-IT*'`. Keep the candidate-finder framing;
Italian has more expected false positives, so lean on the judgment pass.

- [ ] **Step 3: Write SKILL.md**

Model on `pt-pt-quality/SKILL.md`. Triggers on "check the Italian", "review
it-IT", "is this natural Italian", "fix the Italian register", "before publishing
Italian". Pass 1 runs `scan.sh` and `build check-lang --root . --locale it-IT`;
Pass 2 is judgment against the guide. State plainly that LanguageTool's Italian is
thin (spelling and accents), so this skill plus native review carry grammar and
warmth.

- [ ] **Step 4: Make the scanner executable and sanity-check it**

```bash
chmod +x .claude/skills/it-it-quality/scan.sh
bash .claude/skills/it-it-quality/scan.sh | tail -5
```

Expected: runs and prints a candidate count, no shell error.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/it-it-quality
git commit -m "feat: it-IT quality skill (warm-register guide + scanner + check-lang)"
```

---

## Note on en-GB (no skill, by design)

en-GB does **not** get a quality skill. It is the canonical, human-authored source,
LanguageTool's English is the strongest of the four, and the only real risk
(Americanisms creeping in) is light. It is covered by the existing
`authoring-story-content` guidance, and `build check-lang --locale en-GB` still
works for a grammar pass. Promote en-GB to its own skill only if a recurring
problem actually emerges.

Shared principle across all locales: the mechanical layer (`check-lang`) is written
once and shared; only the small register guide is per locale. This keeps the skills
lean and prevents the LanguageTool URL and retry logic from being copied per
language.

---

## Self-Review

**Spec coverage:**
- Shared `check-lang` subcommand: Tasks 2 to 6.
- URL in `.env` plus committed `.env.example` documentation: Task 1.
- Per-locale routing (the `LOCALE_LANGUAGE` map, `--locale` choices): Tasks 2 and 6.
- Markdown handled so syntax is not flagged: Task 3.
- Transient-blip retry: Task 4.
- Candidate-not-gate behaviour and loud-on-unreachable: Task 6, verified in Task 7.
- pt-pt-quality skill wired to the shared finder: Task 8.
- Main README documents self-hosting LanguageTool and running a check: Task 9.
- es-ES quality skill (peninsular register guide, scanner, check-lang): Task 10.
- it-IT quality skill (warm register guide, scanner, check-lang): Task 11.
- en-GB intentionally gets no skill, with the reasoning recorded in its note.

**Placeholder scan:** No TODOs or vague steps; every code step shows complete code and every run step shows the exact command and expected result.

**Type consistency:** `Finding` is defined once (Task 2) and used unchanged in Tasks 5, 6, 8. `check_text` (Task 4) is called by `check_file` (Task 5) and monkeypatched by name in Tasks 5 and 6. `_post_json` (Task 4) is the single monkeypatch seam for the HTTP boundary. `LOCALE_LANGUAGE`, `DEFAULT_URL`, `iter_locale_files`, `check_locale` keep the same names across the CLI handler and tests.

**Open risk to watch during implementation:** the offset-preservation invariant in `markdown_to_text` is load-bearing for correct line numbers. The `assert len(out) == len(md)` guard catches any rule that changes length; if a future Markdown rule is added, keep that invariant.
