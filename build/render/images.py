"""Embed declared images into kit pages as scaled reportlab flowables.

Three placements: a cover page (the story cover plus the title), a "story in
pictures" gallery (each scene image with its localized caption), and small
portraits beside their canon entries in the glossary. This module only builds
flowables; the kit decides which image files exist and passes them in.
"""

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage, Paragraph, Spacer

from build.render import markdown as md

CONTENT_WIDTH = 210 * mm - 36 * mm  # A4 width minus the page margins
_COVER_MAX_HEIGHT = 222 * mm
_SCENE_MAX_HEIGHT = 115 * mm
_PORTRAIT_SIZE = 34 * mm


def image_flowable(path: Path, max_width: float, max_height: float) -> RLImage:
    """A reportlab Image scaled to fit within the box, preserving aspect ratio."""
    iw, ih = ImageReader(str(path)).getSize()
    scale = min(max_width / iw, max_height / ih)
    img = RLImage(str(path), width=iw * scale, height=ih * scale)
    img.hAlign = "CENTER"
    return img


def cover_flowables(cover_path: Path, title: str, styles: dict) -> list:
    """Title banner plus the large cover image, for the kit's front page."""
    return [
        Paragraph(md.inline_to_rl(title), styles["h1"]),
        Spacer(1, 10),
        image_flowable(cover_path, CONTENT_WIDTH, _COVER_MAX_HEIGHT),
    ]


def gallery_flowables(title: str, scenes: list, styles: dict) -> list:
    """A story-in-pictures page: each scene image with a localized caption.

    `scenes` is a list of (path, caption) pairs in story order.
    """
    flows: list = [Paragraph(md.inline_to_rl(title), styles["h1"])]
    for path, caption in scenes:
        flows.append(Spacer(1, 8))
        flows.append(image_flowable(path, CONTENT_WIDTH, _SCENE_MAX_HEIGHT))
        if caption:
            flows.append(Paragraph(md.inline_to_rl(caption), styles["body"]))
    return flows


def portrait_flowable(path: Path) -> RLImage:
    """A small square portrait image for the glossary."""
    return image_flowable(path, _PORTRAIT_SIZE, _PORTRAIT_SIZE)
