import json
from pathlib import Path

from build import langcheck
from build.locales import REQUIRED_LOCALES


def test_locale_language_map_covers_required_locales():
    for loc in REQUIRED_LOCALES:
        assert loc in langcheck.LOCALE_LANGUAGE
    assert langcheck.LOCALE_LANGUAGE["pt-PT"] == "pt-PT"
    assert langcheck.LOCALE_LANGUAGE["es-ES"] == "es"
    assert langcheck.LOCALE_LANGUAGE["it-IT"] == "it"
    assert langcheck.LOCALE_LANGUAGE["en-GB"] == "en-GB"


def test_iter_locale_files_finds_pt_pt_by_path_segment(tmp_path: Path):
    f1 = tmp_path / "worlds" / "w" / "stories" / "s" / "content" / "pt-PT" / "rules.md"
    f2 = tmp_path / "worlds" / "w" / "stories" / "s" / "content" / "es-ES" / "rules.md"
    f3 = tmp_path / "guide" / "pt-PT" / "guide.md"
    for f in (f1, f2, f3):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x", encoding="utf-8")
    found = langcheck.iter_locale_files(tmp_path, "pt-PT")
    assert f1 in found and f3 in found
    assert f2 not in found


def test_markdown_to_text_preserves_length_and_newlines():
    md = "# Stop 1: The Gate\n\nThe *cat* walks to [home](http://x).\n\n| a | b |\n"
    out = langcheck.markdown_to_text(md)
    assert len(out) == len(md)
    # newline positions identical, so line numbers map straight back
    assert [i for i, c in enumerate(out) if c == "\n"] == [i for i, c in enumerate(md) if c == "\n"]
    # heading marker and emphasis markers are gone (blanked), prose survives
    assert "Stop 1: The Gate" in out
    assert "cat" in out
    assert "#" not in out and "*" not in out
    # the table row is blanked to spaces
    assert "a | b" not in out
    # the visible link text survives, the target does not
    assert "home" in out
    assert "http://x" not in out


def test_check_text_returns_matches_and_retries_on_blank(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, fields):
        calls["n"] += 1
        assert url.endswith("/v2/check")
        assert fields["language"] == "pt-PT"
        if calls["n"] == 1:
            raise json.JSONDecodeError("empty", "", 0)  # the transient blank body
        return {"matches": [{"rule": {"id": "X"}, "offset": 0, "message": "m",
                             "replacements": [{"value": "y"}], "context": {"text": "t"}}]}

    monkeypatch.setattr(langcheck, "_post_json", fake_post)
    matches = langcheck.check_text("Os menino", "pt-PT", url="http://h:1")
    assert calls["n"] == 2  # retried once after the blank body
    assert matches[0]["rule"]["id"] == "X"


def test_check_file_maps_offsets_to_line_and_col(tmp_path, monkeypatch):
    md = "# Title\n\nOs menino vai.\n"
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "narration.simple.md"
    f.parent.mkdir(parents=True)
    f.write_text(md, encoding="utf-8")
    # offset of "menino" in the stripped text (heading blanked, same length as md)
    off = langcheck.markdown_to_text(md).index("menino")

    def fake_check_text(text, language, *, url):
        assert language == "pt-PT"
        return [{"rule": {"id": "AGREEMENT"}, "offset": off, "message": "concordancia",
                 "replacements": [{"value": "meninos"}], "context": {"text": "Os menino vai."}}]

    monkeypatch.setattr(langcheck, "check_text", fake_check_text)
    findings = langcheck.check_file(f, "pt-PT", url="http://h:1", root=tmp_path)
    assert len(findings) == 1
    fnd = findings[0]
    assert fnd.line == 3 and fnd.col == 4   # "menino" starts at column 4 of line 3
    assert fnd.rule_id == "AGREEMENT"
    assert fnd.suggestions == ("meninos",)
    assert fnd.file.endswith("narration.simple.md")


def test_cli_check_lang_prints_findings_and_exits_zero(tmp_path, monkeypatch, capsys):
    from build import __main__ as cli
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "rules.md"
    f.parent.mkdir(parents=True)
    f.write_text("Os menino vai.\n", encoding="utf-8")

    monkeypatch.setattr(
        "build.langcheck.check_text",
        lambda text, language, *, url: [
            {"rule": {"id": "AGREEMENT"}, "offset": 0, "message": "concordancia",
             "replacements": [{"value": "O menino"}], "context": {"text": "Os menino vai."}}
        ],
    )
    rc = cli.main(["check-lang", "--root", str(tmp_path), "--locale", "pt-PT"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "AGREEMENT" in out
    assert "1 candidate finding" in out


def test_cli_check_lang_exits_nonzero_when_server_unreachable(tmp_path, monkeypatch):
    from build import __main__ as cli
    f = tmp_path / "worlds" / "w" / "content" / "pt-PT" / "rules.md"
    f.parent.mkdir(parents=True)
    f.write_text("texto\n", encoding="utf-8")

    def boom(text, language, *, url):
        raise RuntimeError("no JSON")

    monkeypatch.setattr("build.langcheck.check_text", boom)
    rc = cli.main(["check-lang", "--root", str(tmp_path), "--locale", "pt-PT"])
    assert rc == 2
