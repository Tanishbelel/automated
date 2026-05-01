"""
redaction/views.py
------------------
Single API view:  POST /api/redact/

Accepts a file upload, detects sensitive data via OCR, redraws pixels,
and streams the redacted file back – all in memory.

No dependency on any existing project code.
"""

import io
import logging

from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from PIL import Image

from .detector import detect_sensitive_regions
from .redactor import redact_image
from .utils import (
    get_mime_type,
    is_image_mime,
    is_pdf_mime,
    pdf_to_images,
    images_to_pdf_bytes,
    image_to_png_bytes,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class RedactView(View):
    """
    POST /api/redact/

    Form field
    ----------
    file : UploadedFile
        An image (JPEG / PNG / WEBP / TIFF) or a PDF.

    Response
    --------
    On success:
        The redacted file is returned as a binary HTTP response with the
        appropriate Content-Type and a JSON header:

            X-Redacted-Fields : JSON array of labels found
                                e.g.  ["email", "phone"]

    On error:
        JSON 400 / 500 response.
    """

    def post(self, request, *args, **kwargs):
        # ── 1. Validate input ──────────────────────────────────────────────
        uploaded = request.FILES.get("file")
        if not uploaded:
            return _json_error(400, "No file provided.  Send a 'file' field.")

        mime = get_mime_type(uploaded)

        if not (is_image_mime(mime) or is_pdf_mime(mime)):
            return _json_error(
                400,
                f"Unsupported file type: {mime}.  "
                "Send an image (JPEG/PNG/WEBP/TIFF) or a PDF.",
            )

        raw_bytes = uploaded.read()

        # ── 2. Dispatch by file type ───────────────────────────────────────
        try:
            if is_pdf_mime(mime):
                return self._handle_pdf(raw_bytes)
            else:
                return self._handle_image(raw_bytes, mime)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Redaction failed: %s", exc)
            return _json_error(500, f"Redaction failed: {exc}")

    # ── Image pipeline ────────────────────────────────────────────────────────

    def _handle_image(self, raw_bytes: bytes, mime: str) -> HttpResponse:
        image = Image.open(io.BytesIO(raw_bytes))
        detections = detect_sensitive_regions(image)
        redacted = redact_image(image, detections)
        out_bytes = image_to_png_bytes(redacted)

        labels = _unique_labels(detections)
        response = HttpResponse(out_bytes, content_type="image/png")
        response["Content-Disposition"] = 'attachment; filename="redacted.png"'
        response["X-Redacted-Fields"] = _labels_json(labels)
        _attach_detections_header(response, detections)
        return response

    # ── PDF pipeline ──────────────────────────────────────────────────────────

    def _handle_pdf(self, raw_bytes: bytes) -> HttpResponse:
        pages = pdf_to_images(raw_bytes)

        redacted_pages = []
        all_detections = []

        for page_img in pages:
            detections = detect_sensitive_regions(page_img)
            all_detections.extend(detections)
            redacted_pages.append(redact_image(page_img, detections))

        out_bytes = images_to_pdf_bytes(redacted_pages)
        labels = _unique_labels(all_detections)

        response = HttpResponse(out_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="redacted.pdf"'
        response["X-Redacted-Fields"] = _labels_json(labels)
        _attach_detections_header(response, all_detections)
        return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_error(status: int, message: str) -> HttpResponse:
    import json
    body = json.dumps({"error": message})
    return HttpResponse(body, content_type="application/json", status=status)


def _unique_labels(detections) -> list:
    seen = []
    for d in detections:
        if d.label not in seen:
            seen.append(d.label)
    return seen


def _labels_json(labels: list) -> str:
    import json
    return json.dumps(labels)


def _attach_detections_header(response: HttpResponse, detections) -> None:
    """
    Attach a compact JSON summary of every detection to the response as
    the custom header  X-Redaction-Detail.

    Each entry: {"label": "email", "text": "...", "box": [x,y,w,h]}
    """
    import json
    detail = [
        {"label": d.label, "text": d.text, "box": list(d.box)}
        for d in detections
    ]
    response["X-Redaction-Detail"] = json.dumps(detail)
