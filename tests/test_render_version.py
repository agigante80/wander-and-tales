import subprocess
from pathlib import Path

from build.render import version


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "Test")


def _commit(root: Path, path: Path, text: str, message: str) -> None:
    path.write_text(text, encoding="utf-8")
    _git(root, "add", str(path.relative_to(root)))
    _git(root, "commit", "-m", message)


def test_version_counts_commits_and_dates(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "a.txt"
    _commit(tmp_path, f, "one", "first")
    _commit(tmp_path, f, "two", "second")
    info = version.version_info(tmp_path, [f])
    assert info.major == 2
    assert info.minor == 0
    assert info.updated.count("-") == 2  # YYYY-MM-DD
    assert info.dirty is False
    assert info.label == "v2.0"


def test_version_with_no_history_is_unreleased(tmp_path):
    _init_repo(tmp_path)
    info = version.version_info(tmp_path, [tmp_path / "missing.txt"])
    assert info.major == 0
    assert info.minor == 0
    assert info.updated == "unreleased"
    assert info.label == "v0.0"


def test_version_marks_a_dirty_input(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "a.txt"
    _commit(tmp_path, f, "one", "first")
    f.write_text("uncommitted change", encoding="utf-8")
    info = version.version_info(tmp_path, [f])
    assert info.major == 1
    assert info.dirty is True
    assert info.label == "v1.0+"


def test_minor_counts_render_commits_since_the_last_content_edition(tmp_path):
    # MINOR tracks layout/render commits made after the content's last commit, and a
    # fresh content edition resets it, the way major.minor reads.
    _init_repo(tmp_path)
    content = tmp_path / "story.yaml"
    render = tmp_path / "layout.py"
    _commit(tmp_path, content, "v1", "content: first edition")
    info = version.version_info(tmp_path, [content], [render])
    assert info.label == "v1.0"  # no layout commits yet
    _commit(tmp_path, render, "a", "layout: tweak one")
    _commit(tmp_path, render, "b", "layout: tweak two")
    info = version.version_info(tmp_path, [content], [render])
    assert (info.major, info.minor) == (1, 2)
    assert info.label == "v1.2"
    _commit(tmp_path, content, "v2", "content: second edition")
    info = version.version_info(tmp_path, [content], [render])
    assert info.label == "v2.0"  # the new edition resets the layout counter


def test_story_pack_inputs_lists_the_right_paths(tmp_path):
    paths = version.story_pack_inputs(tmp_path, "w", "s", "en-GB", "simple")
    names = {p.name for p in paths}
    assert "story.yaml" in names
    assert "narration.simple.md" in names
    assert "world.yaml" in names


def test_story_pack_inputs_are_isolated_per_locale_and_level(tmp_path):
    # The en-GB simple pack must not be coupled to other locales, levels, or the
    # grown-up content, or its version would move when those change.
    paths = {str(p) for p in version.story_pack_inputs(tmp_path, "w", "s", "en-GB", "simple")}
    assert not any("es-ES" in p for p in paths)
    assert not any(p.endswith("narration.rich.md") for p in paths)
    assert not any(p.endswith(("rules.md", "puzzles.md", "idea-bank.md")) for p in paths)
    # It must not pass a bare assets directory (that over-couples to all art).
    assert not any(p.endswith("assets") for p in paths)


def test_world_book_inputs_scope(sample_repo):
    paths = {str(p) for p in version.world_book_inputs(sample_repo, "floating-isles", "en-GB")}
    assert any(p.endswith("narration.simple.md") and "en-GB" in p for p in paths)
    assert any(p.endswith("story.yaml") for p in paths)
    assert any(p.endswith("idea-bank.md") for p in paths)
    assert not any(p.endswith(("rules.md", "puzzles.md", "narration.rich.md")) for p in paths)
    assert not any("es-ES" in p for p in paths)
    assert not any(p.endswith("stories") for p in paths)
