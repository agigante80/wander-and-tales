import base64
import types

from build import generate
from build.__main__ import main


class _FakeImages:
    def generate(self, **kwargs):
        return types.SimpleNamespace(
            data=[types.SimpleNamespace(b64_json=base64.b64encode(b"PNG").decode())]
        )


class _FakeClient:
    images = _FakeImages()


def test_generate_images_writes_files(repo_with_images, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(generate, "make_client", lambda api_key: _FakeClient())
    code = main(["generate-images", "--root", str(repo_with_images)])
    assert code == 0
    assert (repo_with_images / "worlds" / "w" / "assets" / "cover.png").is_file()
    assert "4 image(s) written" in capsys.readouterr().out


def test_generate_images_skips_then_forces(repo_with_images, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(generate, "make_client", lambda api_key: _FakeClient())
    main(["generate-images", "--root", str(repo_with_images)])
    capsys.readouterr()  # discard first-run output
    cover = repo_with_images / "worlds" / "w" / "assets" / "cover.png"
    mtime = cover.stat().st_mtime_ns
    # second run skips every image (files already exist), writing nothing
    main(["generate-images", "--root", str(repo_with_images)])
    assert "0 image(s) written" in capsys.readouterr().out
    assert cover.stat().st_mtime_ns == mtime
    # force regenerates all four
    main(["generate-images", "--root", str(repo_with_images), "--force"])
    assert "4 image(s) written" in capsys.readouterr().out


def test_generate_images_missing_key_returns_one(repo_with_images, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code = main(["generate-images", "--root", str(repo_with_images)])
    assert code == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out
