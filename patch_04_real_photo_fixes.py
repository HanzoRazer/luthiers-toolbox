"""
PATCH 04 — Real-Photo Pipeline Fixes
======================================

Failures diagnosed on Jumbo_Tiger_Maple_Archtop (1024×1536, dark wood background):

  FAILURE 1 — False coin detection (mpp 7x wrong)
    Wood planks after inversion → 357 Hough circles, largest 398px diameter
    Treated as US quarter (24.26mm) → mpp=0.061 → body reads 62mm not 430mm
    Fix: reject coins whose diameter > MAX_COIN_FRACTION of min(w, h)

  FAILURE 2 — BodyIsolator row-width profiling fails on inverted textured background
    Wood grain planks after inversion have wide dark horizontal bands
    Body rows detected: 1015-1257 (242px) instead of ~400-1000 (600px)
    Fix: BodyIsolator must run on fg_mask (from BG removal) not raw thresholded image
         If no mask, run on PRE-inversion image (pass original_image separately)

  FAILURE 3 — Background type detection: "dark background" ≠ "invert and proceed"
    Dark wood background is NOT a solid dark matte — it has texture and detail
    Inverting it creates a complex light background that breaks everything downstream
    Fix: Add TEXTURED_DARK_BG detection; use GrabCut/rembg instead of invert

Three drop-in fixes below.  Integration notes at bottom of each class.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FIX 1 — ReferenceObjectDetector: coin size sanity filter
# =============================================================================

# A real reference coin/card photographed alongside a guitar occupies at most
# ~15% of the image's shorter dimension.  Anything larger is a false positive
# from background texture or guitar hardware.
MAX_COIN_DIAMETER_FRACTION = 0.15   # of min(image_w, image_h)
MIN_COIN_DIAMETER_PX = 12           # below this it's noise

def filter_coin_detections(circles: np.ndarray, image_shape: Tuple[int, int],
                           min_px: int = MIN_COIN_DIAMETER_PX,
                           max_fraction: float = MAX_COIN_DIAMETER_FRACTION,
                           ) -> np.ndarray:
    """
    Remove implausibly large or small circles from HoughCircles output.

    Parameters
    ----------
    circles     : np.ndarray shape (N, 3) of [x, y, r]
    image_shape : (height, width)
    min_px      : minimum diameter in pixels
    max_fraction: maximum diameter as fraction of min(h, w)

    Returns filtered array, same shape.
    """
    h, w = image_shape
    max_diameter = min(h, w) * max_fraction
    filtered = []
    for x, y, r in circles:
        diameter = 2 * r
        if diameter < min_px:
            logger.debug(f"Coin rejected (too small): r={r}px at ({x},{y})")
            continue
        if diameter > max_diameter:
            logger.debug(f"Coin rejected (too large {diameter:.0f}px > {max_diameter:.0f}px): at ({x},{y})")
            continue
        filtered.append([x, y, r])
    logger.info(f"Coin filter: {len(circles)} → {len(filtered)} detections "
                f"(max_diameter={max_diameter:.0f}px)")
    return np.array(filtered, dtype=np.float32) if filtered else np.empty((0, 3))


class PatchedReferenceObjectDetector:
    """
    Drop-in replacement for ReferenceObjectDetector with coin size sanity filter.

    Integration: replace self.ref_detector = ReferenceObjectDetector()
                 with    self.ref_detector = PatchedReferenceObjectDetector()
    in ScaleCalibrator.__init__()
    """

    def __init__(self, instrument_specs: Optional[dict] = None):
        try:
            from photo_vectorizer_v2 import INSTRUMENT_SPECS
            self.specs = INSTRUMENT_SPECS.get("reference_objects", {})
        except ImportError:
            self.specs = {
                "us_quarter": (24.26, 24.26),
                "credit_card": (85.6, 53.98),
                "business_card": (88.9, 50.8),
            }

    def detect(self, image: np.ndarray):
        h, w = image.shape[:2]
        detections = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Coin detection
        raw_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=30, minRadius=20, maxRadius=200)

        if raw_circles is not None:
            raw = np.round(raw_circles[0]).astype(int)
            filtered = filter_coin_detections(raw, (h, w))
            for entry in filtered:
                x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
                for name in self.specs:
                    if "quarter" in name or "card" not in name:
                        detections.append({
                            "name": name, "type": "coin",
                            "diameter_px": 2 * r, "confidence": 0.5,
                        })
                        break

        # Card detection (unchanged — cards are rectangular, not affected by this bug)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10000:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect = max(cw, ch) / max(1, min(cw, ch))
                for card_name, (wm, hm) in [("credit_card", (85.6, 53.98))]:
                    expected = max(wm, hm) / min(wm, hm)
                    if abs(aspect - expected) / expected < 0.2:
                        detections.append({
                            "name": card_name, "type": "card",
                            "width_px": cw, "height_px": ch, "confidence": 0.7,
                        })
                        break

        logger.info(f"ReferenceObjectDetector: {len(detections)} detections after filtering")
        return detections


# =============================================================================
# FIX 2 — BodyIsolator: must use fg_mask or pre-inversion image
# =============================================================================

class PatchedBodyIsolator:
    """
    Drop-in replacement for BodyIsolator that:
      1. Prioritises fg_mask (from Stage 4 BG removal) over raw thresholding
      2. Accepts original_image (pre-inversion) as fallback
      3. Detects and warns when wood-grain / textured background is interfering

    Integration: replace self.body_isolator = BodyIsolator()
                 with    self.body_isolator = PatchedBodyIsolator()
    in PhotoVectorizerV2.__init__()

    Then in extract(), pass original_image:
        body_region = self.body_isolator.isolate(
            image,
            fg_mask=alpha_mask,
            original_image=original_before_inversion,  # ← NEW
        )
    """

    def __init__(self, body_width_min_pct: float = 0.40, smooth_window: int = 15):
        self.body_width_min = body_width_min_pct
        self.smooth_window = smooth_window

    def isolate(self, image: np.ndarray,
                fg_mask: Optional[np.ndarray] = None,
                original_image: Optional[np.ndarray] = None):
        """
        Returns a BodyRegion.

        Priority:
          1. fg_mask (most reliable — BG already removed)
          2. original_image (pre-inversion) dark pixel threshold
          3. image (current, possibly inverted) dark pixel threshold — WARNS if used
        """
        h, w = image.shape[:2]
        notes = []

        if fg_mask is not None and np.sum(fg_mask > 0) > (h * w * 0.05):
            # Use foreground mask — most reliable source
            row_widths = np.sum(fg_mask > 0, axis=1).astype(float)
            source = "fg_mask"
            notes.append("Row widths from fg_mask (Stage 4 output)")
        elif original_image is not None:
            # Use pre-inversion image
            gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY) \
                if len(original_image.shape) == 3 else original_image
            row_widths = np.sum(gray < 150, axis=1).astype(float)
            source = "original_image"
            notes.append("Row widths from pre-inversion image (dark pixel threshold)")
        else:
            # Raw image — warn if it may be inverted
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            mean_val = float(gray.mean())
            row_widths = np.sum(gray < 150, axis=1).astype(float)
            source = "image_raw"
            if mean_val > 160:
                notes.append(
                    "⚠️  Using raw (possibly inverted) image for body isolation — "
                    "results may be unreliable. Pass fg_mask or original_image.")
            else:
                notes.append("Row widths from raw image threshold")

        kernel = np.ones(self.smooth_window) / self.smooth_window
        smoothed = np.convolve(row_widths, kernel, mode='same')

        body_min_px = w * self.body_width_min
        body_rows = np.where(smoothed >= body_min_px)[0]

        if len(body_rows) == 0:
            body_start = int(h * 0.45)
            body_end = int(h * 0.97)
            confidence = 0.30
            notes.append(f"No body rows at {body_min_px:.0f}px threshold (source={source}) → fallback")
        else:
            body_start = int(body_rows[0])
            body_end = int(body_rows[-1])
            confidence = min(1.0, 0.50 + 0.005 * len(body_rows))
            notes.append(
                f"Body rows {body_start}–{body_end} "
                f"({len(body_rows)} rows ≥ {body_min_px:.0f}px, source={source})")

        body_h = body_end - body_start
        max_body_w = int(smoothed[body_start:body_end].max()) if body_h > 0 else 0

        # Column extent
        if fg_mask is not None and source == "fg_mask":
            body_strip = fg_mask[body_start:body_end, :]
        else:
            ref = original_image if original_image is not None else image
            gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY) if len(ref.shape) == 3 else ref
            body_strip = (gray[body_start:body_end, :] < 150).astype(np.uint8)

        col_widths = np.sum(body_strip > 0, axis=0)
        body_cols = np.where(col_widths > 0)[0]
        x_start = int(body_cols[0]) if len(body_cols) else 0
        x_end = int(body_cols[-1]) if len(body_cols) else w

        logger.info(
            f"PatchedBodyIsolator: x={x_start}–{x_end}, y={body_start}–{body_end}, "
            f"size={x_end-x_start}x{body_h}px, conf={confidence:.2f}, src={source}")

        # Import BodyRegion from main module
        try:
            from photo_vectorizer_v2 import BodyRegion
        except ImportError:
            from dataclasses import dataclass, field
            @dataclass
            class BodyRegion:
                x: int; y: int; width: int; height: int
                confidence: float; neck_end_row: int
                max_body_width_px: int; notes: list = field(default_factory=list)
                @property
                def bbox(self): return (self.x, self.y, self.width, self.height)
                @property
                def height_px(self): return self.height

        return BodyRegion(
            x=x_start, y=body_start, width=x_end - x_start, height=body_h,
            confidence=confidence, neck_end_row=body_start,
            max_body_width_px=max_body_w, notes=notes)


# =============================================================================
# FIX 3 — Background type detection: textured vs. solid dark
# =============================================================================

class BackgroundTypeDetector:
    """
    Distinguishes between:
      - SOLID_DARK    → safe to invert (e.g. black velvet, dark seamless paper)
      - TEXTURED_DARK → do NOT invert (e.g. wood grain, brick, fabric)
      - SOLID_LIGHT   → standard light background, no inversion needed
      - GRADIENT      → vignette or studio gradient

    The current pipeline inverts ALL dark backgrounds, which corrupts the
    pipeline when the background is textured (wood, stone, etc.).

    Usage in extract() — replace:
        is_dark_bg = detect_dark_background(image)
        if is_dark_bg:
            image = cv2.bitwise_not(image)

    With:
        from patch_04_real_photo_fixes import BackgroundTypeDetector
        bg_type = BackgroundTypeDetector().detect(image)
        result.dark_background_detected = bg_type in ("solid_dark",)
        if bg_type == "solid_dark":
            image = cv2.bitwise_not(image)
        elif bg_type == "textured_dark":
            # Use rembg or GrabCut with tight hint_rect — do NOT invert
            pass
    """

    def detect(self, image: np.ndarray,
               border_px: int = 60,
               dark_threshold: float = 0.65,
               texture_variance_threshold: float = 350.0,
               ) -> str:
        """
        Returns one of: "solid_dark", "textured_dark", "solid_light", "gradient"
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape[:2]
        border_px = min(border_px, h // 4, w // 4)

        top = gray[:border_px, :]
        bottom = gray[h - border_px:, :]
        left = gray[border_px:h - border_px, :border_px]
        right = gray[border_px:h - border_px, w - border_px:]

        border_pixels = np.concatenate([
            top.ravel(), bottom.ravel(), left.ravel(), right.ravel()])
        dark_ratio = float(np.mean(border_pixels < 80))
        mean_brightness = float(border_pixels.mean())

        if dark_ratio < dark_threshold:
            # Light or gradient background
            brightness_range = float(border_pixels.max() - border_pixels.min())
            return "gradient" if brightness_range > 80 else "solid_light"

        # Dark background confirmed — check texture
        # Sample 4 border patches and compute variance
        patches = [top, bottom, left.T, right.T]
        variances = [float(np.var(p)) for p in patches if p.size > 0]
        mean_variance = float(np.mean(variances)) if variances else 0.0

        bg_type = "solid_dark" if mean_variance < texture_variance_threshold else "textured_dark"

        logger.info(
            f"BackgroundTypeDetector: dark_ratio={dark_ratio:.1%}, "
            f"border_variance={mean_variance:.0f} → {bg_type}")

        return bg_type


# =============================================================================
# Integration diff for PhotoVectorizerV2.extract()
# =============================================================================

INTEGRATION_DIFF = """
In photo_vectorizer_v2.py, make these three targeted changes:

──────────────────────────────────────────────────────────────────
CHANGE 1: Add imports at top of extract() or __init__()
──────────────────────────────────────────────────────────────────
from patch_04_real_photo_fixes import (
    PatchedReferenceObjectDetector,
    PatchedBodyIsolator,
    BackgroundTypeDetector,
)

──────────────────────────────────────────────────────────────────
CHANGE 2: In __init__(), replace isolator + patch calibrator's detector
──────────────────────────────────────────────────────────────────
# was: self.body_isolator = BodyIsolator()
self.body_isolator = PatchedBodyIsolator()

# was: self.calibrator = ScaleCalibrator(default_dpi)
# ScaleCalibrator uses ReferenceObjectDetector internally — patch it:
self.calibrator = ScaleCalibrator(default_dpi)
self.calibrator.ref_detector = PatchedReferenceObjectDetector()

──────────────────────────────────────────────────────────────────
CHANGE 3: In _extract_image() / extract(), replace the dark-bg block
──────────────────────────────────────────────────────────────────
# BEFORE:
is_dark_bg = detect_dark_background(image)
result.dark_background_detected = is_dark_bg
if is_dark_bg:
    image = cv2.bitwise_not(image)

# AFTER:
original_image = image.copy()   # ← save before any inversion
bg_type = BackgroundTypeDetector().detect(image)
is_dark_bg = (bg_type == "solid_dark")
result.dark_background_detected = is_dark_bg
if bg_type == "solid_dark":
    image = cv2.bitwise_not(image)
    logger.info("Solid dark background → image inverted")
elif bg_type == "textured_dark":
    logger.info("Textured dark background detected — NOT inverting; using rembg/grabcut")
    result.warnings.append(
        f"Textured dark background ({bg_type}) — consider using --bg rembg for best results")

──────────────────────────────────────────────────────────────────
CHANGE 4: Pass original_image to body_isolator (after Stage 4)
──────────────────────────────────────────────────────────────────
# was: body_region = self.body_isolator.isolate(image, fg_mask=alpha_mask)
body_region = self.body_isolator.isolate(
    image,
    fg_mask=alpha_mask,
    original_image=original_image,   # ← pre-inversion image
)
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    path = sys.argv[1] if len(sys.argv) > 1 else \
        "/mnt/user-data/uploads/Jumbo_Tiger_Maple_Archtop_Guitar_with_a_Florentine_Cutaway.png"
    img = cv2.imread(path)
    h, w = img.shape[:2]

    print(f"\nImage: {w}×{h}")

    # Fix 3: background type
    bg_det = BackgroundTypeDetector()
    bg_type = bg_det.detect(img)
    print(f"\nFix 3 — Background type: {bg_type}")
    should_invert = (bg_type == "solid_dark")
    print(f"  Invert? {should_invert}  (was: True — WRONG)")

    # Fix 1: coin filter on INVERTED image (what pipeline currently does)
    inv = cv2.bitwise_not(img)
    gray_inv = cv2.cvtColor(inv, cv2.COLOR_BGR2GRAY)
    raw_circles = cv2.HoughCircles(
        gray_inv, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
        param1=50, param2=30, minRadius=20, maxRadius=200)

    if raw_circles is not None:
        raw = np.round(raw_circles[0]).astype(int)
        filtered = filter_coin_detections(raw, (h, w))
        print(f"\nFix 1 — Coin filter: {len(raw)} raw → {len(filtered)} after filter")
        if len(filtered) == 0:
            print("  All false positives eliminated ✓")

    # Fix 2: body isolator with original image
    isolator = PatchedBodyIsolator()
    # Without mask, with original (NOT inverted) image
    region = isolator.isolate(inv, original_image=img)
    spec_h_mm = 520.0
    mpp = spec_h_mm / region.height_px if region.height_px > 0 else 0
    print(f"\nFix 2 — BodyIsolator (original_image fallback):")
    print(f"  Body region: {region.width}×{region.height}px @ ({region.x},{region.y})")
    print(f"  Confidence: {region.confidence:.2f}")
    print(f"  mpp @ spec 520mm: {mpp:.4f}")
    print(f"  Body width: {region.width * mpp:.0f}mm (expected ~430mm)")
    for note in region.notes:
        print(f"  Note: {note}")
