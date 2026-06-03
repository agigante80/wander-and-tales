from PIL import Image as PILImage
from reportlab.platypus import Image as RLImage, Paragraph

from build.render import fonts, images, theme


def _styles():
    faces = fonts.register_family("dejavu-sans")
    return theme.make_styles(theme.Theme.default(), faces)


def _png(path, w, h):
    PILImage.new("RGB", (w, h), "white").save(path)
    return path


def test_image_flowable_scales_to_fit_preserving_aspect(tmp_path):
    p = _png(tmp_path / "i.png", 100, 50)
    flow = images.image_flowable(p, 200, 200)
    assert isinstance(flow, RLImage)
    # iw=100 ih=50; scale=min(200/100, 200/50)=2 -> 200 x 100
    assert round(flow.drawWidth) == 200
    assert round(flow.drawHeight) == 100


def test_image_flowable_capped_by_height(tmp_path):
    p = _png(tmp_path / "tall.png", 100, 400)
    flow = images.image_flowable(p, 200, 100)
    # scale=min(200/100, 100/400)=0.25 -> 25 x 100
    assert round(flow.drawHeight) == 100
    assert round(flow.drawWidth) == 25


def test_cover_flowables_has_title_and_image(tmp_path):
    p = _png(tmp_path / "c.png", 100, 150)
    flows = images.cover_flowables(p, "My Title", _styles())
    assert any(isinstance(f, Paragraph) and "My Title" in f.text for f in flows)
    assert any(isinstance(f, RLImage) for f in flows)


def test_gallery_flowables_image_and_caption_per_scene(tmp_path):
    a = _png(tmp_path / "a.png", 160, 100)
    b = _png(tmp_path / "b.png", 160, 100)
    flows = images.gallery_flowables(
        "Pictures", [(a, "first"), (b, "second")], _styles()
    )
    rl = [f for f in flows if isinstance(f, RLImage)]
    caps = [
        f
        for f in flows
        if isinstance(f, Paragraph) and ("first" in f.text or "second" in f.text)
    ]
    assert len(rl) == 2 and len(caps) == 2


def test_portrait_flowable_is_an_image(tmp_path):
    p = _png(tmp_path / "p.png", 200, 200)
    assert isinstance(images.portrait_flowable(p), RLImage)


def test_embed_flattens_transparency_onto_white(tmp_path):
    # A fully transparent RGBA PNG (over black) must composite to white, not black.
    p = tmp_path / "t.png"
    PILImage.new("RGBA", (20, 20), (0, 0, 0, 0)).save(p)
    buffer, _, _ = images._embed_jpeg(p)
    out = PILImage.open(buffer).convert("RGB")
    assert min(out.getpixel((10, 10))) > 240


def test_frontpage_without_cover_is_title_and_paragraph(tmp_path):
    from reportlab.platypus import Paragraph

    from build.render import fonts, images, theme

    styles = theme.make_styles(theme.Theme.default(), fonts.register_family("dejavu-sans"))
    flows = images.frontpage_flowables("The Sleeping Garden", "A world of floating isles.", None, styles)
    assert all(isinstance(f, Paragraph) or f.__class__.__name__ == "Spacer" for f in flows)
    assert any(isinstance(f, Paragraph) for f in flows)


def test_frontpage_with_cover_includes_an_image(tmp_path):
    from PIL import Image as PILImage
    from reportlab.platypus import Image as RLImage

    from build.render import fonts, images, theme

    cover = tmp_path / "cover.png"
    PILImage.new("RGB", (400, 600), "white").save(cover)
    styles = theme.make_styles(theme.Theme.default(), fonts.register_family("dejavu-sans"))
    flows = images.frontpage_flowables("Title", "Paragraph.", cover, styles)
    assert any(isinstance(f, RLImage) for f in flows)
