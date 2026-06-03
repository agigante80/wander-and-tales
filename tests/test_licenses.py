from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_code_licence_is_mit():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "Wits and Wonder" in text


def test_content_licence_is_cc_by_sa():
    text = (ROOT / "LICENSE-CONTENT").read_text(encoding="utf-8")
    assert "CC BY-SA 4.0" in text
    assert "creativecommons.org/licenses/by-sa/4.0" in text
