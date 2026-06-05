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
            "      it-IT: Una scena.\n"
            "      pt-PT: Una scena.\n"
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
    # Match the canon_ref warning by its wording, not the loose substring "canon_ref"
    # (which would also match the temp directory path pytest names after the test).
    assert not any(
        i.level == "warning" and "names no canon entry" in i.message for i in issues
    )


def _set_world_image(sample_repo, canon_ref):
    world_yaml = sample_repo / "worlds/floating-isles/world.yaml"
    world_yaml.write_text(
        world_yaml.read_text(encoding="utf-8")
        + (
            "images:\n"
            "  - id: cover\n"
            "    role: cover\n"
            "    orientation: portrait\n"
            f"    canon_ref: {canon_ref}\n"
            "    prompt: A world image.\n"
            "    alt:\n"
            "      en-GB: A world image.\n"
            "      es-ES: Una imagen del mundo.\n"
            "      it-IT: Un'immagine del mondo.\n"
            "      pt-PT: Un'immagine del mondo.\n"
        ),
        encoding="utf-8",
    )


def test_unknown_world_image_canon_ref_is_a_warning(sample_repo):
    _set_world_image(sample_repo, "no-such-world-ref")
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "warning" and "no-such-world-ref" in i.message for i in issues
    )


_IMAGE_BLOCK = (
    "images:\n"
    "  - id: cover\n"
    "    role: cover\n"
    "    orientation: portrait\n"
    "    prompt: A scene.\n"
    "    alt:\n"
    "      en-GB: A scene.\n"
    "      es-ES: Una escena.\n"
    "      it-IT: Una scena.\n"
    "      pt-PT: Una scena.\n"
)


def test_declared_image_without_file_is_a_warning(sample_repo):
    story_yaml = (
        sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    )
    story_yaml.write_text(
        story_yaml.read_text(encoding="utf-8") + _IMAGE_BLOCK, encoding="utf-8"
    )
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "warning" and "cover" in i.message and "no generated file" in i.message
        for i in issues
    )


def test_declared_image_with_file_is_clean(sample_repo):
    story_dir = sample_repo / "worlds/floating-isles/stories/sleeping-garden"
    assets = story_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "cover.png").write_bytes(b"PNG")
    story_yaml = story_dir / "story.yaml"
    story_yaml.write_text(
        story_yaml.read_text(encoding="utf-8") + _IMAGE_BLOCK, encoding="utf-8"
    )
    issues = lint.lint_repo(sample_repo)
    assert not any(i.level == "warning" and "cover" in i.message for i in issues)


def test_orphan_image_file_is_a_warning(sample_repo):
    assets = sample_repo / "worlds/floating-isles/stories/sleeping-garden/assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "stray.png").write_bytes(b"PNG")
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "warning"
        and "stray.png" in i.message
        and "no matching image declaration" in i.message
        for i in issues
    )
