"""
ocr_calibrator.py
=================
Reads the in-game coordinate display via Tesseract OCR and returns the
current map position as (kingdom_id, map_x, map_y).

Used for two purposes:
  1. Auto-calibration: verify the scanner's internal grid position matches
     the game's reported coordinates.
  2. Enriching find-log entries with accurate map coordinates.

Expected on-screen text format (examples):
    K:1024  X:312  Y:  87
    K1024 X312 Y87
    [K=1024] (312, 87)
"""

from __future__ import annotations

import re

import cv2
import numpy as np
import pytesseract


# Compiled patterns so they are not re-compiled on every call
_RE_KINGDOM = re.compile(r"K[:\s=]*(\d{3,4})", re.IGNORECASE)
_RE_X       = re.compile(r"X[:\s=]*(\d+)",      re.IGNORECASE)
_RE_Y       = re.compile(r"Y[:\s=]*(\d+)",      re.IGNORECASE)


def _preprocess(bgra_crop: np.ndarray) -> np.ndarray:
    """Convert a BGRA capture to a binarised grayscale image for OCR."""
    gray = cv2.cvtColor(bgra_crop, cv2.COLOR_BGRA2GRAY)
    # OTSU binarisation handles varying HUD brightness automatically
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # 2× upscale – Tesseract is much more accurate on larger text
    thresh = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    return thresh


def _parse_int(pattern: re.Pattern, text: str) -> int | None:
    m = pattern.search(text)
    return int(m.group(1)) if m else None


def read_map_coords(
    sct,
    region: dict,
    tesseract_path: str | None = None,
) -> tuple[int | None, int | None, int | None]:
    """Grab *region* from the screen and OCR the coordinate string.

    Parameters
    ----------
    sct:
        An active ``mss.mss()`` instance.
    region:
        A dict with keys ``left``, ``top``, ``width``, ``height`` (screen-px).
    tesseract_path:
        Absolute path to ``tesseract.exe`` on Windows, or None to use PATH.

    Returns
    -------
    (kingdom_id, map_x, map_y) – any component is None if OCR could not parse it.
    """
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    raw  = np.array(sct.grab(region))
    proc = _preprocess(raw)

    # PSM 7 = single text line; whitelist keeps only digits and label chars
    config = (
        "--psm 7 "
        "-c tessedit_char_whitelist=0123456789KXYkxy:=.,[] "
    )
    try:
        text = pytesseract.image_to_string(proc, config=config).strip()
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("  [OCR] Tesseract not found – coordinate calibration disabled.")
        return None, None, None

    kingdom_id = _parse_int(_RE_KINGDOM, text)
    map_x      = _parse_int(_RE_X,       text)
    map_y      = _parse_int(_RE_Y,       text)

    return kingdom_id, map_x, map_y


def format_coords(kingdom_id: int | None, map_x: int | None, map_y: int | None) -> str:
    """Return a compact human-readable coordinate string."""
    k = f"K{kingdom_id}" if kingdom_id is not None else "K?"
    x = f"X{map_x}"      if map_x      is not None else "X?"
    y = f"Y{map_y}"      if map_y      is not None else "Y?"
    return f"{k} {x} {y}"
