import pytest

from build import fontspec


def test_known_families_include_sans_and_serif():
    assert "dejavu-sans" in fontspec.KNOWN_FAMILIES
    assert "dejavu-serif" in fontspec.KNOWN_FAMILIES
    assert fontspec.DEFAULT_FAMILY == "dejavu-sans"


def test_faces_for_returns_four_existing_files():
    faces = fontspec.faces_for("dejavu-serif")
    for filename in (faces.normal, faces.bold, faces.italic, faces.bold_italic):
        assert fontspec.font_path(filename).is_file()


def test_faces_for_unknown_family_raises():
    with pytest.raises(KeyError):
        fontspec.faces_for("papyrus")
