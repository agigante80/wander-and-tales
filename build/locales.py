"""Locale codes. British English is canonical; Spanish from Spain and Italian are synced.

US English, Latin American Spanish, and other locales are separate languages
added later, each keyed by its own explicit code (like pt-PT versus pt-BR).
"""

from collections.abc import Mapping

CANONICAL_LOCALE = "en-GB"
SYNCED_LOCALES = ("es-ES", "it-IT")
REQUIRED_LOCALES = (CANONICAL_LOCALE, *SYNCED_LOCALES)


def missing_locales(mapping: Mapping[str, object]) -> tuple[str, ...]:
    """Return the required locale codes absent (or blank) in a per-locale map."""
    return tuple(
        code
        for code in REQUIRED_LOCALES
        if not str(mapping.get(code, "")).strip()
    )
