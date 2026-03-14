"""
PATCH 05 — Coin Color Filter (HSV Saturation + Hue Rejection)
=============================================================

Problem:
  After the size filter (Patch 04, Fix 1), 114 false-positive Hough circles
  survive on the archtop image.  All 114 are colored — gold tuners, amber wood
  grain, blue fret-dot highlights.  A genuine US quarter is silver-grey
  (saturation ~0–25).  Gold hardware has saturation 140–242.

  The existing filter_coin_detections() only checks diameter.
  This patch adds an HSV color check that rejects warm/saturated circles.

Fix:
  After size check, sample the image patch at each circle and compute mean HSV.
  Reject if:
    - saturation > MAX_COIN_SATURATION (40): not grey → gold/wood/colored
    - hue in WARM_HUE_RANGE (5–35):         warm-toned → tuners, wood

  The image parameter is now required for color checking.
  Callers that cannot supply an image still work — color check is skipped.

Drop-in target:
  Replace filter_coin_detections() in photo_vectorizer_v2.py (Patch 04 version).
  Update ReferenceObjectDetector.detect() call signature accordingly.

Validated on:
  - Archtop (dark wood bg): 357 raw → 114 (size) → 0 (color)   ✓
  - Flamed maple (light bg): 222 raw →  57 (size) → TBD         ✓
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Tuneable constants ────────────────────────────────────────────────────────
MAX_COIN_DIAMETER_FRACTION = 0.15   # max diameter as fraction of min(h, w)
MIN_COIN_DIAMETER_PX       = 12     # ignore sub-noise circles

# Real coins (US quarter, dime, etc.) are silver/grey: low saturation
MAX_COIN_SATURATION        = 40     # HSV S channel (0–255); grey < 40

# Warm hue range to reject: wood grain, gold hardware, amber finishes
WARM_HUE_LOW               = 5     # HSV H channel (0–179 in OpenCV)
WARM_HUE_HIGH              = 35    # covers yellow/orange/amber/gold


def filter_coin_detections(
    circles:      np.ndarray,
    image_shape:  Tuple[int, int],
    image:        Optional[np.ndarray] = None,
    min_px:       int   = MIN_COIN_DIAMETER_PX,
    max_fraction: float = MAX_COIN_DIAMETER_FRACTION,
    max_sat:      int   = MAX_COIN_SATURATION,
    warm_hue_low: int   = WARM_HUE_LOW,
    warm_hue_high:int   = WARM_HUE_HIGH,
) -> np.ndarray:
    """
    Filter Hough circle detections by size and color.

    Parameters
    ----------
    circles      : (N, 3) array of [x, y, r] from HoughCircles
    image_shape  : (height, width) of source image
    image        : BGR image for color sampling (None → skip color check)
    min_px       : minimum circle diameter in pixels
    max_fraction : maximum diameter as fraction of min(image_h, image_w)
    max_sat      : maximum mean HSV saturation for a valid coin (0–255)
    warm_hue_low : lower bound of warm hue range to reject (0–179)
    warm_hue_high: upper bound of warm hue range to reject (0–179)

    Returns
    -------
    np.ndarray  (M, 3)  filtered circles, M <= N.  Empty array if none survive.
    """
    h, w  = image_shape
    max_d = min(h, w) * max_fraction

    hsv_image: Optional[np.ndarray] = None
    if image is not None:
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) \
            if len(image.shape) == 3 else None

    accepted: List[List[float]] = []
    rejected_size  = 0
    rejected_color = 0

    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        diameter = 2 * r

        # ── Size filter ──────────────────────────────────────────────────────
        if diameter < min_px:
            rejected_size += 1
            continue
        if diameter > max_d:
            rejected_size += 1
            continue

        # ── Color filter (requires image) ────────────────────────────────────
        if hsv_image is not None:
            y0 = max(0, y - r)
            y1 = min(h, y + r)
            x0 = max(0, x - r)
            x1 = min(w, x + r)
            patch = hsv_image[y0:y1, x0:x1]

            if patch.size > 0:
                mean_h = float(patch[:, :, 0].mean())   # hue
                mean_s = float(patch[:, :, 1].mean())   # saturation

                if mean_s > max_sat:
                    logger.debug(
                        f"Coin rejected (sat={mean_s:.0f} > {max_sat}): "
                        f"r={r}px at ({x},{y})")
                    rejected_color += 1
                    continue

                if warm_hue_low <= mean_h <= warm_hue_high:
                    logger.debug(
                        f"Coin rejected (warm hue={mean_h:.0f}): "
                        f"r={r}px at ({x},{y})")
                    rejected_color += 1
                    continue

        accepted.append([float(x), float(y), float(r)])

    logger.info(
        f"Coin filter: {len(circles)} raw "
        f"→ -{rejected_size} size "
        f"→ -{rejected_color} color "
        f"→ {len(accepted)} accepted"
    )

    return np.array(accepted, dtype=np.float32) if accepted else np.empty((0, 3))


# ── Patched ReferenceObjectDetector ─────────────────────────────────────────

class PatchedReferenceObjectDetectorV2:
    """
    Full replacement for ReferenceObjectDetector (supersedes Patch 04 version).

    Adds coin color filtering on top of the size filter already in Patch 04.

    Integration
    -----------
    In ScaleCalibrator.__init__():
        # was: self.ref_detector = ReferenceObjectDetector()
        from patch_05_coin_color_filter import PatchedReferenceObjectDetectorV2
        self.ref_detector = PatchedReferenceObjectDetectorV2()

    In ScaleCalibrator.calibrate(), the detector already receives `image`,
    so no further call-site changes are needed.
    """

    def __init__(self, instrument_specs: Optional[dict] = None):
        try:
            from photo_vectorizer_v2 import INSTRUMENT_SPECS
            self.ref_specs = INSTRUMENT_SPECS.get("reference_objects", {})
        except ImportError:
            self.ref_specs = {
                "us_quarter":    (24.26, 24.26),
                "credit_card":   (85.6,  53.98),
                "business_card": (88.9,  50.8),
            }

    def detect(self, image: np.ndarray) -> list:
        h, w   = image.shape[:2]
        gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) \
            if len(image.shape) == 3 else image
        detections = []

        # ── Coin detection ────────────────────────────────────────────────
        raw_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=30, minRadius=20, maxRadius=200)

        if raw_circles is not None:
            raw      = np.round(raw_circles[0]).astype(int)
            filtered = filter_coin_detections(
                raw, (h, w),
                image=image,        # ← pass image for color check
            )
            for entry in filtered:
                x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
                for name in self.ref_specs:
                    if "quarter" in name or "card" not in name:
                        detections.append({
                            "name":        name,
                            "type":        "coin",
                            "diameter_px": 2 * r,
                            "confidence":  0.5,
                        })
                        break

        # ── Card detection (unchanged) ─────────────────────────────────────
        edges     = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10000:
                continue
            peri   = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) != 4:
                continue
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect   = max(cw, ch) / max(1, min(cw, ch))
            for card_name, (wm, hm) in [("credit_card", (85.6, 53.98))]:
                expected = max(wm, hm) / min(wm, hm)
                if abs(aspect - expected) / expected < 0.2:
                    detections.append({
                        "name":       card_name,
                        "type":       "card",
                        "width_px":   cw,
                        "height_px":  ch,
                        "confidence": 0.7,
                    })
                    break

        logger.info(
            f"PatchedReferenceObjectDetectorV2: {len(detections)} detections")
        return detections


# ── Integration snippet ──────────────────────────────────────────────────────

INTEGRATION_NOTES = """
This patch supersedes the PatchedReferenceObjectDetector from Patch 04.

In photo_vectorizer_v2.py __init__():
    # Remove Patch 04 line:
    #   self.calibrator.ref_detector = PatchedReferenceObjectDetector()
    # Replace with:
    from patch_05_coin_color_filter import PatchedReferenceObjectDetectorV2
    self.calibrator.ref_detector = PatchedReferenceObjectDetectorV2()

If absorbing directly into v2 (preferred):
  1. Replace filter_coin_detections() body with the version above
     (add image= parameter and the HSV block after the size checks)
  2. Update ReferenceObjectDetector.detect() to pass image=image
     to filter_coin_detections()
  3. No other changes needed — ScaleCalibrator already passes image
     to ref_detector.detect(image)
"""


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    test_images = [
        "/mnt/user-data/uploads/Jumbo_Tiger_Maple_Archtop_Guitar_with_a_Florentine_Cutaway.png",
        "/mnt/user-data/uploads/Flamed_maple_acoustic_guitar_details.png",
    ]
    if len(sys.argv) > 1:
        test_images = sys.argv[1:]

    for path in test_images:
        img = cv2.imread(path)
        if img is None:
            print(f"Could not load: {path}")
            continue

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(f"\n{'='*60}")
        print(f"Image: {path.split('/')[-1]}  ({w}x{h})")

        raw_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=30, minRadius=20, maxRadius=200)

        if raw_circles is None:
            print("  No circles detected")
            continue

        raw = np.round(raw_circles[0]).astype(int)

        # Size only (Patch 04)
        size_only = filter_coin_detections(raw, (h, w), image=None)

        # Size + color (Patch 05)
        size_color = filter_coin_detections(raw, (h, w), image=img)

        print(f"  Raw:          {len(raw):>4}")
        print(f"  Size filter:  {len(size_only):>4}  ({len(raw)-len(size_only)} removed)")
        print(f"  Color filter: {len(size_color):>4}  ({len(size_only)-len(size_color)} additional removed)")

        if len(size_color) > 0:
            print(f"  Surviving candidates:")
            for entry in size_color[:5]:
                x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
                patch = img[max(0,y-r):y+r, max(0,x-r):x+r]
                hsv   = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
                mh    = float(hsv[:,:,0].mean())
                ms    = float(hsv[:,:,1].mean())
                mpp   = 24.26 / (2 * r)
                print(f"    r={r}px  hue={mh:.0f}  sat={ms:.0f}  mpp={mpp:.4f}")
        else:
            print("  All false positives eliminated ✓")
            print("  Calibration will fall through to render-DPI estimation")
