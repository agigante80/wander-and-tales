from build import lint


def _set_story_image(sample_repo, canon_ref):
    story_yaml = (
        sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    )
    story_yaml.write_text(
        story_yaml.read_text(encoding="utf-8")
        + (
            "images:\n"
            "  - id: cover\n"
            "    role: cover\n"
            "    orientation: portrait\n"
            f"    canon_ref: {canon_ref}\n"
            "    prompt: A scene.\n"
            "    alt:\n"
            "      en-GB: A scene.\n"
            "      es-ES: Una escena.\n"
        ),
        encoding="utf-8",
    )


def test_unknown_canon_ref_is_a_warning(sample_repo):
    _set_story_image(sample_repo, "no-such-id")
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "warning" and "no-such-id" in i.message for i in issues
    )


def test_known_canon_ref_is_clean(sample_repo):
    _set_story_image(sample_repo, "mist-cat")
    issues = lint.lint_repo(sample_repo)
    assert not any(
        i.level == "warning" and "canon_ref" in i.message for i in issues
    )
