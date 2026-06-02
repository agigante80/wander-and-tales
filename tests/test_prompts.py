from build import prompts
from build.models import Image, World


def _world():
    return World.model_validate(
        {"id": "w", "name": {"en-GB": "W", "es-ES": "W"},
         "visual_style": "Soft storybook art."}
    )


def _image(**over):
    data = {"id": "cover", "role": "cover", "orientation": "portrait",
            "prompt": "A sleeping garden.",
            "alt": {"en-GB": "x", "es-ES": "y"}}
    data.update(over)
    return Image.model_validate(data)


def test_compose_includes_style_subject_and_no_text_rule():
    text = prompts.compose_prompt(_world(), _image(), {})
    assert "Soft storybook art." in text
    assert "A sleeping garden." in text
    assert "No text" in text


def test_compose_aspect_hint_matches_orientation():
    assert "3 to 4" in prompts.compose_prompt(_world(), _image(orientation="portrait"), {})
    assert "4 to 3" in prompts.compose_prompt(_world(), _image(orientation="landscape"), {})
    assert "1 to 1" in prompts.compose_prompt(_world(), _image(orientation="square"), {})


def test_compose_appends_canon_description_when_ref_resolves():
    from build.models import CanonEntry

    canon = {"mist-cat": CanonEntry.model_validate(
        {"id": "mist-cat", "kind": "creature",
         "names": {"en-GB": "Mist Cat", "es-ES": "Gato de Niebla"},
         "description": {"en-GB": "A gentle cat of fog.", "es-ES": "Un gato de niebla."}}
    )}
    text = prompts.compose_prompt(_world(), _image(canon_ref="mist-cat"), canon)
    assert "Mist Cat" in text and "gentle cat of fog" in text


def test_iter_image_prompts_covers_world_and_story(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    ids = {(e.world_id, e.story_id, e.image.id) for e in entries}
    assert ("w", None, "cover") in ids
    assert ("w", None, "beast") in ids
    assert ("w", "s", "cover") in ids
    assert ("w", "s", "scene-1") in ids
    beast = next(e for e in entries if e.image.id == "beast")
    assert "Test Beast" in beast.text  # canon_ref pulled the canon name


def test_filters_narrow_to_a_story(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images, world="w", story="s")
    owners = {(e.world_id, e.story_id) for e in entries}
    assert owners == {("w", "s")}  # world-level images excluded when a story is named


def test_markdown_has_fenced_prompt_and_alt(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    md = prompts.build_prompts_markdown(entries)
    assert "```" in md
    assert "Alt text:" in md
    assert "- en-GB:" in md
