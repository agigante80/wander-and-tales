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
    assert info.number == 2
    assert info.updated.count("-") == 2  # YYYY-MM-DD
    assert info.dirty is False
    assert info.label == "v2"


def test_version_with_no_history_is_unreleased(tmp_path):
    _init_repo(tmp_path)
    info = version.version_info(tmp_path, [tmp_path / "missing.txt"])
    assert info.number == 0
    assert info.updated == "unreleased"
    assert info.label == "v0"


def test_version_marks_a_dirty_input(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "a.txt"
    _commit(tmp_path, f, "one", "first")
    f.write_text("uncommitted change", encoding="utf-8")
    info = version.version_info(tmp_path, [f])
    assert info.number == 1
    assert info.dirty is True
    assert info.label == "v1+"


def test_story_pack_inputs_lists_the_right_paths(tmp_path):
    paths = version.story_pack_inputs(tmp_path, "w", "s", "en-GB", "simple")
    names = {p.name for p in paths}
    assert "story.yaml" in names
    assert "narration.simple.md" in names
    assert "world.yaml" in names
