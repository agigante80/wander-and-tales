import base64
import types
from pathlib import Path

import pytest

from build import generate, prompts


class _FakeImages:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return types.SimpleNamespace(
            data=[types.SimpleNamespace(b64_json=self._payload)]
        )


class _FakeClient:
    def __init__(self, raw: bytes):
        self.images = _FakeImages(base64.b64encode(raw).decode())


def test_image_size_for_each_orientation():
    assert generate.image_size_for("portrait") == "1024x1536"
    assert generate.image_size_for("landscape") == "1536x1024"
    assert generate.image_size_for("square") == "1024x1024"


def test_target_path_for_world_and_story_images(repo_with_images):
    entries = prompts.iter_image_prompts(repo_with_images)
    world_cover = next(e for e in entries if e.story_id is None and e.image.id == "cover")
    story_scene = next(e for e in entries if e.story_id == "s" and e.image.id == "scene-1")
    assert generate.target_path(repo_with_images, world_cover) == (
        repo_with_images / "worlds" / "w" / "assets" / "cover.png"
    )
    assert generate.target_path(repo_with_images, story_scene) == (
        repo_with_images / "worlds" / "w" / "stories" / "s" / "assets" / "scene-1.png"
    )


def test_generate_image_writes_decoded_bytes(tmp_path):
    client = _FakeClient(b"PNGDATA")
    out = tmp_path / "a" / "cover.png"
    result = generate.generate_image("a prompt", "portrait", out, client=client)
    assert result == out
    assert out.read_bytes() == b"PNGDATA"
    assert client.images.calls[0]["size"] == "1024x1536"
    assert client.images.calls[0]["prompt"] == "a prompt"
    assert client.images.calls[0]["model"] == "gpt-image-1"


def test_generate_all_skips_existing_unless_forced(repo_with_images):
    client = _FakeClient(b"PNGDATA")
    first = generate.generate_all(repo_with_images, client=client)
    assert len(first) == 4  # 2 world images + 2 story images
    again = generate.generate_all(repo_with_images, client=client)
    assert again == []  # all exist now, skipped
    forced = generate.generate_all(repo_with_images, force=True, client=client)
    assert len(forced) == 4
