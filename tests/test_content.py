from build import content
from build.models import CanonEntry, Story, World


def test_load_world(sample_repo):
    world = content.load_world(sample_repo / "worlds" / "floating-isles" / "world.yaml")
    assert isinstance(world, World)
    assert world.name["es-ES"] == "Las Islas Flotantes"


def test_load_story(sample_repo):
    path = sample_repo / "worlds/floating-isles/stories/sleeping-garden/story.yaml"
    story = content.load_story(path)
    assert isinstance(story, Story)
    assert story.id == "sleeping-garden"


def test_load_canon_merges_category_files(sample_repo):
    entries = content.load_canon(sample_repo / "worlds" / "floating-isles" / "canon")
    assert all(isinstance(e, CanonEntry) for e in entries)
    assert {e.id for e in entries} == {"mist-cat"}


def test_iter_stories_finds_all(sample_repo):
    stories = list(content.iter_stories(sample_repo / "worlds"))
    assert [s.id for s in stories] == ["sleeping-garden"]
