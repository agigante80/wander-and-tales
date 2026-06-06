import textwrap

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from build.models import ExampleHero
from build.render import examples


def _write_heroes(repo):
    (repo / "worlds" / "floating-isles" / "heroes.yaml").write_text(
        textwrap.dedent("""
        - id: aria
          tier: young
          name: Aria
          hero_of: { en-GB: the Isles, es-ES: las Islas, it-IT: le Isole, pt-PT: le Isole }
          magics: [mist-cat, mist-cat]
          energy: 3
          carry:
            - { en-GB: a lantern, es-ES: un farol, it-IT: una lanterna, pt-PT: una lanterna }
          image:
            id: hero-aria
            role: hero
            orientation: portrait
            prompt: A friendly young hero.
            alt: { en-GB: a hero, es-ES: un heroe, it-IT: un eroe, pt-PT: un eroe }
        - id: leo
          tier: young
          name: Leo
          hero_of: { en-GB: the Isles, es-ES: las Islas, it-IT: le Isole, pt-PT: le Isole }
          magics: [mist-cat, mist-cat]
          energy: 2
          carry: []
          image:
            id: hero-leo
            role: hero
            orientation: portrait
            prompt: A friendly young hero.
            alt: { en-GB: a hero, es-ES: un heroe, it-IT: un eroe, pt-PT: un eroe }
        - id: mira
          tier: older
          name: Mira
          hero_of: { en-GB: the Isles, es-ES: las Islas, it-IT: le Isole, pt-PT: le Isole }
          magics: [mist-cat, mist-cat]
          energy: 5
          carry: []
          image:
            id: hero-mira
            role: hero
            orientation: portrait
            prompt: A confident older hero.
            alt: { en-GB: a hero, es-ES: un heroe, it-IT: un eroe, pt-PT: un eroe }
        - id: theo
          tier: older
          name: Theo
          hero_of: { en-GB: the Isles, es-ES: las Islas, it-IT: le Isole, pt-PT: le Isole }
          magics: [mist-cat, mist-cat]
          energy: 4
          carry: []
          image:
            id: hero-theo
            role: hero
            orientation: portrait
            prompt: A confident older hero.
            alt: { en-GB: a hero, es-ES: un heroe, it-IT: un eroe, pt-PT: un eroe }
    """).lstrip(), encoding="utf-8")


def test_example_heroes_pdf_has_one_page_per_hero(sample_repo, tmp_path):
    _write_heroes(sample_repo)
    out = examples.build_example_heroes(
        sample_repo, "floating-isles", "en-GB", out_dir=tmp_path
    )
    assert out == (
        tmp_path / "en-GB" / "floating-isles"
        / "floating-isles-example-heroes-en-GB.pdf"
    )
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 4


def test_example_heroes_renders_in_spanish(sample_repo, tmp_path):
    _write_heroes(sample_repo)
    out = examples.build_example_heroes(
        sample_repo, "floating-isles", "es-ES", out_dir=tmp_path
    )
    assert out.read_bytes().startswith(b"%PDF")


def test_example_hero_rejects_three_or_more_magics():
    with pytest.raises(ValidationError):
        ExampleHero.model_validate({
            "id": "x", "tier": "young", "name": "X",
            "hero_of": {"en-GB": "a", "es-ES": "a", "it-IT": "a", "pt-PT": "a"},
            "magics": ["a", "b", "c"],
            "image": {
                "id": "h", "role": "hero", "orientation": "portrait",
                "prompt": "p", "alt": {"en-GB": "a", "es-ES": "a", "it-IT": "a", "pt-PT": "a"},
            },
        })


def test_example_hero_tier_must_be_young_or_older():
    with pytest.raises(ValidationError):
        ExampleHero.model_validate({
            "id": "x", "tier": "early", "name": "X",
            "hero_of": {"en-GB": "a", "es-ES": "a", "it-IT": "a", "pt-PT": "a"},
            "magics": ["a", "b"],
            "image": {
                "id": "h", "role": "hero", "orientation": "portrait",
                "prompt": "p", "alt": {"en-GB": "a", "es-ES": "a", "it-IT": "a", "pt-PT": "a"},
            },
        })
