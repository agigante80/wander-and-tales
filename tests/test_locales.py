from build import locales


def test_canonical_and_required_locales():
    assert locales.CANONICAL_LOCALE == "en-GB"
    assert locales.REQUIRED_LOCALES == ("en-GB", "es-ES", "it-IT")


def test_missing_locales_reports_absent_required_codes():
    mapping = {"en-GB": "The Sleeping Garden"}
    assert locales.missing_locales(mapping) == ("es-ES", "it-IT")


def test_missing_locales_empty_when_all_present():
    mapping = {"en-GB": "x", "es-ES": "y", "it-IT": "z"}
    assert locales.missing_locales(mapping) == ()
