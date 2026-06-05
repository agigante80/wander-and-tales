from build import lint


def test_clean_repo_has_no_errors(sample_repo):
    issues = lint.lint_repo(sample_repo)
    assert [i for i in issues if i.level == "error"] == []


def test_duplicate_canon_id_is_an_error(sample_repo):
    canon = sample_repo / "worlds" / "floating-isles" / "canon" / "extra.yaml"
    canon.write_text(
        "- id: mist-cat\n"
        "  names: {en-GB: Mist Cat, es-ES: Gato de Niebla, it-IT: Gatto di Nebbia, pt-PT: Gatto di Nebbia}\n"
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


def test_clean_repo_has_no_lexicon_errors(sample_repo):
    issues = lint.lint_repo(sample_repo)
    assert not [i for i in issues if "lexicon" in i.message]


def test_duplicate_lexicon_id_is_an_error(sample_repo):
    path = sample_repo / "lexicon" / "terms.yaml"
    path.write_text(
        "- id: game-master\n"
        "  names: {en-GB: Game Master, es-ES: Guia del Juego, it-IT: Maestro di Gioco, pt-PT: Maestro di Gioco}\n"
        "- id: game-master\n"
        "  names: {en-GB: GM, es-ES: GJ, it-IT: MG, pt-PT: MG}\n",
        encoding="utf-8",
    )
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "error" and "game-master" in i.message and "lexicon" in i.message
        for i in issues
    )


def test_lint_requires_a_world_level_idea_bank(sample_repo):
    from build import lint

    target = sample_repo / "worlds" / "floating-isles" / "content" / "en-GB" / "idea-bank.md"
    target.unlink()
    issues = lint.lint_repo(sample_repo)
    assert any(
        i.level == "error" and "world idea bank" in i.message for i in issues
    )


def test_lint_does_not_require_a_per_story_idea_bank(sample_repo):
    from build import lint

    story_idea = (
        sample_repo / "worlds" / "floating-isles" / "stories" / "sleeping-garden"
        / "content" / "en-GB" / "idea-bank.md"
    )
    # There is no per-story idea bank, and that must not be an error.
    assert not story_idea.exists()
    errors = [i for i in lint.lint_repo(sample_repo) if i.level == "error"]
    assert not any("idea-bank.md" in e.message for e in errors)
