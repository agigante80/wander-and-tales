from pypdf import PdfReader

from build.render import mapgen, theme


def _narration(tmp_path, body):
    path = tmp_path / "narration.simple.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_trail_nodes_reads_start_stops_and_goal(tmp_path):
    path = _narration(tmp_path, (
        "# The Sleeping Garden\n\n"
        "## Before you begin\n\nx\n\n"
        "## Stop 1: The Vine Gate\n\nx\n\n"
        "## Stop 2: The Flower Bed\n\nx\n\n"
        "## Stop 3: The Talking Fountain\n\nx\n\n"
        "## The Heart of the Garden\n\nx\n"
    ))
    nodes = mapgen.trail_nodes(path, "en-GB")
    kinds = [n.kind for n in nodes]
    assert kinds == ["start", "stop", "stop", "stop", "finish"]
    assert [n.tag for n in nodes if n.kind == "stop"] == ["1", "2", "3"]
    assert [n.label for n in nodes if n.kind == "stop"] == [
        "The Vine Gate", "The Flower Bed", "The Talking Fountain",
    ]
    assert nodes[-1].label == "The Heart of the Garden"


def test_trail_nodes_localised_numbered_headings(tmp_path):
    path = _narration(tmp_path, (
        "# Titolo\n\n## Prima di cominciare\n\n"
        "## Tappa 1: Il Cancello\n\n## Tappa 2: Il Prato\n\n"
        "## Il Cuore del Giardino\n"
    ))
    nodes = mapgen.trail_nodes(path, "it-IT")
    assert [n.kind for n in nodes] == ["start", "stop", "stop", "finish"]
    assert nodes[-1].label == "Il Cuore del Giardino"


def test_trail_nodes_without_headings_still_has_start_and_goal(tmp_path):
    path = _narration(tmp_path, "placeholder\n")
    nodes = mapgen.trail_nodes(path, "en-GB")
    assert [n.kind for n in nodes] == ["start", "finish"]


def test_render_generated_map_is_one_pdf_page(tmp_path):
    path = _narration(tmp_path, (
        "# T\n\n## Before you begin\n\n## Stop 1: A\n\n## Stop 2: B\n\n## The End Place\n"
    ))
    out = tmp_path / "map.pdf"
    mapgen.render_generated_map(out, "en-GB", "The Sleeping Garden", path, theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) == 1


def test_render_generated_map_handles_placeholder_narration(tmp_path):
    path = _narration(tmp_path, "placeholder\n")
    out = tmp_path / "map.pdf"
    mapgen.render_generated_map(out, "es-ES", "Prueba", path, theme.Theme.default())
    assert out.read_bytes().startswith(b"%PDF")
