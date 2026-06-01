from build import lint


def test_clean_repo_has_no_errors(sample_repo):
    issues = lint.lint_repo(sample_repo)
    assert [i for i in issues if i.level == "error"] == []


def test_duplicate_canon_id_is_an_error(sample_repo):
    canon = sample_repo / "worlds" / "floating-isles" / "canon" / "extra.yaml"
    canon.write_text(
        "- id: mist-cat\n"
        "  names: {en-GB: Mist Cat, es-ES: Gato de Niebla}\n"
        "  kind: creature\n",
        encoding="utf-8",
    )
    issues = lint.lint_repo(sample_repo)
    assert any(i.level == "error" and "mist-cat" in i.message for i in issues)


def test_missing_required_content_file_is_an_error(sample_repo):
    target = (
        sample_repo
        / "worlds/floating-isles/stories/sleeping-garden/content/es-ES/rules.md"
    )
    target.unlink()
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "error" and "rules.md" in i.message and "es-ES" in i.message
        for i in issues
    )


def test_story_world_mismatch_is_an_error(sample_repo):
    story_yaml = (
        sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    )
    text = story_yaml.read_text(encoding="utf-8").replace(
        "world: floating-isles", "world: greek-myth"
    )
    story_yaml.write_text(text, encoding="utf-8")
    issues = lint.lint_repo(sample_repo)
    assert any(i.level == "error" and "world" in i.message.lower() for i in issues)
