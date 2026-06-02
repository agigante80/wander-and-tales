from build.render import markdown as md


def test_headings_and_levels():
    blocks = md.parse_markdown("# Title\n\n## Section\n")
    assert blocks == [md.Heading(1, "Title"), md.Heading(2, "Section")]


def test_paragraph_joins_wrapped_lines():
    blocks = md.parse_markdown("One line\nwrapped onto two.\n")
    assert blocks == [md.Para("One line wrapped onto two.")]


def test_bullets_collect_and_join_continuations():
    text = "- first item that\n  wraps\n- second item\n"
    blocks = md.parse_markdown(text)
    assert blocks == [md.Bullets(["first item that wraps", "second item"])]


def test_pipe_table_parses_header_and_rows():
    text = "| Roll | Surprise |\n|---|---|\n| 1 | A hint. |\n| 2 | A star. |\n"
    blocks = md.parse_markdown(text)
    assert blocks == [
        md.Table(["Roll", "Surprise"], [["1", "A hint."], ["2", "A star."]])
    ]


def test_mixed_document_keeps_order():
    text = "# T\n\nIntro para.\n\n## S\n\n- a\n- b\n"
    blocks = md.parse_markdown(text)
    assert blocks == [
        md.Heading(1, "T"),
        md.Para("Intro para."),
        md.Heading(2, "S"),
        md.Bullets(["a", "b"]),
    ]
