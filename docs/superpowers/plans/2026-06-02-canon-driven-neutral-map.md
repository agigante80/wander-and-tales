# Canon-Driven Neutral Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Spanish-baked Sleeping Garden map with one locale-neutral SVG template whose labels are filled at render time from the story title, the canon place names in the kit's locale, and a few localized UI strings, so a single `map.svg` serves every language and en-GB kits gain a map.

**Architecture:** The map stays a self-contained SVG. Its text nodes become empty placeholders carrying a `data-label` key (and a `data-wrap` count for narrow stop labels). `build/render/map.py` gains a pure fill step (ElementTree) that writes localized text into those nodes (wrapping long names into centered `<tspan>`s) before the existing cairosvg render. The kit builds the labels dict generically from the template's keys, resolving `title` from the story, `stop:<canon-id>` from canon, and everything else from `map_*` UI strings. A plain SVG with no placeholders renders unchanged.

**Tech Stack:** Python 3.11+, `defusedxml` (hardened SVG parsing, guards against XXE and billion-laughs in any contributed map SVG) with `xml.etree.ElementTree` for building and serializing, cairosvg (render), the existing `build/render` pipeline, pytest. Adds `defusedxml` to the `render` optional extra.

---

## File structure

```
pyproject.toml             # MODIFIED: add defusedxml to the render extra
build/render/map.py        # MODIFIED: _wrap, fill_template, template_keys, render_map_template
build/render/strings.py    # MODIFIED: map_* UI strings (en-GB + es-ES)
build/render/kit.py        # MODIFIED: build map labels, route the map through render_map_template
worlds/floating-isles/stories/sleeping-garden/assets/map.svg        # NEW: neutral template
worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg  # DELETED
tests/test_render_map.py   # MODIFIED: _wrap, template_keys, fill, passthrough tests
tests/test_render_kit.py   # MODIFIED: neutral map serves en-GB and es-ES
docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md  # maps note
CLAUDE.md                  # maps bullet
```

`map.py` stays pure-SVG: it knows nothing about canon or strings. The kit owns content resolution. `_wrap` and `fill_template` are pure functions (no I/O), so they are unit-testable without rendering.

---

## Task 1: The word-wrap helper

**Files:**
- Modify: `build/render/map.py`
- Test: `tests/test_render_map.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_map.py`:

```python
def test_wrap_one_word_stays_one_line():
    assert kit_map._wrap("Mist", 2) == ["Mist"]


def test_wrap_two_words_split_one_each():
    assert kit_map._wrap("Vine Gate", 2) == ["Vine", "Gate"]


def test_wrap_four_words_balanced():
    assert kit_map._wrap("La Puerta de Enredaderas", 2) == ["La Puerta", "de Enredaderas"]


def test_wrap_max_one_returns_whole_text():
    assert kit_map._wrap("The Talking Fountain", 1) == ["The Talking Fountain"]
```

(`tests/test_render_map.py` already imports `from build.render import map as kit_map`.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -k wrap -v`
Expected: FAIL with `AttributeError: module 'build.render.map' has no attribute '_wrap'`.

- [ ] **Step 3: Implement the helper**

Add to `build/render/map.py` (after the imports):

```python
def _wrap(text: str, max_lines: int) -> list[str]:
    """Split text on spaces into at most max_lines balanced lines, preserving order.

    One word stays on one line; a two-word name splits one word per line; a longer
    name is balanced as evenly as possible. No word is ever dropped.
    """
    words = text.split()
    if max_lines <= 1 or len(words) <= 1:
        return [text] if text else []
    lines_wanted = min(max_lines, len(words))
    per = len(words) / lines_wanted
    lines: list[str] = []
    start = 0
    for index in range(lines_wanted):
        end = round((index + 1) * per)
        lines.append(" ".join(words[start:end]))
        start = end
    return [line for line in lines if line]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -k wrap -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build/render/map.py tests/test_render_map.py
git commit -m "feat: balanced word-wrap helper for map labels"
git push origin main
```
End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Task 2: Template keys, fill, and render

**Files:**
- Modify: `pyproject.toml`
- Modify: `build/render/map.py`
- Test: `tests/test_render_map.py`

- [ ] **Step 0: Add the defusedxml dependency and install it**

The map SVG is parsed with `defusedxml` so a contributed or third-party SVG cannot mount an XXE or billion-laughs attack on the build. In `pyproject.toml`, add `defusedxml>=0.7` to the existing `render` optional-dependency group (beside `reportlab`, `cairosvg`, `pypdf`):

```toml
render = [
    "reportlab>=4.0",
    "cairosvg>=2.7",
    "pypdf>=4.0",
    "defusedxml>=0.7",
]
```

Run:
```bash
.venv/bin/pip install -e ".[dev,render,images]"
```
Confirm: `.venv/bin/python -c "import defusedxml.ElementTree"` exits 0.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_map.py`:

```python
_TEMPLATE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="30" text-anchor="middle"></text>'
    '<text data-label="stop:gate" data-wrap="2" x="100" y="80" text-anchor="middle"></text>'
    "</svg>"
)


def test_template_keys_in_document_order(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TEMPLATE_SVG, encoding="utf-8")
    assert kit_map.template_keys(svg) == ["title", "stop:gate"]


def test_fill_substitutes_wraps_and_strips_data_attrs():
    out = kit_map.fill_template(
        _TEMPLATE_SVG, {"title": "El Jardín", "stop:gate": "La Puerta Verde"}
    )
    assert "El Jardín" in out  # accent preserved
    assert out.count("<tspan") == 2  # "La Puerta Verde" wrapped to two lines
    assert "data-label" not in out and "data-wrap" not in out


def test_fill_leaves_unkeyed_label_empty():
    out = kit_map.fill_template(_TEMPLATE_SVG, {"title": "Only Title"})
    assert "Only Title" in out


def test_render_map_template_writes_pdf(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TEMPLATE_SVG, encoding="utf-8")
    out = tmp_path / "map.pdf"
    result = kit_map.render_map_template(
        svg, out, {"title": "El Jardín", "stop:gate": "La Puerta Verde"}
    )
    assert result == out
    assert out.read_bytes().startswith(b"%PDF")


def test_render_map_template_passes_plain_svg_through(tmp_path):
    svg = tmp_path / "plain.svg"
    svg.write_text(_TINY_SVG, encoding="utf-8")  # no data-label nodes
    out = tmp_path / "plain.pdf"
    kit_map.render_map_template(svg, out, {})
    assert out.read_bytes().startswith(b"%PDF")
```

(`_TINY_SVG` is already defined at the top of `tests/test_render_map.py`.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -k "template or fill or render_map" -v`
Expected: FAIL with `AttributeError: module 'build.render.map' has no attribute 'template_keys'`.

- [ ] **Step 3: Implement the fill and render functions**

Add to `build/render/map.py`. Add these two imports at the top (stdlib `ElementTree` is used only to build and serialize; all PARSING goes through `defusedxml`, which returns standard `Element` objects so the rest of the API is unchanged):

```python
import xml.etree.ElementTree as ET

import defusedxml.ElementTree as DefusedET
```

Then add:

```python
_SVG_NS = "http://www.w3.org/2000/svg"
_LINE_DY = 15  # vertical gap between wrapped label lines, in SVG user units


def template_keys(svg_path: Path) -> list[str]:
    """Return every data-label value in the template, in document order."""
    root = DefusedET.parse(svg_path).getroot()
    return [
        element.get("data-label")
        for element in root.iter()
        if element.get("data-label") is not None
    ]


def fill_template(svg_text: str, labels: dict[str, str]) -> str:
    """Write localized text into the data-label placeholders and return the SVG.

    A node with data-wrap="N" has its text balanced into up to N centered tspans.
    The data-label and data-wrap attributes are stripped from the output. Nodes
    without a data-label are left untouched, so a plain SVG comes back unchanged.

    Parsing uses defusedxml so a malicious contributed SVG cannot mount an XXE or
    entity-expansion attack; building and serializing use the stdlib ElementTree.
    """
    ET.register_namespace("", _SVG_NS)
    root = DefusedET.fromstring(svg_text)
    for element in root.iter():
        key = element.get("data-label")
        if key is None:
            continue
        text = labels.get(key, "")
        wrap = element.get("data-wrap")
        element.text = None
        for child in list(element):
            element.remove(child)
        if wrap:
            x = element.get("x", "0")
            for index, line in enumerate(_wrap(text, int(wrap))):
                tspan = ET.SubElement(element, f"{{{_SVG_NS}}}tspan")
                tspan.set("x", x)
                tspan.set("dy", "0" if index == 0 else str(_LINE_DY))
                tspan.text = line
        else:
            element.text = text
        for attribute in ("data-label", "data-wrap"):
            element.attrib.pop(attribute, None)
    return ET.tostring(root, encoding="unicode")


def render_map_template(svg_path: Path, out_path: Path, labels: dict[str, str]) -> Path:
    """Fill a template SVG with localized labels and render it to a one-page PDF."""
    filled = fill_template(svg_path.read_text(encoding="utf-8"), labels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(bytestring=filled.encode("utf-8"), write_to=str(out_path))
    return out_path
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_map.py -v`
Expected: PASS (all map tests, including Task 1's).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml build/render/map.py tests/test_render_map.py
git commit -m "feat: fill data-label map templates and render them to PDF"
git push origin main
```
End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Task 3: Map UI strings

**Files:**
- Modify: `build/render/strings.py`
- Test: `tests/test_render_strings.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_strings.py`:

```python
def test_map_strings_present_in_both_locales():
    for locale in ("en-GB", "es-ES"):
        for key in (
            "map_subtitle", "map_start", "map_hint_start", "map_goal",
            "map_legend_title", "map_legend_a1", "map_legend_a2",
            "map_legend_b1", "map_legend_b2", "map_legend_foot",
        ):
            assert strings.ui(locale, key)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_strings.py -k map -v`
Expected: FAIL with `KeyError`.

- [ ] **Step 3: Add the strings**

In `build/render/strings.py`, add these entries to the `en-GB` dict and the `es-ES` dict inside `UI` (keep all existing keys). Add to `en-GB`:

```python
        "map_subtitle": "A magical adventure map",
        "map_start": "START",
        "map_hint_start": "Begin here",
        "map_goal": "GOAL",
        "map_legend_title": "How to use the map",
        "map_legend_a1": "Put a small figure on each white",
        "map_legend_a2": "circle (that is you).",
        "map_legend_b1": "The golden path leads you from",
        "map_legend_b2": "1 to 4, solving each puzzle.",
        "map_legend_foot": "Build the objects from bricks.",
```

Add to `es-ES` (peninsular Spanish, full accents, vosotros):

```python
        "map_subtitle": "Un mapa de aventura mágica",
        "map_start": "SALIDA",
        "map_hint_start": "Empezáis aquí",
        "map_goal": "META",
        "map_legend_title": "Cómo usar el mapa",
        "map_legend_a1": "Pon una figura en cada círculo",
        "map_legend_a2": "blanco (sois vosotros).",
        "map_legend_b1": "El camino dorado os lleva del",
        "map_legend_b2": "1 al 4 resolviendo cada puzle.",
        "map_legend_foot": "Construid los objetos con piezas.",
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_strings.py -v`
Expected: PASS (the new test and the existing balance test `test_every_required_locale_has_every_key`).

- [ ] **Step 5: Commit**

```bash
git add build/render/strings.py tests/test_render_strings.py
git commit -m "feat: localised UI strings for the map labels"
git push origin main
```
End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Task 4: Author the neutral template SVG

**Files:**
- Create: `worlds/floating-isles/stories/sleeping-garden/assets/map.svg`
- Delete: `worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg`

- [ ] **Step 1: Write the neutral template**

Create `worlds/floating-isles/stories/sleeping-garden/assets/map.svg` with exactly this content (the original art, number badges and heart kept; every Spanish text replaced by a `data-label` placeholder; root font set to DejaVu Sans):

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794" font-family="DejaVu Sans">
  <defs>
    <radialGradient id="sky" cx="50%" cy="0%" r="120%">
      <stop offset="0%" stop-color="#fef9ef"/>
      <stop offset="60%" stop-color="#eaf7e1"/>
      <stop offset="100%" stop-color="#d8efce"/>
    </radialGradient>
    <linearGradient id="banner" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7bc96f"/>
      <stop offset="100%" stop-color="#4ea24a"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#3a5a32" flood-opacity="0.25"/>
    </filter>
  </defs>

  <rect width="1123" height="794" fill="url(#sky)"/>
  <rect x="14" y="14" width="1095" height="766" rx="26" fill="none" stroke="#9ccf8a" stroke-width="6" stroke-dasharray="2 14" stroke-linecap="round"/>

  <circle cx="120" cy="120" r="46" fill="#ffd95e"/>
  <g stroke="#ffd95e" stroke-width="7" stroke-linecap="round">
    <line x1="120" y1="46" x2="120" y2="22"/>
    <line x1="120" y1="194" x2="120" y2="218"/>
    <line x1="46" y1="120" x2="22" y2="120"/>
    <line x1="194" y1="120" x2="218" y2="120"/>
    <line x1="68" y1="68" x2="50" y2="50"/>
    <line x1="172" y1="68" x2="190" y2="50"/>
    <line x1="68" y1="172" x2="50" y2="190"/>
  </g>

  <g fill="#ffffff" opacity="0.9">
    <ellipse cx="880" cy="90" rx="60" ry="26"/>
    <ellipse cx="920" cy="78" rx="44" ry="24"/>
    <ellipse cx="845" cy="78" rx="38" ry="22"/>
  </g>

  <path d="M 150 700 C 320 660, 300 540, 360 470 S 560 430, 620 330 S 760 280, 840 200 S 980 170, 1000 120"
        fill="none" stroke="#e9d8a6" stroke-width="58" stroke-linecap="round" filter="url(#soft)"/>
  <path d="M 150 700 C 320 660, 300 540, 360 470 S 560 430, 620 330 S 760 280, 840 200 S 980 170, 1000 120"
        fill="none" stroke="#f7ecc9" stroke-width="40" stroke-linecap="round" stroke-dasharray="4 26"/>

  <g filter="url(#soft)">
    <rect x="245" y="300" width="16" height="40" rx="6" fill="#9c6b3f"/>
    <circle cx="253" cy="285" r="40" fill="#6fbf73"/>
    <circle cx="230" cy="300" r="28" fill="#82cf86"/>
    <circle cx="278" cy="302" r="26" fill="#5fb463"/>
  </g>
  <g filter="url(#soft)">
    <rect x="700" y="560" width="16" height="40" rx="6" fill="#9c6b3f"/>
    <circle cx="708" cy="545" r="38" fill="#6fbf73"/>
    <circle cx="686" cy="560" r="26" fill="#82cf86"/>
    <circle cx="732" cy="560" r="24" fill="#5fb463"/>
  </g>
  <g filter="url(#soft)">
    <rect x="930" y="430" width="14" height="34" rx="6" fill="#9c6b3f"/>
    <circle cx="937" cy="418" r="32" fill="#6fbf73"/>
    <circle cx="918" cy="430" r="22" fill="#82cf86"/>
  </g>

  <g>
    <g transform="translate(470,620)"><circle r="9" fill="#ff8fb1"/><circle r="4" fill="#fff3b0"/></g>
    <g transform="translate(520,650)"><circle r="8" fill="#b18cff"/><circle r="3.5" fill="#fff3b0"/></g>
    <g transform="translate(820,420)"><circle r="9" fill="#ff8fb1"/><circle r="4" fill="#fff3b0"/></g>
    <g transform="translate(150,400)"><circle r="8" fill="#7ec8ff"/><circle r="3.5" fill="#fff3b0"/></g>
    <g transform="translate(960,300)"><circle r="8" fill="#ff8fb1"/><circle r="3.5" fill="#fff3b0"/></g>
  </g>

  <g filter="url(#soft)">
    <rect x="300" y="30" width="520" height="74" rx="20" fill="url(#banner)"/>
    <text data-label="title" x="560" y="68" text-anchor="middle" font-size="34" fill="#ffffff" font-weight="bold"></text>
    <text data-label="subtitle" x="560" y="93" text-anchor="middle" font-size="16" fill="#eaffe0"></text>
  </g>

  <g filter="url(#soft)">
    <circle cx="150" cy="700" r="46" fill="#ffffff" stroke="#4ea24a" stroke-width="6"/>
    <text data-label="stop:start" x="150" y="694" text-anchor="middle" font-size="20" font-weight="bold" fill="#4ea24a"></text>
    <text data-label="hint:start" x="150" y="716" text-anchor="middle" font-size="13" fill="#5a7a52"></text>
  </g>

  <g filter="url(#soft)">
    <circle cx="360" cy="470" r="50" fill="#ffffff" stroke="#2bb3a3" stroke-width="6"/>
    <circle cx="360" cy="455" r="22" fill="#2bb3a3"/>
    <text x="360" y="463" text-anchor="middle" font-size="22" font-weight="bold" fill="#ffffff">1</text>
    <text data-label="stop:vine-gate" data-wrap="2" x="360" y="500" text-anchor="middle" font-size="13" fill="#1f7d72" font-weight="bold"></text>
  </g>

  <g filter="url(#soft)">
    <circle cx="620" cy="330" r="50" fill="#ffffff" stroke="#d36fb0" stroke-width="6"/>
    <circle cx="620" cy="315" r="22" fill="#d36fb0"/>
    <text x="620" y="323" text-anchor="middle" font-size="22" font-weight="bold" fill="#ffffff">2</text>
    <text data-label="stop:flower-bed" data-wrap="2" x="620" y="360" text-anchor="middle" font-size="13" fill="#a33d83" font-weight="bold"></text>
  </g>

  <g filter="url(#soft)">
    <circle cx="840" cy="200" r="50" fill="#ffffff" stroke="#3f8fd6" stroke-width="6"/>
    <circle cx="840" cy="185" r="22" fill="#3f8fd6"/>
    <text x="840" y="193" text-anchor="middle" font-size="22" font-weight="bold" fill="#ffffff">3</text>
    <text data-label="stop:talking-fountain" data-wrap="2" x="840" y="230" text-anchor="middle" font-size="13" fill="#2b6aa3" font-weight="bold"></text>
  </g>

  <g filter="url(#soft)">
    <circle cx="1000" cy="120" r="54" fill="#fff7e0" stroke="#f2a93b" stroke-width="7"/>
    <path d="M 1000 138 l -20 -20 a 12 12 0 1 1 20 -8 a 12 12 0 1 1 20 8 z" fill="#f2843b"/>
    <text data-label="stop:garden-heart" data-wrap="2" x="1000" y="190" text-anchor="middle" font-size="13" fill="#c2641f" font-weight="bold"></text>
    <text data-label="goal" x="1000" y="222" text-anchor="middle" font-size="12" fill="#c2641f" font-weight="bold"></text>
  </g>

  <g filter="url(#soft)">
    <rect x="40" y="500" width="250" height="150" rx="16" fill="#ffffff" opacity="0.96"/>
    <text data-label="legend:title" x="60" y="528" font-size="17" font-weight="bold" fill="#4ea24a"></text>
    <circle cx="68" cy="552" r="8" fill="#ffd95e" stroke="#4ea24a" stroke-width="2"/>
    <text data-label="legend:a1" x="86" y="557" font-size="13" fill="#3a5a32"></text>
    <text data-label="legend:a2" x="86" y="573" font-size="13" fill="#3a5a32"></text>
    <circle cx="68" cy="596" r="8" fill="#e9d8a6"/>
    <text data-label="legend:b1" x="86" y="601" font-size="13" fill="#3a5a32"></text>
    <text data-label="legend:b2" x="86" y="617" font-size="13" fill="#3a5a32"></text>
    <text data-label="legend:foot" x="60" y="640" font-size="12" fill="#7a9a6f"></text>
  </g>
</svg>
```

- [ ] **Step 2: Delete the Spanish-only map**

```bash
git rm worlds/floating-isles/stories/sleeping-garden/assets/map.es-ES.svg
```

- [ ] **Step 3: Verify the template parses and exposes the expected keys**

Run:
```bash
.venv/bin/python -c "
from pathlib import Path
from build.render import map as kit_map
keys = kit_map.template_keys(Path('worlds/floating-isles/stories/sleeping-garden/assets/map.svg'))
print(keys)
assert keys == ['title','subtitle','stop:start','hint:start','stop:vine-gate','stop:flower-bed','stop:talking-fountain','stop:garden-heart','goal','legend:title','legend:a1','legend:a2','legend:b1','legend:b2','legend:foot'], keys
print('OK', len(keys), 'keys')
"
```
Expected: prints the 15 keys and `OK 15 keys`.

- [ ] **Step 4: Confirm the test suite still passes**

Run: `.venv/bin/python -m pytest -q`
Expected: green (this task adds an asset and removes one; nothing should break yet because the kit still calls the old path until Task 5).

- [ ] **Step 5: Commit**

```bash
git add worlds/floating-isles/stories/sleeping-garden/assets/map.svg
git commit -m "content: neutral data-label map template for the Sleeping Garden"
git push origin main
```
(The `git rm` from Step 2 is already staged.) End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Task 5: Wire the kit to fill the map per locale

**Files:**
- Modify: `build/render/kit.py`
- Test: `tests/test_render_kit.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_kit.py` (it already imports `from pypdf import PdfReader` and `from build.render import kit`):

```python
_NEUTRAL_MAP = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="20" text-anchor="middle"></text>'
    '<text data-label="subtitle" x="100" y="40" text-anchor="middle"></text>'
    '<text data-label="stop:start" x="40" y="100" text-anchor="middle"></text>'
    '<text data-label="stop:mist-cat" data-wrap="2" x="150" y="100" text-anchor="middle"></text>'
    "</svg>"
)


def test_neutral_map_serves_en_gb_and_es_es(sample_repo, tmp_path):
    # Baseline: en-GB with no map yet.
    en_nomap = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path / "a",
    )
    base = len(PdfReader(str(en_nomap)).pages)

    assets = (
        sample_repo / "worlds" / "floating-isles"
        / "stories" / "sleeping-garden" / "assets"
    )
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_NEUTRAL_MAP, encoding="utf-8")

    en = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "en-GB", "simple",
        out_dir=tmp_path / "b",
    )
    es = kit.build_kit(
        sample_repo, "floating-isles", "sleeping-garden", "es-ES", "simple",
        out_dir=tmp_path / "c",
    )
    # The neutral template now adds a map page for BOTH locales (en-GB no longer omitted).
    assert len(PdfReader(str(en)).pages) == base + 1
    assert len(PdfReader(str(es)).pages) == base + 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -k neutral_map -v`
Expected: FAIL: the kit still calls `render_svg_to_pdf` on the template, so the placeholders render empty (the page count may still be base+1, but the kit does not yet build labels; more importantly the test pins the new behaviour). If it happens to pass on page count alone, proceed to Step 3 anyway to implement the label-filling path, then re-run.

- [ ] **Step 3: Implement the kit label-building and route through render_map_template**

In `build/render/kit.py`, add `strings` to the render imports. The existing import line is:

```python
from build.render import fonts, glossary, map as kit_map, pages, sheets, theme
```

Change it to:

```python
from build.render import fonts, glossary, map as kit_map, pages, sheets, strings, theme
```

Add this module-level helper (after the `_PROSE_PAGES` constant near the top):

```python
def _map_label(key: str, story, canon_by_id: dict, locale: str) -> str:
    """Resolve one map data-label key to its localized text.

    `title` comes from the story; `stop:<id>` from canon when <id> is a canon id,
    otherwise from a `map_<id>` UI string (this covers `stop:start`); any other key
    maps to a `map_<key>` UI string (colons and hyphens become underscores).
    """
    if key == "title":
        return story.title.get(locale, story.id)
    if key.startswith("stop:"):
        canon_id = key[len("stop:"):]
        entry = canon_by_id.get(canon_id)
        if entry is not None:
            return entry.names.get(locale, canon_id)
        return strings.ui(locale, "map_" + canon_id)
    return strings.ui(locale, "map_" + key.replace(":", "_").replace("-", "_"))
```

In `build_kit`, locate where canon is loaded and the map is rendered. The story, canon and locale are already available. Find this block:

```python
        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            parts.append(kit_map.render_svg_to_pdf(map_svg, tmp_path / "00_map.pdf"))
```

Replace it with:

```python
        map_svg = kit_map.find_map(world_dir, story_dir, locale)
        if map_svg is not None:
            canon_by_id = {entry.id: entry for entry in canon}
            labels = {
                key: _map_label(key, story, canon_by_id, locale)
                for key in kit_map.template_keys(map_svg)
            }
            parts.append(
                kit_map.render_map_template(map_svg, tmp_path / "00_map.pdf", labels)
            )
```

(`canon` is the list returned by `content.load_canon` already loaded earlier in `build_kit`; this builds the id index locally. If `build_kit` already defines a `canon_by_id`, reuse it instead of rebuilding.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_render_kit.py -v`
Expected: PASS (the new test and the existing kit tests; the existing `test_build_kit_writes_one_merged_pdf` and `test_kit_uses_a_locale_specific_story_map` use plain SVG maps with no `data-label`, which still render through `render_map_template` unchanged).

- [ ] **Step 5: Run the whole suite**

Run: `.venv/bin/python -m pytest -q`
Expected: green.

- [ ] **Step 6: Commit**

```bash
git add build/render/kit.py tests/test_render_kit.py
git commit -m "feat: fill the neutral map per locale in the kit build"
git push origin main
```
End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Task 6: Build the real kits, eyeball, and update docs

**Files:**
- Modify: `docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Build the real Sleeping Garden kits and rasterize the map page**

Run:
```bash
.venv/bin/python -c "
from pathlib import Path
from build.render import kit
from pypdf import PdfReader
for locale in ('en-GB', 'es-ES'):
    out = kit.build_kit(Path('.'), 'floating-isles', 'sleeping-garden', locale, 'simple')
    print(locale, len(PdfReader(str(out)).pages), 'pages', out.name)
"
pdftoppm -png -r 90 -f 1 -l 1 dist/floating-isles_sleeping-garden_en-GB_simple.pdf dist/_map_en
pdftoppm -png -r 90 -f 1 -l 1 dist/floating-isles_sleeping-garden_es-ES_simple.pdf dist/_map_es
ls dist/_map_*.png
```
Expected: both kits build, both now report a map page (en-GB included). Open `dist/_map_en-1.png` and `dist/_map_es-1.png`: confirm the English map reads "The Sleeping Garden", "START / Begin here", "The Vine Gate", "The Flower Bed", "The Talking Fountain", "The Heart of the Garden", "GOAL", and the English legend; the Spanish map reads "El Jardín Dormido", "SALIDA / Empezáis aquí", the Spanish stop names with accents, "META", and the Spanish legend. Confirm the wrapped two-line stop names sit inside their circles and the layout holds.

- [ ] **Step 2: Clean up the preview PNGs**

```bash
rm -f dist/_map_en-1.png dist/_map_es-1.png
```
(`dist/` is gitignored, so nothing is committed here.)

- [ ] **Step 3: Update the maps note in the main spec**

In `docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md`, find the build-pipeline note about maps (the paragraph beginning "Maps come in two kinds and may be per-locale"). Append to it:

```markdown
A map may instead be a neutral template: the art and number badges stay
locale-neutral and the text labels are placeholders (`data-label` keys) filled at
render time from the story title, the canon place names in the locale, and a few
`map_*` UI strings. One `map.svg` then serves every locale, which is the preferred
form. The Sleeping Garden uses this, so en-GB and es-ES both render the same board
with their own labels. Per-locale `map.<locale>.svg` files remain supported for art
that must be hand-localized.
```

- [ ] **Step 4: Update the maps bullet in CLAUDE.md**

In `CLAUDE.md`, in the Architecture bullet that begins "Maps are world-level or story-level", append:

```markdown
A map may also be a neutral template: text becomes `data-label` placeholders that
`map.py:render_map_template` fills per locale from the story title, canon names, and
`map_*` UI strings, so one `map.svg` serves every language. The Sleeping Garden uses
this (its old `map.es-ES.svg` is gone), so en-GB kits now include the map too.
```

- [ ] **Step 5: Run the suite once more**

Run: `.venv/bin/python -m pytest -q`
Expected: green.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-06-01-floating-isles-story-kit-library-design.md CLAUDE.md
git commit -m "docs: document the canon-driven neutral map"
git push origin main
```
End the commit message with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` on its own line (heredoc).

---

## Self-review

**Spec coverage:**
- Neutral template SVG with data-label placeholders and data-wrap: Task 4. Covered.
- `template_keys`, `fill_template`, `render_map_template`, `_wrap`, backward-compatible passthrough: Tasks 1 and 2. Covered.
- Map UI strings (en-GB + es-ES): Task 3. Covered.
- Kit builds labels generically (title from story, stop:<id> from canon with UI fallback, others from map_* strings) and routes the map through `render_map_template`; en-GB gains the map: Task 5. Covered.
- Delete `map.es-ES.svg`: Task 4 Step 2. Covered.
- Docs (spec maps note, CLAUDE.md): Task 6. Covered. Real-kit eyeball: Task 6 Step 1.

**Placeholder scan:** every code step contains complete, runnable code and the full template SVG. No TODOs. The one manual judgement (eyeballing the rasterized maps) is an explicit verification step, not a code gap.

**Type and name consistency:** `map._wrap(text, max_lines) -> list[str]`, `map.template_keys(svg_path) -> list[str]`, `map.fill_template(svg_text, labels) -> str`, `map.render_map_template(svg_path, out_path, labels) -> Path` (used by name in `kit.build_kit`); `kit._map_label(key, story, canon_by_id, locale) -> str`; the `data-label` key set authored in Task 4 matches the resolution rule in Task 5 (`title`, `stop:<canon-id>`, `stop:start`, `hint:start`, `goal`, `subtitle`, `legend:*`) and the `map_*` string names added in Task 3 (`map_subtitle`, `map_start`, `map_hint_start`, `map_goal`, `map_legend_title`, `map_legend_a1/a2/b1/b2/foot`). The four canon stop ids (`vine-gate`, `flower-bed`, `talking-fountain`, `garden-heart`) all exist in `worlds/floating-isles/canon/`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-canon-driven-neutral-map.md`.

Two execution options:

1. **Subagent-Driven (recommended):** a fresh subagent per task, with two-stage review between tasks.
2. **Inline Execution:** execute the tasks in this session with checkpoints.

Which approach?
