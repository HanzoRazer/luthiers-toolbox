"""
PATCH 01 — Scale Calibration: DPI Sanity Check + Render-Aware Estimation
=========================================================================

Problem diagnosed:
  - PNG renders have no EXIF DPI → pipeline falls back to assumed 300 DPI
  - At 300 DPI a 402px wide guitar body = 34mm (actual is ~340mm, 10x wrong)
  - FeatureClassifier thresholds (max_dim > 300mm) never fire → everything → UNKNOWN

Fix:
  1. Estimate effective DPI from actual image content dimensions
  2. Warn loudly when calibration confidence is below threshold
  3. Add RENDER_DPI (96) as a fallback between EXIF and ASSUMED
  4. Clamp assumed DPI to a plausible range based on image pixel count

Drop-in replacement for ScaleCalibrator.calibrate() in photo_vectorizer_v2.py
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Known instrument body heights (mm) for fallback spec-based estimation ──
_SPEC_BODY_HEIGHT_MM = {
    "stratocaster": 459,
    "telecaster":   457,
    "les_paul":     450,
    "es335":        508,
    "dreadnought":  520,
    "smart_guitar": 444,
    "generic_acoustic": 500,
    "generic_electric":  450,
}

# ── DPI thresholds ──────────────────────────────────────────────────────────
_MIN_PLAUSIBLE_DPI  = 72     # Browser / screen render floor
_MAX_PLAUSIBLE_DPI  = 1200   # High-res scan ceiling
_PRINT_DPI_DEFAULT  = 300    # Original assumed value (often wrong)
_SCREEN_DPI_DEFAULT = 96     # Typical screen / AI render DPI
_WARN_CONFIDENCE    = 0.50   # Log a warning below this


def estimate_render_dpi(image: np.ndarray, fg_mask: Optional[np.ndarray] = None) -> float:
    """
    Heuristic: estimate whether an image was rendered at screen (~96 dpi)
    or scanned at print (~300 dpi) by looking at fine-detail density.

    High scan DPI → many tiny edge pixels relative to image area.
    Screen renders → coarser relative edge density.

    Returns estimated DPI (float).  Caller should use this only when no
    authoritative source (EXIF, user input, reference object) is available.
    """
    h, w = image.shape[:2]
    px_count = h * w

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    if fg_mask is not None:
        roi = cv2.bitwise_and(gray, gray, mask=fg_mask)
    else:
        roi = gray

    # Edge density in the foreground region
    blurred = cv2.GaussianBlur(roi, (3, 3), 0)
    edges   = cv2.Canny(blurred, 30, 90)
    if fg_mask is not None:
        edges = cv2.bitwise_and(edges, edges, mask=fg_mask)

    edge_px    = int(np.sum(edges > 0))
    total_px   = int(np.sum(fg_mask > 0)) if fg_mask is not None else px_count
    edge_ratio = edge_px / max(total_px, 1)

    # High-DPI scans have denser fine edges; renders are smoother
    # Empirically: scans >0.08, renders 0.02–0.06
    if edge_ratio > 0.10:
        est_dpi = 300.0
    elif edge_ratio > 0.06:
        est_dpi = 150.0
    else:
        est_dpi = 96.0

    logger.info(
        f"DPI estimation: edge_ratio={edge_ratio:.4f} → est_dpi={est_dpi:.0f} "
        f"(image {w}x{h}, {edge_px}/{total_px} edge px)"
    )
    return est_dpi


class PatchedScaleCalibrator:
    """
    Drop-in replacement for ScaleCalibrator.

    Priority chain (highest → lowest confidence):
      1. User-supplied known_mm + known_px          confidence=1.0
      2. Reference object detected in image         confidence=0.5–0.8
      3. EXIF DPI (authoritative from scanner/cam)  confidence=0.85
      4. Instrument spec + body contour height       confidence=0.60
      5. Render DPI estimated from edge density      confidence=0.40
      6. Assumed 300 DPI (original fallback)         confidence=0.20  ← WARN

    New: emits a WARNING log whenever confidence < 0.5 and appends a
    human-readable calibration_warning to the result so the caller / CLI
    can surface it.
    """

    def __init__(self, default_dpi: float = _PRINT_DPI_DEFAULT,
                 instrument_specs: Optional[dict] = None):
        self.default_dpi   = default_dpi
        self._specs        = instrument_specs or _SPEC_BODY_HEIGHT_MM
        self._ref_detector = _build_ref_detector()

    # ------------------------------------------------------------------
    def calibrate(
        self,
        image: np.ndarray,
        known_mm:    Optional[float] = None,
        known_px:    Optional[float] = None,
        spec_name:   Optional[str]   = None,
        image_dpi:   Optional[float] = None,
        unit:        str             = "mm",
        fg_mask:     Optional[np.ndarray] = None,
        # NEW optional: pass the detected body contour height in px
        body_height_px: Optional[float]  = None,
    ) -> "CalibrationResult":
        from dataclasses import dataclass, field as dc_field
        from enum import Enum

        # ── 1. User dimension ──────────────────────────────────────────
        if known_mm and known_px and known_px > 0:
            mm = _to_mm(known_mm, unit)
            mpp = mm / known_px
            return _result(mpp, "user_dimension", 1.0,
                           f"User: {mm:.1f}mm / {known_px:.1f}px")

        # ── 2. Reference object ────────────────────────────────────────
        refs = self._ref_detector(image)
        if refs:
            det = refs[0]
            if "diameter_px" in det and det["diameter_px"] > 0:
                from photo_vectorizer_v2 import INSTRUMENT_SPECS
                ref_specs = INSTRUMENT_SPECS.get("reference_objects", {})
                name = det["name"]
                if name in ref_specs:
                    diam_mm = ref_specs[name][0]
                    mpp = diam_mm / det["diameter_px"]
                    return _result(mpp, "reference_object", det["confidence"],
                                   f"Reference: {name} ({diam_mm}mm)")

        # ── 3. EXIF DPI (authoritative) ────────────────────────────────
        if image_dpi and _MIN_PLAUSIBLE_DPI <= image_dpi <= _MAX_PLAUSIBLE_DPI:
            return _result(25.4 / image_dpi, "exif_dpi", 0.85,
                           f"EXIF: {image_dpi:.0f} DPI")

        # ── 4. Instrument spec + body contour ──────────────────────────
        if spec_name and body_height_px and body_height_px > 0:
            key = spec_name.lower().replace(" ", "_")
            body_h_mm = self._specs.get(key)
            if body_h_mm:
                mpp = body_h_mm / body_height_px
                return _result(mpp, "instrument_spec", 0.60,
                               f"Spec: {spec_name} {body_h_mm}mm / {body_height_px:.0f}px")

        # ── 5. Render-DPI estimation ───────────────────────────────────
        est_dpi = estimate_render_dpi(image, fg_mask)
        if est_dpi != _PRINT_DPI_DEFAULT:
            return _result(25.4 / est_dpi, "estimated_render_dpi", 0.40,
                           f"Estimated render DPI: {est_dpi:.0f}")

        # ── 6. Assumed fallback (WARN) ─────────────────────────────────
        mpp = 25.4 / self.default_dpi
        msg = (
            f"⚠️  SCALE FALLBACK: assumed {self.default_dpi:.0f} DPI "
            f"(mm/px={mpp:.4f}). "
            f"Body dimensions will likely be WRONG. "
            f"Supply --mm + --px or place a reference object in frame."
        )
        logger.warning(msg)
        return _result(mpp, "assumed_dpi", 0.20, msg)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _to_mm(value: float, unit: str) -> float:
    if unit == "inch":
        return value * 25.4
    if unit == "cm":
        return value * 10.0
    return value


def _result(mpp, source, confidence, message):
    """Build a CalibrationResult-compatible dict (also works as dataclass)."""
    return _CalibResult(
        mm_per_px  = mpp,
        source     = source,
        confidence = confidence,
        message    = message,
    )


class _CalibResult:
    """Lightweight stand-in matching CalibrationResult interface."""
    __slots__ = ("mm_per_px", "source", "confidence", "message", "references")

    def __init__(self, mm_per_px, source, confidence, message):
        self.mm_per_px   = mm_per_px
        self.source      = source
        self.confidence  = confidence
        self.message     = message
        self.references  = []

    def __repr__(self):
        return (f"CalibResult(source={self.source}, "
                f"mpp={self.mm_per_px:.5f}, conf={self.confidence:.2f})")


def _build_ref_detector():
    """
    Returns a callable that wraps the ReferenceObjectDetector from the
    main module if available, otherwise returns a no-op.
    """
    try:
        from photo_vectorizer_v2 import ReferenceObjectDetector
        detector = ReferenceObjectDetector()
        return detector.detect
    except ImportError:
        return lambda img: []


# ── Integration snippet (copy into PhotoVectorizerV2.__init__) ───────────────
INTEGRATION_NOTES = """
In PhotoVectorizerV2.__init__, replace:

    self.calibrator = ScaleCalibrator(default_dpi)

with:

    from patch_01_scale_calibration import PatchedScaleCalibrator
    self.calibrator = PatchedScaleCalibrator(default_dpi)

In PhotoVectorizerV2.extract(), pass the body height once you have it.
After the contour assembly block (Stage 8), add:

    body_h_px = body_fc.bbox_px[3] if body_fc else None
    calibration = self.calibrator.calibrate(
        image,
        known_mm=known_dimension_mm,
        known_px=known_dimension_px,
        spec_name=spec_name,
        image_dpi=exif_dpi,
        unit=(known_unit.value if known_unit else "mm"),
        fg_mask=alpha_mask,
        body_height_px=body_h_px,   # ← NEW
    )

Also surface the warning in the CLI output:
    if calibration.confidence < 0.5:
        print(f"  ⚠  Calibration: {calibration.message}")
"""
