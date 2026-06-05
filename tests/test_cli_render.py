from build.__main__ import main

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/></svg>'
)


def test_render_builds_a_story_pack(sample_repo, tmp_path, capsys):
    code = main([
        "render", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--reading-level", "simple",
        "--out-dir", str(tmp_path),
    ])
    assert code == 0
    expected = tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "story-pack-simple-v0.0.pdf"
    assert expected.is_file()
    assert "story-pack-simple-v0.0.pdf" in capsys.readouterr().out


def test_render_guide_builds_under_guides_with_version(sample_repo, tmp_path):
    guide_dir = sample_repo / "guide" / "en-GB"
    guide_dir.mkdir(parents=True)
    (guide_dir / "guide.md").write_text("# Guide\n\nThree jobs.\n", encoding="utf-8")
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "guides" / "Guide_for_the_Grown-Up_en-GB-v0.0.pdf").is_file()


def test_render_guide_missing_markdown_returns_one(sample_repo, tmp_path):
    code = main([
        "render-guide", "--root", str(sample_repo),
        "--locale", "es-ES", "--out-dir", str(tmp_path),
    ])
    assert code == 1


def test_render_playbook_builds(sample_repo, tmp_path):
    from build.__main__ import main

    code = main([
        "render-playbook", "--root", str(sample_repo),
        "--world", "floating-isles", "--story", "sleeping-garden",
        "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (
        tmp_path / "en-GB" / "floating-isles" / "sleeping-garden" / "playbook-v0.0.pdf"
    ).is_file()


def test_render_world_builds(sample_repo, tmp_path):
    from build.__main__ import main

    code = main([
        "render-world", "--root", str(sample_repo),
        "--world", "floating-isles", "--locale", "en-GB", "--out-dir", str(tmp_path),
    ])
    assert code == 0
    assert (tmp_path / "en-GB" / "floating-isles" / "world-book-v0.0.pdf").is_file()


def test_rebuild_builds_the_library_and_rewrites_readme(sample_repo):
    from build.__main__ import main

    # the rebuild rewrites README.md between markers, so seed one
    (sample_repo / "README.md").write_text(
        "# Wander and Tales\n\n<!-- BEGIN KIT TABLE -->\nold\n<!-- END KIT TABLE -->\n\nEnd.\n",
        encoding="utf-8",
    )
    code = main(["rebuild", "--root", str(sample_repo), "--out-dir", str(sample_repo / "kits")])
    assert code == 0
    assert (
        sample_repo / "kits" / "en-GB" / "floating-isles" / "world-book-v0.0.pdf"
    ).is_file()
    readme = (sample_repo / "README.md").read_text(encoding="utf-8")
    assert "The Sleeping Garden" in readme
    assert "\nold\n" not in readme  # the seeded placeholder line was replaced
    assert "End." in readme
