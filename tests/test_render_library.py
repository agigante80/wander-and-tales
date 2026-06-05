from build.render import library


def test_build_all_creates_every_artifact(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    story_dir = out_dir / "en-GB" / "floating-isles" / "sleeping-garden"
    assert (story_dir / "floating-isles-sleeping-garden-tale-book-simple-en-GB-v0.0.pdf").is_file()
    assert (story_dir / "floating-isles-sleeping-garden-atlas-en-GB-v0.0.pdf").is_file()
    assert (out_dir / "en-GB" / "floating-isles" / "floating-isles-world-book-en-GB-v0.0.pdf").is_file()
    assert ("floating-isles", "sleeping-garden", "es-ES", "rich") in built.tale_books


def test_prune_removes_superseded_versions(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    story_dir = out_dir / "en-GB" / "floating-isles" / "sleeping-garden"
    stale = story_dir / "floating-isles-sleeping-garden-tale-book-simple-en-GB-v9.9.pdf"
    stale.write_bytes(b"%PDF-stale")
    removed = library.prune_old(out_dir, built)
    assert stale in removed
    assert not stale.exists()
    # the current version survives
    assert (story_dir / "floating-isles-sleeping-garden-tale-book-simple-en-GB-v0.0.pdf").is_file()


def test_readme_block_lists_stories_and_links(sample_repo):
    out_dir = sample_repo / "kits"
    built = library.build_all(sample_repo, out_dir)
    block = library.readme_block(sample_repo, built)
    assert library.README_BEGIN in block
    assert library.README_END in block
    assert "The Sleeping Garden" in block
    assert "floating-isles-sleeping-garden-tale-book-simple-en-GB-v0.0.pdf" in block
    assert "floating-isles-sleeping-garden-atlas-en-GB-v0.0.pdf" in block
    # the catalogue is grouped per world, each with its World Book links
    assert "### The Floating Isles" in block
    assert "**World Book:**" in block
    # one column per language in the per-world table header
    assert "| English | Español | Italiano |" in block


def test_apply_readme_block_replaces_only_between_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# Title\n\nIntro.\n\n{library.README_BEGIN}\nold\n{library.README_END}\n\nFooter.\n",
        encoding="utf-8",
    )
    library.apply_readme_block(readme, f"{library.README_BEGIN}\nNEW\n{library.README_END}")
    text = readme.read_text(encoding="utf-8")
    assert "NEW" in text
    assert "old" not in text
    assert "# Title" in text
    assert "Footer." in text
