"""DEFERRED path-scoped spelling lint (en-GB and es-ES only).

Seam only. The rule set (American spellings inside en-GB, Latin American turns
of phrase inside es-ES) is implemented in a later plan once locale content
exists. `check_text` returns no findings today so callers can wire it in safely.
"""

from pathlib import Path

_SCOPED_LOCALES = ("en-GB", "es-ES", "it-IT", "pt-PT")


def locale_for_path(path: Path) -> str | None:
    """Return the scoped locale if this path is inside one, else None."""
    parts = path.parts
    for code in _SCOPED_LOCALES:
        if code in parts:
            return code
    return None


def check_text(text: str, locale: str) -> list[str]:
    """Return human-readable findings. Deferred: always empty for now."""
    return []
