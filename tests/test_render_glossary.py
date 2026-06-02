from reportlab.platypus import Paragraph

from build.models import CanonEntry
from build.render import fonts, glossary, theme


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def _entries():
    return [
        CanonEntry.model_validate(
            {"id": "great-garden", "kind": "place",
             "names": {"en-GB": "The Great Garden", "es-ES": "El Gran Jardin"},
             "description": {"en-GB": "The green heart of the island.",
                             "es-ES": "El corazon verde de la isla."}}
        ),
        CanonEntry.model_validate(
            {"id": "mist-cat", "kind": "creature",
             "names": {"en-GB": "Mist Cat", "es-ES": "Gato de Niebla"},
             "description": {"en-GB": "A gentle cat made of fog.",
                             "es-ES": "Un gato amable hecho de niebla."}}
        ),
    ]


def test_glossary_titles_and_names_appear_for_locale():
    flows = glossary.glossary_flowables(_entries(), "en-GB", _styles(), theme.Theme.default())
    text = " ".join(f.text for f in flows if isinstance(f, Paragraph))
    assert "Who's Who" in text
    assert "Places" in text and "Creatures" in text
    assert "The Great Garden" in text and "green heart" in text


def test_glossary_uses_the_requested_locale():
    flows = glossary.glossary_flowables(_entries(), "es-ES", _styles(), theme.Theme.default())
    text = " ".join(f.text for f in flows if isinstance(f, Paragraph))
    assert "El Gran Jardin" in text and "Gato de Niebla" in text
