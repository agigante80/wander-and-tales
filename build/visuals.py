"""Image vocabulary: the single source of truth for image roles and orientations.

Pure data so the model can import it without any rendering or network dependency,
like fontspec.py, tags.py and dice.py.
"""

IMAGE_ROLES = ("cover", "scene", "portrait", "motif", "hero")
ORIENTATIONS = ("portrait", "landscape", "square")
