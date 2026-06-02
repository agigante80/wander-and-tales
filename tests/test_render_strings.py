import pytest

from build.locales import REQUIRED_LOCALES
from build.render import strings


def test_every_required_locale_has_every_key():
    keys = set(strings.UI["en-GB"])
    for locale in REQUIRED_LOCALES:
        assert set(strings.UI[locale]) == keys, locale


def test_ui_returns_text_and_raises_on_unknown_key():
    assert strings.ui("en-GB", "glossary_title")
    assert strings.ui("es-ES", "glossary_title")
    with pytest.raises(KeyError):
        strings.ui("en-GB", "no_such_key")
