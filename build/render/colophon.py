"""The colophon end page: project link, content licence, version, and a QR code.

A printed kit is frozen at its printed version, so the QR links to the artifact's
GitHub directory, which always shows the newest versioned file. The QR image and the
URLs are locale-neutral; only the surrounding words are localized.
"""

import io

import segno
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, Paragraph, Spacer

from build.render import markdown as md, strings
from build.render.version import VersionInfo

PROJECT_URL = "https://github.com/agigante80/wander-and-tales"
LICENCE_CODE = "CC BY-SA 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
_QR_SIZE = 30 * mm


def _qr_image(url: str) -> RLImage:
    buffer = io.BytesIO()
    segno.make(url, error="m").save(buffer, kind="png", scale=8, border=1)
    buffer.seek(0)
    return RLImage(buffer, width=_QR_SIZE, height=_QR_SIZE)


def colophon_flowables(
    styles: dict,
    locale: str,
    version_info: VersionInfo,
    artifact_label: str,
    qr_url: str,
) -> list:
    """Flowables for the single colophon page at the end of every artifact."""
    licence = strings.ui(locale, "colophon_licence").format(
        code=LICENCE_CODE, url=LICENCE_URL
    )
    version_line = strings.ui(locale, "colophon_version").format(
        number=f"{version_info.major}.{version_info.minor}",
        updated=version_info.updated,
        locale=locale,
    )
    return [
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_project")), styles["h1"]),
        Spacer(1, 12),
        Paragraph(md.inline_to_rl(artifact_label), styles["h2"]),
        Spacer(1, 6),
        Paragraph(md.inline_to_rl(PROJECT_URL), styles["body"]),
        Paragraph(md.inline_to_rl(licence), styles["body"]),
        Paragraph(md.inline_to_rl(version_line), styles["body"]),
        Spacer(1, 16),
        _qr_image(qr_url),
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_qr_caption")), styles["body"]),
        Spacer(1, 16),
        Paragraph(md.inline_to_rl(strings.ui(locale, "colophon_promise")), styles["body"]),
    ]
