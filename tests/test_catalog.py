from build import catalog, content


def test_catalog_lists_story_with_tags(sample_repo):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    markdown = catalog.build_catalog_markdown(stories)
    assert "| World | Title | Age | Skills | Peril | Dice | Players | Time |" in markdown
    assert "floating-isles" in markdown
    assert "The Sleeping Garden" in markdown
    assert "gentle" in markdown
    assert "30 min" in markdown


def test_write_catalog_creates_file(sample_repo, tmp_path):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    out = tmp_path / "catalog.md"
    catalog.write_catalog(stories, out)
    assert out.read_text(encoding="utf-8").startswith("# Catalog")
