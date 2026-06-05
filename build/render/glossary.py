"""Build the who's-who glossary appendix straight from canon entries.

Generated, never hand-written, so it cannot drift from the world bible. Entries
are grouped by kind in a fixed order and printed with the locale name and
(optional) description.
"""

from pathlib import Path

from reportlab.platypus import Paragraph, Spacer

from build.models import CanonEntry
from build.render import images, markdown as md
from build.render import strings
from build.render.theme import Theme

# Hero qualities (or magics) come first: they are what a player picks on the sheet.
_KIND_ORDER = ("quality", "place", "character", "creature", "item", "term")
_KIND_LABEL = {
    "place": "group_place",
    "character": "group_character",
    "creature": "group_creature",
    "item": "group_item",
    "term": "group_term",
}


def glossary_flowables(
    entries: list[CanonEntry],
    locale: str,
    styles: dict,
    theme: Theme,
    portrait_paths: dict[str, Path] | None = None,
    hero_powers: str = "magic",
) -> list:
    """Return flowables for a glossary page: a title, then a group per kind.

    The hero qualities (or magics) get their own clearly-labelled group at the top,
    with a one-line note that these are what a player chooses on the adventure sheet, so
    a reader is never left guessing what the list is for. When `portrait_paths` maps a
    canon id to an image file, a small portrait is placed above that entry.
    """
    portrait_paths = portrait_paths or {}
    flows: list = [Paragraph(strings.ui(locale, "glossary_title"), styles["h1"])]
    for kind in _KIND_ORDER:
        group = [e for e in entries if e.kind == kind]
        if not group:
            continue
        if kind == "quality":
            label_key = "group_magics" if hero_powers == "magic" else "group_strengths"
            flows.append(Paragraph(strings.ui(locale, label_key), styles["h2"]))
            flows.append(Paragraph(
                md.inline_to_rl(strings.ui(locale, "glossary_quality_lead")),
                styles["body"],
            ))
        else:
            flows.append(Paragraph(strings.ui(locale, _KIND_LABEL[kind]), styles["h2"]))
        for entry in sorted(group, key=lambda e: e.names[locale]):
            if entry.id in portrait_paths:
                flows.append(Spacer(1, 4))
                flows.append(images.portrait_flowable(portrait_paths[entry.id]))
            name = entry.names[locale]
            desc = (entry.description or {}).get(locale, "")
            line = f"**{name}**" + (f" - {desc}" if desc else "")
            flows.append(Paragraph(md.inline_to_rl(line), styles["body"]))
    return flows
