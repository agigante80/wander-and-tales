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
    span: str
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


def _post_json(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Blanking Markdown to equal-length spaces (to preserve offsets) leaves stray
# spaces where headings, bullets, table rows, and emphasis markers were, which
# trips the whitespace and punctuation-spacing rules (an emphasis marker next to
# a comma or colon leaves "palabra ," or "Voce :"). That noise is an artifact of
# our stripping, not the prose, so disable that whole family by default.
DEFAULT_DISABLED_RULES = (
    "WHITESPACE_RULE,COMMA_PARENTHESIS_WHITESPACE,INCORRECT_SPACES,WHITESPACE_PUNCTUATION"
    ",SPACE_BEFORE_PUNCTUATION2,ESPACO_DUPLO"
)


def check_text(text: str, language: str, *, url: str = DEFAULT_URL,
               disabled_rules: str = DEFAULT_DISABLED_RULES) -> list[dict]:
    """POST text to the server's /v2/check and return its matches. Retries once
    on a blank or non-JSON body (the server can do that on a cold request)."""
    endpoint = url.rstrip("/") + "/v2/check"
    fields = {"language": language, "text": text}
    if disabled_rules:
        fields["disabledRules"] = disabled_rules
    last_err: Exception | None = None
    for _ in range(2):
        try:
            payload = _post_json(endpoint, fields)
            return payload.get("matches", [])
        except (json.JSONDecodeError, ValueError) as exc:
            last_err = exc
    raise RuntimeError(f"LanguageTool returned no JSON from {endpoint}: {last_err}")


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
        ctx = m.get("context", {})
        ctext = ctx.get("text", "")
        coff, clen = ctx.get("offset", 0), ctx.get("length", 0)
        span = ctext[coff:coff + clen] if clen else ""
        reps = tuple(r["value"] for r in m.get("replacements", [])[:5])
        findings.append(Finding(rel, line, col, m["rule"]["id"], m["message"], ctext, span, reps))
    return findings


def check_locale(root: Path, locale: str, *, url: str = DEFAULT_URL,
                 files: list[Path] | None = None) -> list[Finding]:
    paths = files if files is not None else iter_locale_files(root, locale)
    out: list[Finding] = []
    for p in paths:
        out.extend(check_file(p, locale, url=url, root=root))
    return out
