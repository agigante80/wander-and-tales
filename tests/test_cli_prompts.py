from build.__main__ import main


def test_prompts_prints_all(repo_with_images, capsys):
    code = main(["prompts", "--root", str(repo_with_images)])
    assert code == 0
    out = capsys.readouterr().out
    assert "# Image prompts" in out
    assert "w / cover" in out and "s / scene-1" in out


def test_prompts_writes_a_file(repo_with_images, tmp_path):
    out = tmp_path / "prompts.md"
    code = main(["prompts", "--root", str(repo_with_images), "--out", str(out)])
    assert code == 0
    assert out.read_text(encoding="utf-8").startswith("# Image prompts")


def test_prompts_filters_to_a_story(repo_with_images, capsys):
    code = main([
        "prompts", "--root", str(repo_with_images), "--world", "w", "--story", "s",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "s / cover" in out
    assert "## World: w" not in out  # world-level images excluded
