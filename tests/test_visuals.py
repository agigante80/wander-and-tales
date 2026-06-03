from build import visuals


def test_image_roles_and_orientations():
    assert visuals.IMAGE_ROLES == ("cover", "scene", "portrait", "motif", "hero")
    assert visuals.ORIENTATIONS == ("portrait", "landscape", "square")
