"""Generate image files from composed prompts via an injectable OpenAI client.

The client is passed in so tests use a fake and nothing touches the network. The
CLI builds the real client only after confirming the API key is present. A
different image backend can replace make_client and generate_image later without
touching the schema or the prompts.
"""

import base64
from pathlib import Path

from build import prompts
from build.prompts import PromptEntry

_SIZES = {
    "portrait": "1024x1536",
    "landscape": "1536x1024",
    "square": "1024x1024",
}


def image_size_for(orientation: str) -> str:
    """Map an orientation to an OpenAI image size."""
    return _SIZES[orientation]


def target_path(root: Path, entry: PromptEntry) -> Path:
    """The assets path where an entry's PNG is written."""
    world_dir = root / "worlds" / entry.world_id
    if entry.story_id is None:
        return world_dir / "assets" / f"{entry.image.id}.png"
    return world_dir / "stories" / entry.story_id / "assets" / f"{entry.image.id}.png"


def make_client(api_key: str):
    """Construct a real OpenAI client. Imported lazily so the core needs no openai."""
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def generate_image(prompt: str, orientation: str, out_path: Path, *, client) -> Path:
    """Generate one image and write the PNG to out_path. Returns out_path."""
    response = client.images.generate(
        model="gpt-image-1", prompt=prompt, size=image_size_for(orientation), n=1
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return out_path


def generate_all(
    root: Path,
    *,
    world: str | None = None,
    story: str | None = None,
    force: bool = False,
    client,
) -> list[Path]:
    """Generate every declared image (filtered), skipping existing unless force."""
    written: list[Path] = []
    for entry in prompts.iter_image_prompts(root, world=world, story=story):
        out = target_path(root, entry)
        if out.exists() and not force:
            continue
        generate_image(entry.text, entry.image.orientation, out, client=client)
        written.append(out)
    return written
