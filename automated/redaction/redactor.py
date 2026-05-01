"""
redaction/redactor.py
---------------------
Draws irreversible black-box redactions on images.
Works entirely in memory – nothing is written to disk.
"""

from typing import List, Tuple
from PIL import Image, ImageDraw

from .detector import Detection


# Padding (px) added around each detected box for a cleaner look
_BOX_PADDING = 4


def redact_image(
    image: Image.Image,
    detections: List[Detection],
    fill_color: Tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """
    Return a **new** PIL Image with every detection covered by a solid
    filled rectangle (default: black).  The original *image* is not
    mutated.

    Parameters
    ----------
    image : PIL.Image.Image
        Source image (any mode – will be converted to RGB).
    detections : list[Detection]
        Bounding boxes returned by ``detector.detect_sensitive_regions``.
    fill_color : tuple
        RGB colour for the redaction box.  Default is pure black.

    Returns
    -------
    PIL.Image.Image
        New image with sensitive regions blacked out.
    """
    # Work on a fresh copy so caller's image is untouched
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)

    img_w, img_h = out.size

    for det in detections:
        x, y, w, h = det.box
        # Apply padding, clamped to image bounds
        x1 = max(0, x - _BOX_PADDING)
        y1 = max(0, y - _BOX_PADDING)
        x2 = min(img_w, x + w + _BOX_PADDING)
        y2 = min(img_h, y + h + _BOX_PADDING)

        draw.rectangle([x1, y1, x2, y2], fill=fill_color)

    return out
