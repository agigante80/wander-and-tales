"""Shared helpers for assembling kit PDFs: merge page parts, resolve an image file, and
localize a hand-drawn map's data-labels. Used by the Tale Book and Atlas builders.

(This module once built the Story Pack; the kit is now a Tale Book plus an Atlas, so
only these small shared helpers remain here.)
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build.render import strings


def _image_file(assets_dir: Path, image_id: str) -> Path | None:
    path = assets_dir / f"{image_id}.png"
    return path if path.is_file() else None


def _map_label(key: str, story, canon_by_id: dict, locale: str) -> str:
    if key == "title":
        return story.title.get(locale, story.id)
    if key.startswith("stop:"):
        canon_id = key[len("stop:"):]
        entry = canon_by_id.get(canon_id)
        if entry is not None:
            return entry.names.get(locale, canon_id)
        return strings.ui(locale, "map_" + canon_id)
    return strings.ui(locale, "map_" + key.replace(":", "_").replace("-", "_"))


def _merge(parts: list[Path], out_path: Path) -> Path:
    writer = PdfWriter()
    for part in parts:
        for page in PdfReader(str(part)).pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        writer.write(handle)
    return out_path
