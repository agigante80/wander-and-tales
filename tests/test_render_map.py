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


def test_wrap_one_word_stays_one_line():
    assert kit_map._wrap("Mist", 2) == ["Mist"]


def test_wrap_two_words_split_one_each():
    assert kit_map._wrap("Vine Gate", 2) == ["Vine", "Gate"]


def test_wrap_four_words_balanced():
    assert kit_map._wrap("La Puerta de Enredaderas", 2) == ["La Puerta", "de Enredaderas"]


def test_wrap_max_one_returns_whole_text():
    assert kit_map._wrap("The Talking Fountain", 1) == ["The Talking Fountain"]


_TEMPLATE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" font-family="DejaVu Sans">'
    '<rect width="200" height="120" fill="#eaf7e1"/>'
    '<text data-label="title" x="100" y="30" text-anchor="middle"></text>'
    '<text data-label="stop:gate" data-wrap="2" x="100" y="80" text-anchor="middle"></text>'
    "</svg>"
)


def test_template_keys_in_document_order(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TEMPLATE_SVG, encoding="utf-8")
    assert kit_map.template_keys(svg) == ["title", "stop:gate"]


def test_fill_substitutes_wraps_and_strips_data_attrs():
    out = kit_map.fill_template(
        _TEMPLATE_SVG, {"title": "El Jardín", "stop:gate": "La Puerta Verde"}
    )
    assert "El Jardín" in out  # accent preserved
    assert out.count("<tspan") == 2  # "La Puerta Verde" wrapped to two lines
    assert "data-label" not in out and "data-wrap" not in out


def test_fill_leaves_unkeyed_label_empty():
    out = kit_map.fill_template(_TEMPLATE_SVG, {"title": "Only Title"})
    assert "Only Title" in out


def test_render_map_template_writes_pdf(tmp_path):
    svg = tmp_path / "map.svg"
    svg.write_text(_TEMPLATE_SVG, encoding="utf-8")
    out = tmp_path / "map.pdf"
    result = kit_map.render_map_template(
        svg, out, {"title": "El Jardín", "stop:gate": "La Puerta Verde"}
    )
    assert result == out
    assert out.read_bytes().startswith(b"%PDF")


def test_render_map_template_passes_plain_svg_through(tmp_path):
    svg = tmp_path / "plain.svg"
    svg.write_text(_TINY_SVG, encoding="utf-8")  # no data-label nodes
    out = tmp_path / "plain.pdf"
    kit_map.render_map_template(svg, out, {})
    assert out.read_bytes().startswith(b"%PDF")
