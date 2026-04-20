"""
scanner.py
==========
Two-Tier Mercenary Exchange Scanner.

Tier 1  –  "The Sprinter"
    Ultra-fast HSV colour threshold on the raw frame.
    If the purple-pixel count exceeds a configurable threshold, Tier 2 fires.
    This keeps CPU near-idle for the vast majority of boring map tiles.

Tier 2  –  "The Judge"
    cv2.matchTemplate against a provided exchange_template.png crop.
    Only runs when Tier 1 raises a flag, so the heavier template computation
    is seldom executed.

Delta Detection (pre-filter)
    Before either tier runs, a perceptual hash (pHash) of the current frame
    is compared to the hash stored for that grid position on the previous pass.
    A Hamming distance ≤ 2 is treated as "no change" and the frame is skipped
    entirely.  This eliminates redundant work caused by overshoot / settle jitter.
"""

from __future__ import annotations

import cv2
import numpy as np

try:
    import imagehash
    from PIL import Image
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    _IMAGEHASH_AVAILABLE = False
    print(
        "  [Scanner] imagehash / Pillow not installed – "
        "delta detection disabled.  Run: pip install ImageHash Pillow"
    )

# Hamming-distance ceiling for "identical frame" decision.
# 0 = pixel-perfect identical; 2 = tolerates minor animation frames.
_HASH_DUPLICATE_THRESHOLD = 2


class TwoTierScanner:
    """Stateful two-tier scanner.  One instance is shared across the full run."""

    def __init__(
        self,
        hsv_lower:        np.ndarray,
        hsv_upper:        np.ndarray,
        pixel_threshold:  int,
        template_path:    str,
        match_threshold:  float,
    ):
        self.hsv_lower       = hsv_lower
        self.hsv_upper       = hsv_upper
        self.pixel_threshold = pixel_threshold
        self.match_threshold = match_threshold

        self._template: np.ndarray = self._load_template(template_path)

        # position_key → imagehash.ImageHash from the previous scan pass
        self._prev_hashes: dict[str, object] = {}

    # ── template loading ─────────────────────────────────────────────────────

    @staticmethod
    def _load_template(path: str) -> np.ndarray:
        tmpl = cv2.imread(path, cv2.IMREAD_COLOR)
        if tmpl is None:
            raise FileNotFoundError(
                f"Exchange template not found: {path}\n"
                "Place a cropped screenshot of the exchange icon at that path."
            )
        return tmpl

    # ── frame conversion ─────────────────────────────────────────────────────

    @staticmethod
    def _to_bgr(frame: np.ndarray) -> np.ndarray:
        """Convert BGRA (mss output) → BGR for OpenCV operations."""
        if frame.ndim == 3 and frame.shape[2] == 4:
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    # ── delta detection ──────────────────────────────────────────────────────

    def is_duplicate_frame(self, frame_bgr: np.ndarray, position_key: str) -> bool:
        """Return True when this frame is perceptually identical to the last
        frame captured at the same grid position (Hamming distance ≤ threshold).
        Always returns False when imagehash is unavailable.
        """
        if not _IMAGEHASH_AVAILABLE:
            return False

        pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        current_hash = imagehash.phash(pil_img)

        prev = self._prev_hashes.get(position_key)
        self._prev_hashes[position_key] = current_hash   # update for next pass

        if prev is None:
            return False

        return (current_hash - prev) <= _HASH_DUPLICATE_THRESHOLD

    # ── Tier 1: colour threshold ──────────────────────────────────────────────

    def tier1_color_check(self, frame_bgr: np.ndarray) -> bool:
        """Return True when the frame contains enough Exchange-purple pixels."""
        hsv  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        # mask values are 0 or 255; dividing by 255 gives white-pixel count
        return int(np.count_nonzero(mask)) >= self.pixel_threshold

    # ── Tier 2: template match ────────────────────────────────────────────────

    def tier2_template_match(
        self, frame_bgr: np.ndarray
    ) -> list[tuple[int, int]]:
        """Return a list of (x, y) screen positions where the template matched,
        or an empty list when confidence is below the threshold.
        """
        result    = cv2.matchTemplate(frame_bgr, self._template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= self.match_threshold)
        # zip(cols, rows) → (x, y) pairs
        return list(zip(locations[1].tolist(), locations[0].tolist()))

    # ── combined entry point ──────────────────────────────────────────────────

    def scan(
        self, frame_bgra: np.ndarray, position_key: str
    ) -> tuple[bool, list[tuple[int, int]]]:
        """Run the full two-tier scan pipeline on one captured frame.

        Returns
        -------
        (triggered_tier2, matches)
            triggered_tier2 – True when Tier 1 flagged the frame.
            matches         – List of (x, y) match positions (empty if Tier 1
                              did not trigger or Tier 2 found nothing).
        """
        frame_bgr = self._to_bgr(frame_bgra)

        # Pre-filter: skip identical frames
        if self.is_duplicate_frame(frame_bgr, position_key):
            return False, []

        # Tier 1: fast colour gate
        if not self.tier1_color_check(frame_bgr):
            return False, []

        # Tier 2: expensive template match (only reaches here ~rarely)
        matches = self.tier2_template_match(frame_bgr)
        return True, matches
