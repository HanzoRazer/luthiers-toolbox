"""
PATCH 16 — Perspective Diagnostic + Auto-Perspective Correction
================================================================

Context from live tests (Patches 12–14):
  After Fix B (11×11 close) the Smart Guitar height residual is predicted
  at ~15%. The strategic analysis showed:
    - Pre-patch 43% error: clearly fragmentation (not perspective)
    - Post-patch 15% residual: MIXED — could be fragmentation remnant
      or genuine camera foreshortening (max ~13% at 30° camera angle)

  The developer suggested an --auto-perspective flag to diagnose this.

This patch provides:

  PerspectiveDiagnostic
    Analyses the body contour asymmetry and aspect ratio to estimate
    whether camera foreshortening is contributing to height error.
    Returns a perspective estimate and recommendation.

  AutoPerspectiveCorrector
    If perspective distortion is detected above a threshold, applies
    an inverse vertical stretch to the contour coordinates (mm space)
    to recover the true body height.
    Does NOT modify the image — operates on extracted mm contours.

  --auto-perspective CLI flag integration
    Runs PerspectiveDiagnostic after extract() and optionally applies
    AutoPerspectiveCorrector based on confidence threshold.

Theory:
  For a guitar body photographed at angle θ from horizontal:
    apparent_height = true_height × cos(θ)
    apparent_width  = true_width  × cos(φ)   where φ is lateral angle

  For a standard product photo (camera above, pointing slightly down):
    θ ≈ 10–20° → height foreshortened by 2–6%
    φ ≈ 0–5°  → width nearly unaffected

  Diagnostic: compare body contour aspect ratio to expected spec aspect.
    If measured_aspect / spec_aspect < 0.92 and calibration is good
    (confidence > 0.5), perspective is likely contributing.

  The width being 0.8% accurate on Smart Guitar (coin calibration)
  while height is 15% off is consistent with θ ≈ 20° downward camera:
    cos(20°) = 0.940 → height foreshortened by 6% (partial explanation)
    residual 9% likely still fragmentation requiring wider close kernel

Author: The Production Shop
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# Perspective Diagnostic
# =============================================================================

@dataclass
class PerspectiveAssessment:
    """Result of perspective distortion analysis."""
    estimated_angle_deg:   float     # estimated camera tilt angle
    height_foreshorten_pct: float    # estimated % height reduction
    width_affected_pct:    float     # estimated % width reduction (usually ~0)
    confidence:            float     # confidence in this assessment
    recommendation:        str       # "apply_correction" | "minor" | "none"
    corrected_height_mm:   Optional[float]  # corrected height if applicable
    notes:                 List[str] = field(default_factory=list)


class PerspectiveDiagnostic:
    """
    Analyses body contour geometry to estimate camera perspective distortion.

    Parameters
    ----------
    min_calibration_conf  : minimum calibration confidence to run diagnostic
                            (below this, dimension errors may be calibration,
                             not perspective)
    angle_threshold_deg   : minimum estimated angle to flag as significant
    spec_table            : {spec_name: (height_mm, width_mm)} reference dims
    """

    _SPEC_DIMS = {
        "stratocaster":  (406, 325),
        "telecaster":    (406, 325),
        "les_paul":      (450, 340),
        "es335":         (500, 420),
        "dreadnought":   (520, 400),
        "smart_guitar":  (444.5, 368.3),
        "jumbo_archtop": (520, 430),
    }

    def __init__(
        self,
        min_calibration_conf: float = 0.45,
        angle_threshold_deg:  float = 8.0,
    ):
        self.min_cal_conf    = min_calibration_conf
        self.angle_threshold = angle_threshold_deg

    # ------------------------------------------------------------------
    def diagnose(
        self,
        extraction_result,
        spec_name: Optional[str] = None,
    ) -> PerspectiveAssessment:
        """
        Run perspective diagnostic on an extraction result.

        Parameters
        ----------
        extraction_result : PhotoExtractionResult
        spec_name         : instrument spec (uses result.calibration if None)

        Returns
        -------
        PerspectiveAssessment
        """
        notes = []

        cal   = getattr(extraction_result, 'calibration', None)
        cal_conf = cal.confidence if cal else 0.0
        body_h, body_w = getattr(extraction_result, 'body_dimensions_mm', (0, 0))

        if body_h <= 0 or body_w <= 0:
            return PerspectiveAssessment(
                estimated_angle_deg    = 0,
                height_foreshorten_pct = 0,
                width_affected_pct     = 0,
                confidence             = 0,
                recommendation         = "none",
                corrected_height_mm    = None,
                notes                  = ["No body dimensions available"])

        if cal_conf < self.min_cal_conf:
            return PerspectiveAssessment(
                estimated_angle_deg    = 0,
                height_foreshorten_pct = 0,
                width_affected_pct     = 0,
                confidence             = 0,
                recommendation         = "none",
                corrected_height_mm    = None,
                notes = [
                    f"Calibration confidence {cal_conf:.2f} < "
                    f"{self.min_cal_conf} — cannot distinguish "
                    "perspective from calibration error"])

        measured_aspect = body_h / max(body_w, 1.0)
        notes.append(f"Measured body: {body_h:.1f}×{body_w:.1f}mm "
                     f"(h/w={measured_aspect:.3f})")

        # Try to get expected aspect from spec
        spec_h = spec_w = None
        if spec_name and spec_name in self._SPEC_DIMS:
            spec_h, spec_w = self._SPEC_DIMS[spec_name]
        else:
            # Try to infer spec from body aspect clustering
            spec_h, spec_w, spec_name = self._guess_spec(
                body_h, body_w, measured_aspect, notes)

        if spec_h is None:
            return PerspectiveAssessment(
                estimated_angle_deg    = 0,
                height_foreshorten_pct = 0,
                width_affected_pct     = 0,
                confidence             = 0.2,
                recommendation         = "none",
                corrected_height_mm    = None,
                notes                  = notes + ["Cannot estimate without spec"])

        spec_aspect    = spec_h / spec_w
        aspect_ratio   = measured_aspect / spec_aspect  # < 1 means compressed height
        notes.append(f"Spec ({spec_name}): {spec_h}×{spec_w}mm "
                     f"(h/w={spec_aspect:.3f})")
        notes.append(f"Aspect ratio (measured/spec): {aspect_ratio:.3f}")

        # ── Width-based calibration sanity ───────────────────────────
        # If width is close to spec, calibration is probably right,
        # and height compression is likely perspective
        width_error = abs(body_w - spec_w) / spec_w
        height_error = abs(body_h - spec_h) / spec_h
        notes.append(f"Width error: {width_error:.1%}  Height error: {height_error:.1%}")

        if width_error > 0.20:
            notes.append("Width error > 20% — likely calibration issue, not perspective")
            return PerspectiveAssessment(
                estimated_angle_deg    = 0,
                height_foreshorten_pct = 0,
                width_affected_pct     = width_error * 100,
                confidence             = 0.3,
                recommendation         = "check_calibration",
                corrected_height_mm    = None,
                notes                  = notes)

        # ── Estimate camera angle from height compression ─────────────
        # apparent_height = true_height × cos(θ)
        # cos(θ) = body_h / spec_h  (if calibration is correct)
        cos_theta     = body_h / spec_h
        cos_theta     = max(0.1, min(1.0, cos_theta))  # clamp to valid range
        theta_rad     = math.acos(cos_theta)
        theta_deg     = math.degrees(theta_rad)
        foreshorten   = (1.0 - cos_theta) * 100.0

        notes.append(f"Estimated camera angle: {theta_deg:.1f}°")
        notes.append(f"Height foreshortening: {foreshorten:.1f}%")

        # ── Assess severity ──────────────────────────────────────────
        if theta_deg < self.angle_threshold:
            recommendation = "minor"
            confidence     = 0.6
            notes.append(
                f"Angle {theta_deg:.1f}° < threshold {self.angle_threshold}° "
                "— perspective is minor, fragmentation more likely")
        elif theta_deg < 25:
            recommendation = "apply_correction"
            confidence     = 0.70
            notes.append(
                f"Angle {theta_deg:.1f}° is significant — "
                "perspective correction recommended")
        else:
            # Very large angle → more likely contour fragmentation
            recommendation = "likely_fragmentation"
            confidence     = 0.55
            notes.append(
                f"Angle {theta_deg:.1f}° is very large — "
                "more likely contour fragmentation than perspective")

        # ── Corrected height estimate ────────────────────────────────
        corrected_h = spec_h if recommendation == "apply_correction" else None

        return PerspectiveAssessment(
            estimated_angle_deg    = round(theta_deg, 1),
            height_foreshorten_pct = round(foreshorten, 1),
            width_affected_pct     = round(width_error * 100, 1),
            confidence             = confidence,
            recommendation         = recommendation,
            corrected_height_mm    = corrected_h,
            notes                  = notes,
        )

    # ------------------------------------------------------------------
    def _guess_spec(
        self,
        body_h: float,
        body_w: float,
        measured_aspect: float,
        notes: List[str],
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Find the closest spec by body dimensions."""
        best_name, best_h, best_w, best_diff = None, None, None, float('inf')
        for name, (sh, sw) in self._SPEC_DIMS.items():
            spec_asp = sh / sw
            # Weight width match more heavily (width is usually more accurate)
            w_diff = abs(body_w - sw) / sw
            asp_diff = abs(measured_aspect - spec_asp)
            diff = w_diff * 0.6 + asp_diff * 0.4
            if diff < best_diff:
                best_diff = diff
                best_name, best_h, best_w = name, sh, sw

        if best_diff < 0.25:
            notes.append(f"Inferred spec: {best_name} (diff={best_diff:.3f})")
            return best_h, best_w, best_name
        notes.append(f"No spec match within 25% (best={best_name}, diff={best_diff:.3f})")
        return None, None, None


# =============================================================================
# Auto-Perspective Corrector
# =============================================================================

class AutoPerspectiveCorrector:
    """
    Applies inverse vertical stretch to mm contour coordinates to correct
    camera perspective foreshortening.

    Operates on the final export_contours dict (mm space), NOT on the image.
    This preserves all other processing (calibration, feature detection)
    while correcting the height dimension only.

    Parameters
    ----------
    max_correction_pct : maximum allowed height correction (default 20%)
                         prevents over-correction on badly fragmented contours
    """

    def __init__(self, max_correction_pct: float = 20.0):
        self.max_correction_pct = max_correction_pct

    def correct(
        self,
        contours_by_layer: Dict[str, List[np.ndarray]],
        assessment:        PerspectiveAssessment,
        body_dimensions_mm: Tuple[float, float],
    ) -> Tuple[Dict[str, List[np.ndarray]], float]:
        """
        Apply vertical stretch correction to all contours.

        Parameters
        ----------
        contours_by_layer  : {layer: [pts_mm, ...]}
        assessment         : PerspectiveAssessment from PerspectiveDiagnostic
        body_dimensions_mm : (height_mm, width_mm) currently reported

        Returns
        -------
        (corrected_contours, scale_factor_applied)
        """
        if assessment.recommendation not in ("apply_correction",):
            logger.info("AutoPerspectiveCorrector: no correction needed "
                        f"({assessment.recommendation})")
            return contours_by_layer, 1.0

        current_h, _ = body_dimensions_mm
        if current_h <= 0 or assessment.corrected_height_mm is None:
            return contours_by_layer, 1.0

        scale_y = assessment.corrected_height_mm / current_h

        # Cap correction
        max_scale = 1.0 + self.max_correction_pct / 100.0
        if scale_y > max_scale:
            logger.warning(
                f"AutoPerspectiveCorrector: scale_y={scale_y:.3f} exceeds "
                f"max {max_scale:.3f} — capping")
            scale_y = max_scale
        elif scale_y < 1.0:
            logger.info(
                f"AutoPerspectiveCorrector: scale_y={scale_y:.3f} < 1.0 "
                "— no correction applied (body already at spec height)")
            return contours_by_layer, 1.0

        logger.info(
            f"AutoPerspectiveCorrector: stretching Y by {scale_y:.4f} "
            f"({current_h:.1f}mm → {current_h*scale_y:.1f}mm)")

        corrected: Dict[str, List[np.ndarray]] = {}
        for layer, pts_list in contours_by_layer.items():
            corrected[layer] = []
            for pts in pts_list:
                stretched = pts.copy()
                stretched[:, 1] = stretched[:, 1] * scale_y
                corrected[layer].append(stretched)

        return corrected, scale_y


# =============================================================================
# CLI integration
# =============================================================================

CLI_INTEGRATION = """
Add to CLI in photo_vectorizer_v2.py:

    parser.add_argument("--auto-perspective", action="store_true",
        help="Auto-detect and correct camera perspective foreshortening")
    parser.add_argument("--perspective-threshold", type=float, default=8.0,
        help="Minimum camera angle (degrees) to trigger correction (default: 8.0)")

In main(), after extract() and before printing results:

    if args.auto_perspective:
        from patch_16_perspective_diagnostic import (
            PerspectiveDiagnostic, AutoPerspectiveCorrector)

        diag = PerspectiveDiagnostic(
            angle_threshold_deg=args.perspective_threshold)

        for result in results:
            assessment = diag.diagnose(result, spec_name=args.spec)

            print(f"  Perspective: angle~{assessment.estimated_angle_deg:.1f}° "
                  f"foreshortening~{assessment.height_foreshorten_pct:.1f}% "
                  f"[{assessment.recommendation}]")
            for note in assessment.notes:
                print(f"    {note}")

            if assessment.recommendation == "apply_correction":
                corrector = AutoPerspectiveCorrector()
                # Rebuild export contours from result.features
                export_contours = {
                    ft.value.upper(): [fc.points_mm for fc in fcs
                                       if fc.points_mm is not None]
                    for ft, fcs in result.features.items()
                }
                corrected, factor = corrector.correct(
                    export_contours, assessment,
                    result.body_dimensions_mm)
                print(f"  Applied Y-scale: {factor:.4f}")
                # Re-export SVG/DXF with corrected contours
                if result.output_svg:
                    from photo_vectorizer_v2 import write_svg
                    write_svg(corrected, result.output_svg.replace(
                        '_photo_v2.svg', '_perspective_corrected.svg'),
                        *calculate_viewbox(corrected))
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    diag      = PerspectiveDiagnostic()
    corrector = AutoPerspectiveCorrector()

    print("=" * 65)
    print("PATCH 16 — Perspective Diagnostic Self-Test")
    print("=" * 65)

    # Mock calibration result
    class MockCal:
        confidence = 0.60
        class source:
            value = "instrument_spec"

    class MockResult:
        def __init__(self, h, w):
            self.body_dimensions_mm = (h, w)
            self.calibration = MockCal()
            self.features = {}

    print(f"\n{'Scenario':<35} {'Angle':>7} {'Foreshr':>9} {'Conf':>6}  Recommendation")
    print("─" * 75)

    test_cases = [
        # (measured_h, measured_w, spec, label)
        (444.5, 368.3, "smart_guitar",  "Perfect (no distortion)"),
        (416.0, 368.0, "smart_guitar",  "~20° tilt (6% short)"),
        (380.0, 365.0, "smart_guitar",  "~31° tilt (15% short — post-patch)"),
        (251.5, 371.3, "smart_guitar",  "Pre-patch (43% — fragmentation)"),
        (520.0, 430.0, "jumbo_archtop", "Archtop perfect"),
        (480.0, 428.0, "jumbo_archtop", "Archtop mild tilt"),
        (174.2, 304.7, "dreadnought",   "J45 pre-patch (66% — fragmentation)"),
    ]

    for h, w, spec, label in test_cases:
        r = MockResult(h, w)
        a = diag.diagnose(r, spec_name=spec)
        print(f"  {label:<33} {a.estimated_angle_deg:>6.1f}° "
              f"{a.height_foreshorten_pct:>8.1f}% "
              f"{a.confidence:>6.2f}  {a.recommendation}")

    print()
    print("Key insight from results:")
    print("  Post-patch ~15% height error → ~31° estimated angle")
    print("  31° is physically implausible for a product photo")
    print("  → Remaining error is FRAGMENTATION, not perspective")
    print("  → Wider kernel (21×21) from Patch 14 should reduce further")
    print("  → --auto-perspective would NOT trigger (recommendation=likely_fragmentation)")
    print()

    # Test AutoPerspectiveCorrector
    print("AutoPerspectiveCorrector — 20° tilt case:")
    r_tilt = MockResult(416.0, 368.0)
    a_tilt = diag.diagnose(r_tilt, spec_name="smart_guitar")
    print(f"  Assessment: {a_tilt.recommendation}, angle={a_tilt.estimated_angle_deg}°")

    # Build mock contours
    body_pts = np.array([[0,0],[368,0],[368,416],[0,416]], dtype=np.float32)
    mock_contours = {"BODY_OUTLINE": [body_pts]}

    corrected, factor = corrector.correct(
        mock_contours, a_tilt, (416.0, 368.0))

    if factor != 1.0:
        orig_h = body_pts[:,1].max() - body_pts[:,1].min()
        corr_h = corrected["BODY_OUTLINE"][0][:,1].max() - \
                 corrected["BODY_OUTLINE"][0][:,1].min()
        print(f"  Correction factor: {factor:.4f}")
        print(f"  Body height: {orig_h:.1f}mm → {corr_h:.1f}mm "
              f"(spec: {a_tilt.corrected_height_mm}mm)")
    else:
        print(f"  No correction applied ({a_tilt.recommendation})")

    print(f"\n{'='*65}")
    print("All tests complete.")
    print(CLI_INTEGRATION)
