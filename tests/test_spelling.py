from pathlib import Path

from build import spelling


def test_only_scopes_known_locale_folders():
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/en-GB/rules.md")) == "en-GB"
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/es-ES/rules.md")) == "es-ES"
    assert spelling.locale_for_path(Path("worlds/w/stories/s/content/en-US/rules.md")) is None
    assert spelling.locale_for_path(Path("README.md")) is None


def test_check_text_is_a_noop_stub_for_now():
    # Deferred: no rules implemented yet, so nothing is flagged.
    assert spelling.check_text("The colour of autumn.", "en-GB") == []
