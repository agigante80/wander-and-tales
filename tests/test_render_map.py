from build.render import map as kit_map

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text x="20" y="60" font-size="16">Mapa</text></svg>'
)


def test_svg_renders_to_a_pdf(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TINY_SVG, encoding="utf-8")
    out = tmp_path / "map.pdf"
    result = kit_map.render_svg_to_pdf(svg, out)
    assert result == out
    assert out.read_bytes().startswith(b"%PDF")


def _write(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_TINY_SVG, encoding="utf-8")


def test_find_map_returns_none_when_no_map_exists(tmp_path):
    world = tmp_path / "world"
    story = world / "stories" / "s"
    assert kit_map.find_map(world, story, "en-GB") is None


def test_find_map_falls_back_to_world_map(tmp_path):
    world = tmp_path / "world"
    story = world / "stories" / "s"
    _write(world / "assets" / "map.svg")
    assert kit_map.find_map(world, story, "en-GB") == world / "assets" / "map.svg"


def test_story_map_overrides_world_map(tmp_path):
    world = tmp_path / "world"
    story = world / "stories" / "s"
    _write(world / "assets" / "map.svg")
    _write(story / "assets" / "map.svg")
    assert kit_map.find_map(world, story, "en-GB") == story / "assets" / "map.svg"


def test_locale_specific_map_overrides_generic(tmp_path):
    world = tmp_path / "world"
    story = world / "stories" / "s"
    _write(story / "assets" / "map.svg")
    _write(story / "assets" / "map.es-ES.svg")
    assert kit_map.find_map(world, story, "es-ES") == story / "assets" / "map.es-ES.svg"
    # a locale without its own map falls back to the generic story map
    assert kit_map.find_map(world, story, "en-GB") == story / "assets" / "map.svg"
