from build.__main__ import main

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def test_render_builds_a_kit(sample_repo, tmp_path, capsys):
    assets = sample_repo / "worlds" / "floating-isles" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "map.svg").write_text(_TINY_SVG, encoding="utf-8")
    code = main([
        "render", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--reading-level", "simple",
        "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert "floating-isles_sleeping-garden_en-GB_simple.pdf" in capsys.readouterr().out
    assert (tmp_path / "floating-isles_sleeping-garden_en-GB_simple.pdf").is_file()


def test_render_guide_builds_under_guides_with_version(sample_repo, tmp_path):
    guide_dir = sample_repo / "guide" / "en-GB"
    guide_dir.mkdir(parents=True)
    (guide_dir / "guide.md").write_text("# Guide\n\nThree jobs.\n", encoding="utf-8")
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "guides" / "Guide_for_the_Grown-Up_en-GB-v0.pdf").is_file()


def test_render_guide_missing_markdown_returns_one(sample_repo, tmp_path):
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "es-ES", "--out-dir", str(tmp_path),
    ])
    assert code == 1
