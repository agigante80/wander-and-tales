from reportlab.platypus import Paragraph, Table as RLTable

from build.render import flowables, fonts, theme
from build.render import markdown as md


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def test_heading_and_paragraph_become_paragraphs():
    blocks = [md.Heading(1, "Title"), md.Para("Some **bold** text.")]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    paragraphs = [f for f in flows if isinstance(f, Paragraph)]
    assert len(paragraphs) == 2
    assert "<b>bold</b>" in paragraphs[1].text


def test_table_block_becomes_a_reportlab_table():
    blocks = [md.Table(["Roll", "Surprise"], [["1", "A hint."]])]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    assert any(isinstance(f, RLTable) for f in flows)


def test_bullets_become_one_paragraph_each():
    blocks = [md.Bullets(["one", "two", "three"])]
    flows = flowables.blocks_to_flowables(blocks, _styles(), theme.Theme.default())
    paragraphs = [f for f in flows if isinstance(f, Paragraph)]
    assert len(paragraphs) == 3
