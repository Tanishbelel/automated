"""
redaction/utils.py
------------------
Utility helpers shared across the redaction module:

  - PDF → list-of-PIL-Images  (via PyMuPDF / fitz)
  - list-of-PIL-Images → in-memory PDF bytes
  - PIL Image → in-memory PNG bytes
  - MIME-type sniffing from a Django UploadedFile

No dependency on any existing project code.
"""

import io
from typing import List

from PIL import Image


# ── PDF helpers (PyMuPDF) ─────────────────────────────────────────────────────

def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> List[Image.Image]:
    """
    Convert every page of a PDF (supplied as raw bytes) into a PIL Image.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw PDF content (read from an uploaded file, not from disk).
    dpi : int
        Render resolution.  150 dpi is a reasonable balance between speed
        and OCR accuracy; raise to 200-300 for dense documents.

    Returns
    -------
    list[PIL.Image.Image]
        One RGB image per page.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF redaction.  "
            "Install it with:  pip install PyMuPDF"
        ) from exc

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: List[Image.Image] = []
    zoom = dpi / 72.0               # 72 pt = 1 inch; scale to target dpi
    mat = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    doc.close()
    return images


def images_to_pdf_bytes(images: List[Image.Image]) -> bytes:
    """
    Combine a list of PIL Images into a single in-memory PDF and return
    the raw bytes.  Uses Pillow's built-in PDF writer – no extra deps.

    Parameters
    ----------
    images : list[PIL.Image.Image]
        Pages to assemble, in order.

    Returns
    -------
    bytes
        Raw PDF bytes ready to stream as an HTTP response.
    """
    if not images:
        raise ValueError("images list must not be empty")

    buf = io.BytesIO()
    rgb_images = [img.convert("RGB") for img in images]
    rgb_images[0].save(
        buf,
        format="PDF",
        save_all=True,
        append_images=rgb_images[1:],
    )
    return buf.getvalue()


# ── Image helper ──────────────────────────────────────────────────────────────

def image_to_png_bytes(image: Image.Image) -> bytes:
    """
    Serialise a PIL Image to raw PNG bytes (in-memory).

    Parameters
    ----------
    image : PIL.Image.Image

    Returns
    -------
    bytes
    """
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ── MIME / extension helpers ──────────────────────────────────────────────────

def get_mime_type(uploaded_file) -> str:
    """
    Return the MIME type of a Django ``InMemoryUploadedFile`` /
    ``TemporaryUploadedFile``.  Falls back to sniffing by file extension
    when the browser did not set Content-Type.

    Parameters
    ----------
    uploaded_file : django.core.files.uploadedfile.UploadedFile

    Returns
    -------
    str
        Lower-case MIME type string, e.g. ``'image/png'``.
    """
    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type != "application/octet-stream":
        return content_type

    # Fallback: guess from file name
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".tiff") or name.endswith(".tif"):
        return "image/tiff"
    if name.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


_SUPPORTED_IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/tiff",
    "image/bmp",
}


def is_image_mime(mime: str) -> bool:
    return mime in _SUPPORTED_IMAGE_MIMES


def is_pdf_mime(mime: str) -> bool:
    return mime == "application/pdf"
