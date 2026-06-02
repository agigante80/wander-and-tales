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
