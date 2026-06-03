from build.__main__ import main


def test_validate_ok_returns_zero(sample_repo, capsys):
    code = main(["validate", "--root", str(sample_repo)])
    assert code == 0
    assert "OK" in capsys.readouterr().out


def test_lint_reports_errors_with_nonzero_exit(sample_repo, capsys):
    (sample_repo / "worlds/floating-isles/stories/sleeping-garden/content/es-ES/rules.md").unlink()
    code = main(["lint", "--root", str(sample_repo)])
    assert code == 1
    assert "rules.md" in capsys.readouterr().out
