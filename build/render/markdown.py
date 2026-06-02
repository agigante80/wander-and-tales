"""Parse the constrained GitHub-flavoured markdown used by kit content.

Pure and dependency-free. It recognises ATX headings, blank-line-separated
paragraphs, '-' or '*' bullet lists (with wrapped continuation lines), and GFM
pipe tables. Inline markup (**bold**, *italic*) is preserved as raw text and
converted to reportlab markup later, in inline_to_rl.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")
_TABLE_DIVIDER = re.compile(r"^\s*\|?\s*:?-{1,}.*$")


@dataclass(frozen=True)
class Heading:
    level: int
    text: str


@dataclass(frozen=True)
class Para:
    text: str


@dataclass(frozen=True)
class Bullets:
    items: list[str]


@dataclass(frozen=True)
class Table:
    headers: list[str]
    rows: list[list[str]]


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _is_block_start(line: str) -> bool:
    return (
        _is_blank(line)
        or _HEADING.match(line) is not None
        or _BULLET.match(line) is not None
        or line.lstrip().startswith("|")
    )


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_markdown(text: str) -> list:
    """Return an ordered list of Heading, Para, Bullets and Table blocks."""
    lines = text.split("\n")
    blocks: list = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            blocks.append(Heading(len(heading.group(1)), heading.group(2).strip()))
            i += 1
            continue

        if (
            line.lstrip().startswith("|")
            and i + 1 < n
            and _TABLE_DIVIDER.match(lines[i + 1])
        ):
            headers = _split_row(line)
            i += 2  # skip header and divider
            rows: list[list[str]] = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            blocks.append(Table(headers, rows))
            continue

        bullet = _BULLET.match(line)
        if bullet:
            items: list[str] = [bullet.group(1).strip()]
            i += 1
            while i < n and not _is_block_start(lines[i]):
                items[-1] = f"{items[-1]} {lines[i].strip()}"
                i += 1
            while i < n and _BULLET.match(lines[i]):
                items.append(_BULLET.match(lines[i]).group(1).strip())
                i += 1
                while i < n and not _is_block_start(lines[i]):
                    items[-1] = f"{items[-1]} {lines[i].strip()}"
                    i += 1
            blocks.append(Bullets(items))
            continue

        para = [line.strip()]
        i += 1
        while i < n and not _is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(Para(" ".join(para)))
    return blocks
