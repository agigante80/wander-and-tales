"""Embed declared images into kit pages as scaled reportlab flowables.

Three placements: a cover page (the story cover plus the title), a "story in
pictures" gallery (each scene image with its localized caption), and small
portraits beside their canon entries in the glossary. This module only builds
flowables; the kit decides which image files exist and passes them in.
"""

import io
from pathlib import Path

from PIL import Image as PILImage, ImageDraw
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage, Paragraph, Spacer

from build.render import markdown as md

CONTENT_WIDTH = 210 * mm - 36 * mm  # A4 width minus the page margins
_COVER_MAX_HEIGHT = 222 * mm
_FRONT_COVER_MAX_HEIGHT = 170 * mm  # leaves room above for the title and paragraph
_SCENE_MAX_HEIGHT = 115 * mm
_PORTRAIT_SIZE = 34 * mm

# The largest pixel dimension we embed. A full A4-width image at 200 DPI is about
# 1370 px, so 1400 keeps print quality while letting us recompress the source art
# (multi-megabyte watercolour PNGs) to small JPEGs, keeping kit PDFs a few MB
# rather than tens of MB.
_MAX_EMBED_PX = 1400
_JPEG_QUALITY = 82


def _embed_jpeg(path: Path, corner_radius: float = 0.0) -> tuple[io.BytesIO, int, int]:
    """Downscale to a print-sane size and recompress to JPEG for a small PDF.

    Returns the JPEG buffer and its pixel width and height. When `corner_radius` (a
    fraction of the shorter side) is set, the corners are filled white so the picture
    reads as rounded against the white page.
    """
    with PILImage.open(path) as opened:
        if opened.mode in ("RGBA", "LA", "P"):
            # Flatten any transparency onto white so transparent areas print white,
            # not whatever colour sat hidden beneath the alpha.
            rgba = opened.convert("RGBA")
            flat = PILImage.new("RGBA", rgba.size, (255, 255, 255, 255))
            image = PILImage.alpha_composite(flat, rgba).convert("RGB")
        else:
            image = opened.convert("RGB")
        image.thumbnail((_MAX_EMBED_PX, _MAX_EMBED_PX))
        width, height = image.size
        if corner_radius > 0:
            radius = int(min(width, height) * corner_radius)
            mask = PILImage.new("L", (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, width - 1, height - 1], radius=radius, fill=255
            )
            page = PILImage.new("RGB", (width, height), (255, 255, 255))
            image = PILImage.composite(image, page, mask)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=_JPEG_QUALITY)
    buffer.seek(0)
    return buffer, width, height


def rounded_reader(path: Path) -> tuple[ImageReader, int, int]:
    """An ImageReader of the recompressed image with whitened rounded corners, plus
    its pixel size, for chrome.RoundedImage."""
    buffer, width, height = _embed_jpeg(path, corner_radius=0.045)
    return ImageReader(buffer), width, height


def image_reader(path: Path) -> ImageReader:
    """A reportlab ImageReader of the recompressed, print-sized image, for canvas
    drawImage calls (so canvas-drawn art like the hero portrait stays as small in the
    PDF as the flowable art does, not the multi-megabyte source PNG)."""
    buffer, _width, _height = _embed_jpeg(path)
    return ImageReader(buffer)


def image_flowable(path: Path, max_width: float, max_height: float) -> RLImage:
    """A reportlab Image scaled to fit within the box, preserving aspect ratio.

    The source is recompressed to a print-sized JPEG so kit PDFs stay small.
    """
    buffer, iw, ih = _embed_jpeg(path)
    scale = min(max_width / iw, max_height / ih)
    img = RLImage(buffer, width=iw * scale, height=ih * scale)
    img.hAlign = "CENTER"
    return img


def cover_flowables(cover_path: Path, title: str, styles: dict) -> list:
    """Title banner plus the large cover image, for the kit's front page."""
    return [
        Paragraph(md.inline_to_rl(title), styles["h1"]),
        Spacer(1, 10),
        image_flowable(cover_path, CONTENT_WIDTH, _COVER_MAX_HEIGHT),
    ]


def frontpage_flowables(
    title: str, world_paragraph: str, cover_path: Path | None, styles: dict,
    *, kicker: str = "", theme=None,
) -> list:
    """The always-on front page: a header band (kicker + title + motif), a short world
    paragraph, and the optional cover as a rounded illustration.

    The cover image is omitted cleanly when there is no art, so a story with no cover
    still opens with its title and the world paragraph.
    """
    from build.render import chrome  # lazy: avoids a chrome <-> images import cycle

    if theme is not None:
        flows: list = [chrome.HeaderBand(kicker, title, theme)]
    else:
        flows = [Paragraph(md.inline_to_rl(title), styles["h1"])]
    if world_paragraph:
        flows.append(Spacer(1, 6))
        flows.append(Paragraph(md.inline_to_rl(world_paragraph), styles["body"]))
    if cover_path is not None:
        flows.append(Spacer(1, 10))
        if theme is not None:
            flows.append(chrome.RoundedImage(cover_path, theme, max_h=_FRONT_COVER_MAX_HEIGHT))
        else:
            flows.append(image_flowable(cover_path, CONTENT_WIDTH, _FRONT_COVER_MAX_HEIGHT))
    return flows


def scene_flowable(path: Path) -> RLImage:
    """A scene illustration scaled to the kit's standard scene size."""
    return image_flowable(path, CONTENT_WIDTH, _SCENE_MAX_HEIGHT)


def gallery_flowables(title: str, scenes: list, styles: dict) -> list:
    """A story-in-pictures page: each scene image with a localized caption.

    `scenes` is a list of (path, caption) pairs in story order.
    """
    flows: list = [Paragraph(md.inline_to_rl(title), styles["h1"])]
    for path, caption in scenes:
        flows.append(Spacer(1, 8))
        flows.append(scene_flowable(path))
        if caption:
            flows.append(Paragraph(md.inline_to_rl(caption), styles["body"]))
    return flows


def portrait_flowable(path: Path) -> RLImage:
    """A small square portrait image for the glossary."""
    return image_flowable(path, _PORTRAIT_SIZE, _PORTRAIT_SIZE)
