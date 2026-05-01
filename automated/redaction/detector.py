"""
redaction/detector.py
---------------------
PAN card-specific sensitive-region detector.

Detects and returns bounding boxes for:
  1. PAN Number         – regex [A-Z]{5}[0-9]{4}[A-Z]
  2. Full Name          – text immediately after the "Name" label row
  3. Father's Name      – text immediately after the "Father's Name" label row
  4. Date of Birth      – date pattern after the "Date of Birth" label row
  5. Photograph         – face region (top-left quadrant) via OpenCV Haar cascade
  6. Signature          – handwritten ink blob via OpenCV contour analysis
  7. QR Code            – entire QR block via pyzbar / OpenCV

No dependency on any existing project code.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np
import cv2
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logger = logging.getLogger(__name__)

# ── Types ────────────────────────────────────────────────────────────────────

@dataclass
class Detection:
    """One detected sensitive region."""
    label: str                        # 'pan', 'name', 'father_name', 'dob',
                                      # 'photo', 'signature', 'qr_code'
    text: str                         # raw matched text (empty for visual regions)
    box: Tuple[int, int, int, int]    # (x, y, w, h) in pixels
    confidence: float                 # OCR confidence 0–100 (100 for visual detections)


# ── Regex patterns ─────────────────────────────────────────────────────────────

# PAN card number: exactly 5 uppercase letters, 4 digits, 1 uppercase letter
_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# Date of birth: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY etc.
_DOB_RE = re.compile(
    r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b"
    r"|\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b",
    re.IGNORECASE,
)

# Label markers on PAN cards (bilingual – Hindi + English)
_LABEL_NAME       = re.compile(r"\bname\b",              re.IGNORECASE)
_LABEL_FATHER     = re.compile(r"\bfather",              re.IGNORECASE)
_LABEL_DOB        = re.compile(r"\b(date\s+of\s+birth|dob|birth)\b", re.IGNORECASE)
_LABEL_PAN_HDR    = re.compile(r"permanent\s+account\s+number", re.IGNORECASE)


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_sensitive_regions(image: Image.Image) -> List[Detection]:
    """
    Run all detectors on *image* and return every sensitive region.

    Parameters
    ----------
    image : PIL.Image.Image
        RGB(A) image to analyse.

    Returns
    -------
    List[Detection]
        Bounding boxes for all detected sensitive regions.
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    detections: List[Detection] = []

    # ── 1–4: OCR-based text detections ────────────────────────────────────────
    detections.extend(_detect_text_fields(image))

    # ── 5: Photograph (face) ───────────────────────────────────────────────────
    photo = _detect_face(image)
    if photo:
        detections.append(photo)

    # ── 6: Signature ───────────────────────────────────────────────────────────
    sig = _detect_signature(image)
    if sig:
        detections.append(sig)

    # ── 7: QR Code ─────────────────────────────────────────────────────────────
    detections.extend(_detect_qr(image))

    return detections


# ── Words that are PAN card labels/headers – never personal data ─────────────────
_CARD_HEADER_WORDS = {
    "INCOME", "TAX", "DEPARTMENT", "GOVT", "GOVERNMENT", "OF", "INDIA",
    "PERMANENT", "ACCOUNT", "NUMBER", "CARD", "VALID", "UNLESS",
    "PHYSICALLY", "SIGNED", "APPLICATION", "DIGITALLY", "PAN",
    "NAME", "FATHER", "DATE", "BIRTH", "DOB", "S",
}


# ── OCR text field detector ────────────────────────────────────────────────────

def _detect_text_fields(image: Image.Image) -> List[Detection]:
    """
    Two-strategy OCR detector for PAN card text fields:

    Strategy A (label-aware): group tokens into visual lines by Y proximity,
    find the label lines (Name / Father's Name / Date of Birth) and redact
    the value line immediately below each.

    Strategy B (position + content fallback): if any field is still undetected,
    scan the lower-left zone of the card for ALL_CAPS words (names) and date
    patterns (DOB).  This is independent of label recognition.
    """
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--psm 6 -l eng",
    )

    n = len(data["text"])
    detections: List[Detection] = []

    tokens = []
    for i in range(n):
        word = (data["text"][i] or "").strip()
        conf = float(data["conf"][i])
        if conf < 5 or not word:   # lower threshold to catch more tokens
            continue
        tokens.append({
            "text": word,
            "conf": conf,
            "x": int(data["left"][i]),
            "y": int(data["top"][i]),
            "w": int(data["width"][i]),
            "h": int(data["height"][i]),
        })

    img_w, img_h = image.size

    # ── PAN number ─────────────────────────────────────────────────────────────
    pan_y_bottom = 0
    for tok in tokens:
        if _PAN_RE.search(tok["text"]):
            detections.append(Detection(
                label="pan",
                text=tok["text"],
                box=(tok["x"], tok["y"], tok["w"], tok["h"]),
                confidence=tok["conf"],
            ))
            pan_y_bottom = max(pan_y_bottom, tok["y"] + tok["h"])

    visual_lines = _group_into_visual_lines(tokens)

    # ── Strategy A: label-aware detection ──────────────────────────────────
    name_bottom:   Optional[int] = None
    father_bottom: Optional[int] = None
    dob_bottom:    Optional[int] = None
    father_top:    Optional[int] = None
    dob_top:       Optional[int] = None

    for vline in visual_lines:
        lt = vline["text"]
        if _LABEL_FATHER.search(lt):
            father_bottom = vline["y_bottom"]
            father_top    = vline["y_top"]
        elif _LABEL_NAME.search(lt):
            name_bottom   = vline["y_bottom"]
        elif _LABEL_DOB.search(lt):
            dob_bottom    = vline["y_bottom"]
            dob_top       = vline["y_top"]

    def _first_value_line(below_y, stop_y=None, label=""):
        if below_y is None:
            return None
        for vl in visual_lines:
            if vl["y_top"] < below_y:
                continue
            if stop_y and vl["y_top"] >= stop_y:
                break
            lt = vl["text"]
            if (_LABEL_NAME.search(lt) or _LABEL_FATHER.search(lt) or
                    _LABEL_DOB.search(lt) or _LABEL_PAN_HDR.search(lt)):
                continue
            left_toks = [t for t in vl["tokens"] if t["x"] < img_w * 0.70]
            return _tokens_to_detection(left_toks or vl["tokens"], label)
        return None

    name_det   = _first_value_line(name_bottom,   stop_y=father_top, label="name")
    father_det = _first_value_line(father_bottom, stop_y=dob_top,    label="father_name")
    dob_det: Optional[Detection] = None

    if dob_bottom is not None:
        for vl in visual_lines:
            if vl["y_top"] < dob_bottom:
                continue
            lt = vl["text"]
            if (_LABEL_NAME.search(lt) or _LABEL_FATHER.search(lt) or
                    _LABEL_DOB.search(lt) or _LABEL_PAN_HDR.search(lt)):
                continue
            dob_det = _find_dob_on_line(vl["tokens"], lt)
            break

    # ── Strategy B: position + content fallback ─────────────────────────────
    # Kick in for any field that Strategy A missed.
    # Uses raw token Y-bands (20 px) so Hindi OCR garble on label rows
    # cannot displace the real name/father rows.
    if name_det is None or father_det is None or dob_det is None:
        zone_y_start = pan_y_bottom if pan_y_bottom else int(img_h * 0.38)
        zone_x_max   = int(img_w * 0.65)

        # Build a second token list with zero confidence floor so nothing is
        # dropped — we rely on content filtering, not confidence, here.
        data2 = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config="--psm 11 -l eng",
        )
        all_tokens = []
        for i in range(len(data2["text"])):
            word = (data2["text"][i] or "").strip()
            if not word or float(data2["conf"][i]) < 0:
                continue
            all_tokens.append({
                "text": word,
                "x": int(data2["left"][i]),
                "y": int(data2["top"][i]),
                "w": int(data2["width"][i]),
                "h": int(data2["height"][i]),
                "conf": float(data2["conf"][i]),
            })

        # Bands that contain a label keyword — skip these
        label_bands: set = set()
        for t in all_tokens:
            txt = t["text"]
            if (_LABEL_NAME.search(txt) or _LABEL_FATHER.search(txt) or
                    _LABEL_DOB.search(txt) or _LABEL_PAN_HDR.search(txt)):
                label_bands.add(t["y"] // 20)

        # Collect qualifying value tokens (ALL_CAPS alpha, not header words,
        # not on a label band, inside the value zone)
        val_toks = [
            t for t in all_tokens
            if t["y"] >= zone_y_start
            and t["x"] < zone_x_max
            and len(t["text"]) >= 2
            and any(c.isalpha() for c in t["text"])
            and all(c.isupper() or not c.isalpha() for c in t["text"])
            and t["text"].upper() not in _CARD_HEADER_WORDS
            and (t["y"] // 20) not in label_bands
        ]

        # Group by 20-px Y-band and sort bands top-to-bottom
        bands: dict = {}
        for t in val_toks:
            bands.setdefault(t["y"] // 20, []).append(t)
        sorted_bands = [bands[k] for k in sorted(bands.keys())]

        if name_det is None and len(sorted_bands) >= 1:
            name_det = _tokens_to_detection(sorted_bands[0], "name")
        if father_det is None and len(sorted_bands) >= 2:
            father_det = _tokens_to_detection(sorted_bands[1], "father_name")

        # DOB fallback: any date-format token in the lower-left zone
        if dob_det is None:
            for tok in all_tokens:
                if (tok["y"] > zone_y_start
                        and tok["x"] < zone_x_max
                        and _DOB_RE.search(tok["text"])):
                    dob_det = _tokens_to_detection([tok], "dob")
                    break

    # Commit detections
    for d in (name_det, father_det, dob_det):
        if d:
            detections.append(d)

    return detections


# ── Visual line grouping (spatial, Y-proximity based) ─────────────────────────

def _group_into_visual_lines(tokens, y_tolerance: int = 8) -> list:
    """
    Group tokens into visual lines based on Y-coordinate proximity.

    Returns a list of dicts sorted top-to-bottom:
        {"y_top": int, "y_bottom": int, "tokens": [...], "text": str}
    """
    if not tokens:
        return []

    sorted_toks = sorted(tokens, key=lambda t: t["y"])
    groups: list = []
    current = [sorted_toks[0]]
    current_y = sorted_toks[0]["y"]

    for tok in sorted_toks[1:]:
        if abs(tok["y"] - current_y) <= y_tolerance:
            current.append(tok)
        else:
            current.sort(key=lambda t: t["x"])
            y_top    = min(t["y"]           for t in current)
            y_bottom = max(t["y"] + t["h"] for t in current)
            groups.append({
                "y_top": y_top,
                "y_bottom": y_bottom,
                "tokens": current,
                "text": " ".join(t["text"] for t in current),
            })
            current   = [tok]
            current_y = tok["y"]

    if current:
        current.sort(key=lambda t: t["x"])
        y_top    = min(t["y"]           for t in current)
        y_bottom = max(t["y"] + t["h"] for t in current)
        groups.append({
            "y_top": y_top,
            "y_bottom": y_bottom,
            "tokens": current,
            "text": " ".join(t["text"] for t in current),
        })

    return groups


def _find_dob_on_line(tokens, line_text) -> Optional[Detection]:
    """Search for a date pattern in the line and return a Detection if found."""
    m = _DOB_RE.search(line_text)
    if not m:
        return None

    matched_str = m.group()
    # Find the specific token(s) containing the date
    date_tokens = [t for t in tokens if matched_str in t["text"] or t["text"] in matched_str]
    if not date_tokens:
        # fallback: use any token that looks like a date digit
        date_tokens = [t for t in tokens if re.search(r"\d{1,2}[\/\-\.]\d", t["text"])]
    if not date_tokens:
        return None
    return _tokens_to_detection(date_tokens, "dob")


def _tokens_to_detection(tokens, label) -> Optional[Detection]:
    """Merge a list of tokens into a single Detection spanning them all."""
    if not tokens:
        return None
    xs = [t["x"] for t in tokens]
    ys = [t["y"] for t in tokens]
    x2s = [t["x"] + t["w"] for t in tokens]
    y2s = [t["y"] + t["h"] for t in tokens]
    x, y = min(xs), min(ys)
    w = max(x2s) - x
    h = max(y2s) - y
    conf = min(t["conf"] for t in tokens)
    text = " ".join(t["text"] for t in tokens)
    return Detection(label=label, text=text, box=(x, y, w, h), confidence=conf)


# ── Face / photograph detector ─────────────────────────────────────────────────

def _detect_face(image: Image.Image) -> Optional[Detection]:
    """
    Detect the photograph (face) using OpenCV Haar cascade.

    PAN cards always place the photo in the top-left quadrant, so we
    restrict the search to that region and fall back to a fixed box if
    OpenCV finds no face (e.g. low-quality scan).
    """
    img_w, img_h = image.size

    cv_img = _pil_to_cv(image)
    gray   = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Restrict to the left ~30% and top ~75% of the card
    roi_x2 = int(img_w * 0.32)
    roi_y2 = int(img_h * 0.80)
    roi    = gray[0:roi_y2, 0:roi_x2]

    try:
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(
            roi,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(30, 30),
        )
    except Exception:
        faces = []

    if len(faces) > 0:  # type: ignore[arg-type]
        # Take the largest face
        fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])
        return Detection(
            label="photo",
            text="",
            box=(int(fx), int(fy), int(fw), int(fh)),
            confidence=100.0,
        )

    # Fallback: fixed proportional box covering typical PAN photo placement
    # (roughly top-left ~25% width × top 55% height)
    fb_x = int(img_w * 0.01)
    fb_y = int(img_h * 0.13)
    fb_w = int(img_w * 0.26)
    fb_h = int(img_h * 0.58)
    return Detection(
        label="photo",
        text="",
        box=(fb_x, fb_y, fb_w, fb_h),
        confidence=100.0,
    )


# ── Signature detector ────────────────────────────────────────────────────────

def _detect_signature(image: Image.Image) -> Optional[Detection]:
    """
    Detect the handwritten signature region via contour analysis.

    PAN card signatures appear in the bottom half of the card, usually
    on a light background with darker ink strokes that form a compact blob.
    """
    img_w, img_h = image.size
    cv_img = _pil_to_cv(image)

    # Work only on the bottom ~35% of the card (where signature lives)
    # and exclude the extreme right ~35% (occupied by QR code on some cards)
    sig_y1 = int(img_h * 0.62)
    sig_x2 = int(img_w * 0.70)
    roi    = cv_img[sig_y1:img_h, 0:sig_x2]

    gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold to isolate dark ink
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10,
    )
    # Dilate to merge nearby strokes into one blob
    kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by aspect ratio and area consistent with a signature
    candidates = []
    for cnt in contours:
        rx, ry, rw, rh = cv2.boundingRect(cnt)
        area = rw * rh
        aspect = rw / max(rh, 1)
        # Signature: wide relative to height, reasonably large
        if 1.5 < aspect < 8 and area > (img_w * img_h * 0.005):
            candidates.append((rx, ry, rw, rh, area))

    if not candidates:
        return None

    # Pick the largest candidate
    rx, ry, rw, rh, _ = max(candidates, key=lambda c: c[4])

    # Translate back to full-image coordinates
    abs_x = rx
    abs_y = sig_y1 + ry
    return Detection(
        label="signature",
        text="",
        box=(abs_x, abs_y, rw, rh),
        confidence=100.0,
    )


# ── QR Code detector ──────────────────────────────────────────────────────────

def _detect_qr(image: Image.Image) -> List[Detection]:
    """
    Detect QR codes using OpenCV's built-in QRCodeDetector.
    Falls back to pyzbar if available and OpenCV misses it.
    """
    detections: List[Detection] = []
    cv_img = _pil_to_cv(image)

    # ── OpenCV QR detector ───────────────────────────────────────────────────
    try:
        qr_detector = cv2.QRCodeDetector()
        retval, points = qr_detector.detect(cv_img)  # type: ignore[call-arg]
        if retval and points is not None:
            pts = points[0].astype(int)
            x, y, w, h = cv2.boundingRect(pts)
            detections.append(Detection(
                label="qr_code",
                text="",
                box=(int(x), int(y), int(w), int(h)),
                confidence=100.0,
            ))
            return detections
    except Exception as exc:
        logger.debug("OpenCV QR detection failed: %s", exc)

    # ── pyzbar fallback ───────────────────────────────────────────────────────
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode  # type: ignore
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        barcodes = pyzbar_decode(gray)
        for bc in barcodes:
            if bc.type in ("QRCODE", "QR_CODE"):
                rx, ry, rw, rh = bc.rect
                detections.append(Detection(
                    label="qr_code",
                    text="",
                    box=(int(rx), int(ry), int(rw), int(rh)),
                    confidence=100.0,
                ))
    except ImportError:
        logger.debug("pyzbar not installed; skipping fallback QR detection")
    except Exception as exc:
        logger.debug("pyzbar QR detection failed: %s", exc)

    # ── Contour-based QR fallback (right side of card) ───────────────────────
    if not detections:
        qr_det = _detect_qr_by_contour(image)
        if qr_det:
            detections.append(qr_det)

    return detections


def _detect_qr_by_contour(image: Image.Image) -> Optional[Detection]:
    """
    Heuristic: the QR block on a PAN card is a dense dark square in the
    right half of the card.  Use contour analysis to find it.
    """
    img_w, img_h = image.size
    cv_img = _pil_to_cv(image)

    # Search only the right ~45% of the card
    roi_x1 = int(img_w * 0.55)
    roi    = cv_img[0:img_h, roi_x1:img_w]

    gray   = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for cnt in contours:
        rx, ry, rw, rh = cv2.boundingRect(cnt)
        area   = rw * rh
        aspect = rw / max(rh, 1)
        # QR codes are roughly square and cover a sizeable area
        if 0.6 < aspect < 1.6 and area > (img_w * img_h * 0.03):
            candidates.append((rx, ry, rw, rh, area))

    if not candidates:
        return None

    rx, ry, rw, rh, _ = max(candidates, key=lambda c: c[4])
    return Detection(
        label="qr_code",
        text="",
        box=(roi_x1 + rx, ry, rw, rh),
        confidence=100.0,
    )


# ── Utility ───────────────────────────────────────────────────────────────────

def _pil_to_cv(image: Image.Image) -> np.ndarray:
    """Convert a PIL Image (RGB) to an OpenCV BGR ndarray."""
    rgb = image.convert("RGB")
    return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
