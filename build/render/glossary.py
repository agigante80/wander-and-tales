"""Build the who's-who glossary appendix straight from canon entries.

Generated, never hand-written, so it cannot drift from the world bible. Entries
are grouped by kind in a fixed order and printed with the locale name and
(optional) description.
"""

from reportlab.platypus import Paragraph

from build.models import CanonEntry
from build.render import markdown as md
from build.render import strings
from build.render.theme import Theme

_KIND_ORDER = ("place", "character", "creature", "item", "term")
_KIND_LABEL = {
    "place": "group_place",
    "character": "group_character",
    "creature": "group_creature",
    "item": "group_item",
    "term": "group_term",
}


def glossary_flowables(
    entries: list[CanonEntry], locale: str, styles: dict, theme: Theme
) -> list:
    """Return flowables for a glossary page: a title, then a group per kind."""
    flows: list = [Paragraph(strings.ui(locale, "glossary_title"), styles["h1"])]
    for kind in _KIND_ORDER:
        group = [e for e in entries if e.kind == kind]
        if not group:
            continue
        flows.append(Paragraph(strings.ui(locale, _KIND_LABEL[kind]), styles["h2"]))
        for entry in sorted(group, key=lambda e: e.names[locale]):
            name = entry.names[locale]
            desc = (entry.description or {}).get(locale, "")
            line = f"**{name}**" + (f" - {desc}" if desc else "")
            flows.append(Paragraph(md.inline_to_rl(line), styles["body"]))
    return flows
