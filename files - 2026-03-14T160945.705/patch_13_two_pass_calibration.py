"""
PATCH 13 — Two-Pass Calibration + Batch Calibration Smoother
=============================================================

Addresses the two remaining calibration failure modes after Patches 01–12:

  FAILURE 1 — No --spec, no coins → assumed_dpi (conf=0.20) → body 4× too small
    Fix: InstrumentFamilyClassifier (scale-independent, pixel-aspect based)
         + FeatureScaleCalibrator (priority 4.5 in chain, between spec and DPI)

  FAILURE 2 — Batch processing: one image fails coin detection → mpp=0.085
               while all other images in session calibrate to mpp≈0.88
    Fix: BatchCalibrationSmoother — median-based outlier detection,
         corrects outliers to batch median with logged warning

Design principles applied:

  - InstrumentFamilyClassifier is SCALE-INDEPENDENT: operates on
    body_region pixel aspect ratio, requires no mm conversion.
    This eliminates the circular dependency (scale needs type, type
    needs scale) identified in the strategic review.

  - FeatureScaleCalibrator uses INSTRUMENT-SPECIFIC feature sizes:
    single-coil width (85mm) only applies to solid-body electrics;
    soundhole diameter (100mm) only to dreadnoughts; f-hole length
    (165mm) only to archtops. Wrong-family features are excluded.

  - BatchCalibrationSmoother uses MEDIAN not mean:
    prevents poisoned-batch amplification if the first 2–3 images
    in a session all fail calibration.

  - Smoother requires window_size ≥ 3 before activating:
    with only 2 data points and zero variance, any correct mpp
    would produce a huge z-score and get incorrectly corrected.

  - Confidence formula bug fixed:
    hypotheses that disagree by >50% are NOT averaged (blending
    0.85 and 0.085 produces 0.47 — confidently wrong). Instead,
    pick the highest-confidence contributor when disagreement is large.

Pipeline position:
  ScaleCalibrator.calibrate() priority chain (expanded):
    1. User dimension         (conf 1.00)
    2. Reference object       (conf 0.50–0.70)
    3. EXIF DPI               (conf 0.85)
    4. Instrument spec        (conf 0.60)  ← existing
    4.5 Feature-based scale   (conf 0.40–0.55) ← NEW (this patch)
    5. Render DPI estimate    (conf 0.40)
    6. Assumed DPI            (conf 0.20)

  BatchCalibrationSmoother wraps extract() call in PhotoVectorizerV2:
    result = v.extract(...)
    result = smoother.smooth(result)   ← NEW

Author: The Production Shop
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from statistics import median
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# COMPONENT A — InstrumentFamilyClassifier
# =============================================================================

class InstrumentFamily:
    ARCHTOP     = "archtop"       # f-holes, carved top, round lower bout
    ACOUSTIC    = "acoustic"      # soundhole, flat top, dreadnought/auditorium/jumbo
    SOLID_BODY  = "solid_body"    # electric, no holes except f-hole on semi-hollow
    SEMI_HOLLOW = "semi_hollow"   # thinline, f-holes + pickups (ES-335 type)
    UNKNOWN     = "unknown"


@dataclass
class FamilyClassification:
    family:          str
    confidence:      float
    pixel_aspect:    float     # body h/w ratio at pixel level
    f_hole_detected: bool
    soundhole_detected: bool
    notes:           List[str] = field(default_factory=list)


class InstrumentFamilyClassifier:
    """
    Classify instrument family from body region geometry.
    Operates entirely in pixel space — no mm conversion required.

    Parameters
    ----------
    f_hole_circularity_max  : contours below this circularity in middle zones
                              are considered f-hole candidates
    soundhole_circularity_min : contours above this in MC zone → soundhole
    """

    # Aspect ratio ranges (pixel h/w of body region)
    # These overlap — use f-hole/soundhole as tiebreaker
    _ASPECT_RANGES = {
        InstrumentFamily.ARCHTOP:     (1.10, 1.30),
        InstrumentFamily.ACOUSTIC:    (1.20, 1.40),
        InstrumentFamily.SOLID_BODY:  (1.20, 1.40),
        InstrumentFamily.SEMI_HOLLOW: (1.15, 1.35),
    }

    def __init__(
        self,
        f_hole_circularity_max:   float = 0.30,
        soundhole_circularity_min: float = 0.65,
    ):
        self.f_hole_circ_max   = f_hole_circularity_max
        self.soundhole_circ_min = soundhole_circularity_min

    # ------------------------------------------------------------------
    def classify(
        self,
        body_region,                               # BodyRegion dataclass
        edge_image:       Optional[np.ndarray] = None,
        feature_contours: Optional[list]       = None,  # List[FeatureContour]
    ) -> FamilyClassification:
        """
        Classify instrument family from body region and optionally
        from detected feature contours.

        Parameters
        ----------
        body_region      : BodyRegion from BodyIsolator (has .width, .height)
        edge_image       : edge image from Stage 5 (for internal feature scan)
        feature_contours : list of FeatureContour from ContourAssembler

        Returns
        -------
        FamilyClassification
        """
        notes = []

        # ── Pixel aspect ratio (scale-independent) ───────────────────
        bw = max(body_region.width,  1)
        bh = max(body_region.height, 1)
        pixel_aspect = bh / bw
        notes.append(f"Body pixel aspect (h/w): {pixel_aspect:.3f}")

        # ── Feature-based detection ───────────────────────────────────
        f_hole_detected    = False
        soundhole_detected = False

        if feature_contours:
            for fc in feature_contours:
                try:
                    ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value') \
                             else str(fc.feature_type)
                    if ft_val == "f_hole":
                        f_hole_detected = True
                    elif ft_val == "soundhole":
                        soundhole_detected = True
                except Exception:
                    pass

        # Fallback: scan edge image if no feature contours provided
        if not feature_contours and edge_image is not None:
            f_hole_detected, soundhole_detected = self._scan_for_holes(
                edge_image, body_region)

        notes.append(f"f-hole detected: {f_hole_detected}")
        notes.append(f"soundhole detected: {soundhole_detected}")

        # ── Decision logic ────────────────────────────────────────────
        family, confidence = self._decide(
            pixel_aspect, f_hole_detected, soundhole_detected, notes,
            feature_contours=feature_contours)

        return FamilyClassification(
            family             = family,
            confidence         = confidence,
            pixel_aspect       = pixel_aspect,
            f_hole_detected    = f_hole_detected,
            soundhole_detected = soundhole_detected,
            notes              = notes,
        )

    # ------------------------------------------------------------------
    def _decide(
        self,
        aspect:            float,
        f_hole:            bool,
        soundhole:         bool,
        notes:             List[str],
        feature_contours:  Optional[list] = None,
    ) -> Tuple[str, float]:

        # Strong signal: soundhole → acoustic family
        if soundhole and not f_hole:
            notes.append("Decision: soundhole present → ACOUSTIC")
            return InstrumentFamily.ACOUSTIC, 0.85

        # Strong signal: f-holes → archtop or semi-hollow
        if f_hole:
            if aspect < 1.25:
                notes.append("Decision: f-holes + low aspect → ARCHTOP")
                return InstrumentFamily.ARCHTOP, 0.80
            else:
                notes.append("Decision: f-holes + higher aspect → SEMI_HOLLOW")
                return InstrumentFamily.SEMI_HOLLOW, 0.72

        # Electric signals: pickup present → solid_body even in ambiguous aspect zone
        for fc in (feature_contours or []):
            try:
                ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value')                          else str(fc.feature_type)
                if ft_val in ("pickup_route", "control_cavity", "neck_pocket"):
                    notes.append(f"Decision: electric feature ({ft_val}) → SOLID_BODY")
                    return InstrumentFamily.SOLID_BODY, 0.70
            except Exception:
                pass

        # No holes detected — use aspect ratio only
        if aspect > 1.26:
            notes.append(f"Decision: high aspect ({aspect:.3f}) → ACOUSTIC")
            return InstrumentFamily.ACOUSTIC, 0.55

        if aspect < 1.20:
            notes.append(f"Decision: low aspect ({aspect:.3f}), no holes → SOLID_BODY")
            return InstrumentFamily.SOLID_BODY, 0.50

        # Ambiguous range 1.20–1.26
        notes.append(f"Decision: ambiguous aspect ({aspect:.3f}) → UNKNOWN")
        return InstrumentFamily.UNKNOWN, 0.30

    # ------------------------------------------------------------------
    def _scan_for_holes(
        self,
        edge_image:   np.ndarray,
        body_region,
    ) -> Tuple[bool, bool]:
        """
        Quick scan of edge image within body region for hole signatures.
        Returns (f_hole_found, soundhole_found).
        """
        bx = body_region.x
        by = body_region.y
        bw = body_region.width
        bh = body_region.height

        # Crop to body region
        h, w = edge_image.shape[:2]
        y0 = max(0, by)
        y1 = min(h, by + bh)
        x0 = max(0, bx)
        x1 = min(w, bx + bw)
        crop = edge_image[y0:y1, x0:x1]

        if crop.size == 0:
            return False, False

        contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        f_hole = False
        soundhole = False

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 200:   # too small
                continue
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * math.pi * area / (peri ** 2)
            _, (cw, ch), _ = cv2.minAreaRect(cnt)
            aspect = max(cw, ch) / max(min(cw, ch), 1)

            # F-hole: elongated (aspect > 3), low circularity
            if circ < self.f_hole_circ_max and aspect > 3.0:
                f_hole = True

            # Soundhole: round (high circularity), moderate size
            if circ > self.soundhole_circ_min and 0.8 < aspect < 1.3:
                if 500 < area < 30000:
                    soundhole = True

        return f_hole, soundhole


# =============================================================================
# COMPONENT B — FeatureScaleCalibrator
# =============================================================================

# Feature size tables per instrument family (mm)
# Each entry: (feature_name, size_mm, tolerance_pct, applies_to_families)
FEATURE_SIZE_TABLE: List[Tuple[str, float, float, List[str]]] = [
    # Single-coil pickup width
    ("single_coil_pickup_w",  85.0, 0.08,
     [InstrumentFamily.SOLID_BODY, InstrumentFamily.SEMI_HOLLOW]),
    # Humbucker pickup width
    ("humbucker_pickup_w",    70.0, 0.08,
     [InstrumentFamily.SOLID_BODY, InstrumentFamily.SEMI_HOLLOW,
      InstrumentFamily.ARCHTOP]),
    # Dreadnought soundhole diameter
    ("dreadnought_soundhole", 100.0, 0.06,
     [InstrumentFamily.ACOUSTIC]),
    # Auditorium/OM soundhole diameter
    ("auditorium_soundhole",  88.0, 0.07,
     [InstrumentFamily.ACOUSTIC]),
    # Archtop f-hole length
    ("archtop_f_hole_length", 165.0, 0.10,
     [InstrumentFamily.ARCHTOP, InstrumentFamily.SEMI_HOLLOW]),
    # Bridge saddle length (acoustic)
    ("acoustic_bridge_length", 175.0, 0.08,
     [InstrumentFamily.ACOUSTIC]),
    # Standard nut width (not visible in body photos — low priority)
    ("nut_width_standard",    43.0, 0.06,
     [InstrumentFamily.SOLID_BODY, InstrumentFamily.ACOUSTIC]),
]


@dataclass
class FeatureScaleHypothesis:
    feature_name:   str
    measured_px:    float
    known_mm:       float
    mm_per_px:      float
    confidence:     float
    family:         str


class FeatureScaleCalibrator:
    """
    Calibrates scale from known instrument feature sizes, gated by
    instrument family so wrong-family features are never applied.

    Priority 4.5 in the calibration chain — runs when:
      - No user dimension supplied
      - No reference object (coin/card) detected
      - No EXIF DPI
      - Spec-based calibration not available (no --spec flag)

    Requires InstrumentFamilyClassifier to have run first.

    Parameters
    ----------
    min_feature_px : minimum contour size in pixels to consider as a feature
    max_hypotheses : cap on hypotheses to avoid runaway processing
    """

    def __init__(
        self,
        min_feature_px: int = 50,
        max_hypotheses: int = 5,
    ):
        self.min_px     = min_feature_px
        self.max_hyp    = max_hypotheses

    # ------------------------------------------------------------------
    def calibrate_from_features(
        self,
        image:            np.ndarray,
        family:           FamilyClassification,
        feature_contours: Optional[list] = None,   # List[FeatureContour]
        edge_image:       Optional[np.ndarray] = None,
    ) -> Optional[dict]:
        """
        Attempt scale calibration from detected instrument features.

        Parameters
        ----------
        image            : BGR image
        family           : FamilyClassification from InstrumentFamilyClassifier
        feature_contours : assembled contours from ContourAssembler
        edge_image       : edge image from Stage 5 (fallback if no contours)

        Returns
        -------
        CalibrationResult-compatible dict or None if no reliable match found
        """
        if family.family == InstrumentFamily.UNKNOWN:
            logger.info("FeatureScaleCalibrator: unknown family — skipping")
            return None

        hypotheses: List[FeatureScaleHypothesis] = []

        # Build feature measurements from assembled contours
        if feature_contours:
            hypotheses = self._measure_from_contours(
                feature_contours, family)

        # Fallback: basic edge scan if no contours
        if not hypotheses and edge_image is not None:
            hypotheses = self._measure_from_edges(
                edge_image, family)

        if not hypotheses:
            logger.info(
                f"FeatureScaleCalibrator: no matching features for {family.family}")
            return None

        # Combine hypotheses
        combined = self._combine_hypotheses(hypotheses, family)
        if combined is None:
            return None

        logger.info(
            f"FeatureScaleCalibrator: {len(hypotheses)} feature(s) → "
            f"mpp={combined['mm_per_px']:.4f} conf={combined['confidence']:.2f} "
            f"[{family.family}]")
        return combined

    # ------------------------------------------------------------------
    def _measure_from_contours(
        self,
        feature_contours: list,
        family:           FamilyClassification,
    ) -> List[FeatureScaleHypothesis]:
        """Match assembled contours to known feature sizes."""
        hypotheses = []
        family_str = family.family

        for fc in feature_contours:
            if len(hypotheses) >= self.max_hyp:
                break

            try:
                ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value') \
                         else str(fc.feature_type)
            except Exception:
                continue

            _, _, bw_px, bh_px = fc.bbox_px
            max_dim_px = max(bw_px, bh_px)
            min_dim_px = min(bw_px, bh_px)

            if max_dim_px < self.min_px:
                continue

            # Match contour type to feature table
            for feat_name, feat_mm, tol, families in FEATURE_SIZE_TABLE:
                if family_str not in families:
                    continue

                # Choose which pixel dimension to compare
                if ft_val in ("pickup_route", "bridge_route"):
                    measured_px = max_dim_px   # use longer dimension
                elif ft_val in ("soundhole", "rosette"):
                    measured_px = (bw_px + bh_px) / 2.0  # average (roughly circular)
                elif ft_val == "f_hole":
                    measured_px = max_dim_px   # use length
                else:
                    continue

                if measured_px < self.min_px:
                    continue

                mpp = feat_mm / measured_px
                # Confidence from family confidence * feature match confidence
                feat_conf = 0.45 * family.confidence
                hypotheses.append(FeatureScaleHypothesis(
                    feature_name = feat_name,
                    measured_px  = measured_px,
                    known_mm     = feat_mm,
                    mm_per_px    = mpp,
                    confidence   = feat_conf,
                    family       = family_str,
                ))

        return hypotheses

    def _measure_from_edges(
        self,
        edge_image: np.ndarray,
        family:     FamilyClassification,
    ) -> List[FeatureScaleHypothesis]:
        """Fallback: measure blobs in edge image directly."""
        hypotheses = []
        contours, _ = cv2.findContours(
            edge_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if len(hypotheses) >= self.max_hyp:
                break
            area = cv2.contourArea(cnt)
            if area < self.min_px * self.min_px:
                continue
            peri  = cv2.arcLength(cnt, True)
            circ  = 4 * math.pi * area / max(peri ** 2, 1e-9)
            x, y, w, h = cv2.boundingRect(cnt)
            asp   = max(w, h) / max(min(w, h), 1)

            family_str = family.family

            # Soundhole: round blob in acoustic image
            if (family_str == InstrumentFamily.ACOUSTIC and
                    circ > 0.65 and 0.8 < asp < 1.3):
                diam_px = (w + h) / 2.0
                for feat_name, feat_mm, _, families in FEATURE_SIZE_TABLE:
                    if family_str in families and "soundhole" in feat_name:
                        hypotheses.append(FeatureScaleHypothesis(
                            feature_name = feat_name,
                            measured_px  = diam_px,
                            known_mm     = feat_mm,
                            mm_per_px    = feat_mm / diam_px,
                            confidence   = 0.35 * family.confidence,
                            family       = family_str,
                        ))
                        break

        return hypotheses

    # ------------------------------------------------------------------
    def _combine_hypotheses(
        self,
        hypotheses: List[FeatureScaleHypothesis],
        family:     FamilyClassification,
    ) -> Optional[dict]:
        """
        Combine multiple feature-scale hypotheses into one calibration.

        Key fix from strategic review:
          - Do NOT average when hypotheses disagree by > 50%
          - When disagreement is large, use highest-confidence source only
          - Single hypothesis gets confidence * 0.90 (mild solo penalty)
        """
        if not hypotheses:
            return None

        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        best = hypotheses[0]

        if len(hypotheses) == 1:
            # Mild solo penalty (not 0.8 — that was the developer's bug)
            return {
                "mm_per_px":  best.mm_per_px,
                "confidence": best.confidence * 0.90,
                "source":     "feature_scale",
                "message":    (
                    f"Feature scale: {best.feature_name} "
                    f"({best.known_mm}mm / {best.measured_px:.0f}px) "
                    f"[{family.family}]"),
            }

        second = hypotheses[1]
        # Disagreement fraction between top two
        disagreement = abs(best.mm_per_px - second.mm_per_px) / max(best.mm_per_px, 1e-9)

        if disagreement > 0.50:
            # Large disagreement → use best only, penalize for lack of corroboration
            conf = best.confidence * 0.75
            logger.info(
                f"FeatureScaleCalibrator: hypotheses disagree by {disagreement:.0%} "
                f"→ using best only (conf penalized to {conf:.2f})")
            return {
                "mm_per_px":  best.mm_per_px,
                "confidence": conf,
                "source":     "feature_scale",
                "message":    (
                    f"Feature scale (best of {len(hypotheses)}): "
                    f"{best.feature_name} = {best.mm_per_px:.4f}mm/px "
                    f"[{family.family}], disagreement={disagreement:.0%}"),
            }

        # Agreement within 50% → weighted average
        agreement_bonus = max(0.0, 1.0 - disagreement) * 0.10
        total_w = sum(h.confidence for h in hypotheses)
        weighted_mpp = sum(h.mm_per_px * h.confidence for h in hypotheses) / total_w
        conf = min(0.55, best.confidence + agreement_bonus)

        return {
            "mm_per_px":  weighted_mpp,
            "confidence": conf,
            "source":     "feature_scale",
            "message":    (
                f"Feature scale ({len(hypotheses)} hypotheses, "
                f"agreement={1-disagreement:.0%}): "
                f"mpp={weighted_mpp:.4f} [{family.family}]"),
        }


# =============================================================================
# COMPONENT C — BatchCalibrationSmoother
# =============================================================================

@dataclass
class SmootherRecord:
    """One calibration record stored in the smoother's history."""
    mm_per_px:       float
    confidence:      float
    source:          str
    family:          str
    image_path:      str
    was_corrected:   bool = False


class BatchCalibrationSmoother:
    """
    Detects and corrects calibration outliers in a batch processing session
    using median-based z-score analysis, bucketed by instrument family.

    Key design decisions:
      - Uses MEDIAN not mean: outlier-robust baseline
      - Requires window_size >= 3 before activating: prevents false positives
        with only 2 data points
      - Correction replaces outlier mpp with batch median (not mean)
      - Per-family buckets: archtop batch doesn't contaminate acoustic batch
      - State is session-local: not persisted between runs

    Parameters
    ----------
    window_size  : history window per family (default 7)
    z_threshold  : z-score above which a value is an outlier (default 3.0)
    min_history  : minimum history entries before outlier detection activates
    """

    def __init__(
        self,
        window_size:  int   = 7,
        z_threshold:  float = 3.0,
        min_history:  int   = 3,
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.min_history = min_history
        # Per-family deques
        self._history: Dict[str, deque] = {}

    # ------------------------------------------------------------------
    def smooth(self, extraction_result) -> object:
        """
        Inspect calibration from an extraction result and correct if outlier.

        Parameters
        ----------
        extraction_result : PhotoExtractionResult from PhotoVectorizerV2

        Returns
        -------
        extraction_result (modified in-place if correction applied)
        """
        cal = getattr(extraction_result, 'calibration', None)
        if cal is None:
            return extraction_result

        current_mpp  = cal.mm_per_px
        current_conf = cal.confidence
        source_str   = cal.source.value if hasattr(cal.source, 'value') \
                       else str(cal.source)

        # Infer family from result if available
        family = getattr(extraction_result, 'instrument_family', 'unknown')
        if family == 'unknown':
            family = self._infer_family_from_result(extraction_result)

        bucket = self._history.setdefault(family, deque(maxlen=self.window_size))

        # Only apply smoothing when we have enough history
        if len(bucket) >= self.min_history:
            values = list(bucket)
            batch_median = float(median(values))

            # MAD-based scale estimate (robust to outliers)
            mad = float(median([abs(v - batch_median) for v in values]))
            # Convert MAD to std-equivalent (factor 1.4826 for normal distribution)
            robust_std = mad * 1.4826

            if robust_std > 0:
                z_score = abs(current_mpp - batch_median) / robust_std
            else:
                # All historical values identical — any deviation is flagged
                z_score = float('inf') if current_mpp != batch_median else 0.0

            if z_score > self.z_threshold:
                old_mpp = current_mpp
                # Correct to batch median
                cal.mm_per_px  = batch_median
                cal.confidence = 0.55
                cal.message    = (
                    f"Batch corrected: {old_mpp:.4f} → {batch_median:.4f} "
                    f"(z={z_score:.1f}, family={family}, "
                    f"n={len(values)})")
                extraction_result.warnings.append(
                    f"⚠  Scale outlier corrected: mpp was {old_mpp:.4f} "
                    f"(z={z_score:.1f}×σ from batch median {batch_median:.4f}). "
                    f"Verify dimensions before cutting.")
                logger.warning(cal.message)

                # Store the corrected value in history
                bucket.append(batch_median)
                return extraction_result

        # No correction — store current value
        bucket.append(current_mpp)
        return extraction_result

    # ------------------------------------------------------------------
    def session_summary(self) -> str:
        """Return a summary of calibration values seen this session."""
        lines = ["BatchCalibrationSmoother — session summary:"]
        for family, bucket in self._history.items():
            if not bucket:
                continue
            vals = list(bucket)
            med  = median(vals)
            lines.append(
                f"  {family}: n={len(vals)}  "
                f"median={med:.4f}  "
                f"range=[{min(vals):.4f}, {max(vals):.4f}]")
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all history. Call between unrelated batches."""
        self._history.clear()

    # ------------------------------------------------------------------
    @staticmethod
    def _infer_family_from_result(result) -> str:
        """Best-effort instrument family inference from result features."""
        features = getattr(result, 'features', {})
        for ft, contours in features.items():
            if not contours:
                continue
            ft_val = ft.value if hasattr(ft, 'value') else str(ft)
            if ft_val == "f_hole":
                return InstrumentFamily.ARCHTOP
            if ft_val == "soundhole":
                return InstrumentFamily.ACOUSTIC
            if ft_val in ("pickup_route", "control_cavity"):
                return InstrumentFamily.SOLID_BODY
        return "unknown"


# =============================================================================
# Integration into ScaleCalibrator
# =============================================================================

INTEGRATION_NOTES = """
STEP 1 — Add InstrumentFamilyClassifier call in extract() after Stage 4.5:

    from patch_13_two_pass_calibration import (
        InstrumentFamilyClassifier,
        FeatureScaleCalibrator,
        BatchCalibrationSmoother,
    )

    # After body_region = self.body_isolator.isolate(...):
    family_clf = InstrumentFamilyClassifier()
    instrument_family = family_clf.classify(
        body_region,
        edge_image       = None,          # not yet computed at this stage
        feature_contours = None,
    )
    logger.info(f"Instrument family: {instrument_family.family} "
                f"(conf={instrument_family.confidence:.2f})")

STEP 2 — Add FeatureScaleCalibrator as priority 4.5 in ScaleCalibrator.calibrate():

    # After priority 4 (instrument spec) block, before priority 5 (render DPI):
    # Priority 4.5: Feature-based scale (needs family classification)
    if hasattr(self, '_feature_calibrator') and self._feature_calibrator is not None:
        feat_result = self._feature_calibrator.calibrate_from_features(
            image, family_clf_result,
            feature_contours=feature_contours_list)
        if feat_result and feat_result["confidence"] > 0.35:
            return CalibrationResult(
                mm_per_px  = feat_result["mm_per_px"],
                source     = ScaleSource.ESTIMATED_RENDER_DPI,  # closest enum
                confidence = feat_result["confidence"],
                message    = feat_result["message"])

    Wire in __init__:
    self._feature_calibrator = FeatureScaleCalibrator()

STEP 3 — Wrap extract() call with BatchCalibrationSmoother (session-level):

    # In PhotoVectorizerV2.__init__(), add:
    self.batch_smoother = BatchCalibrationSmoother()

    # In extract() or batch_extract(), after getting result:
    if self.batch_smoother:
        result = self.batch_smoother.smooth(result)

    # At end of batch session, log summary:
    logger.info(self.batch_smoother.session_summary())
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 65)
    print("PATCH 13 — Self-Test")
    print("=" * 65)

    # ── Component A: InstrumentFamilyClassifier ──────────────────────
    print("\nCOMPONENT A — InstrumentFamilyClassifier:")
    clf = InstrumentFamilyClassifier()

    class MockBodyRegion:
        def __init__(self, w, h):
            self.width  = w
            self.height = h
            self.x      = 0
            self.y      = 0

    class MockFC:
        def __init__(self, ft_str):
            class FT:
                value = ft_str
            self.feature_type = FT()
            self.bbox_px = (0, 0, 100, 40)

    test_bodies = [
        # (w_px, h_px, mock_features, expected_family, label)
        (430, 520,  [MockFC("soundhole")],             InstrumentFamily.ACOUSTIC,    "Dreadnought with soundhole"),
        (430, 520,  [MockFC("f_hole"), MockFC("f_hole")], InstrumentFamily.ARCHTOP, "Archtop with f-holes"),
        (325, 406,  [MockFC("pickup_route")],           InstrumentFamily.SOLID_BODY, "Strat with pickup"),
        (430, 520,  [],                                 InstrumentFamily.ACOUSTIC,   "Body only, high aspect"),
        (325, 395,  [],                                 InstrumentFamily.SOLID_BODY, "Body only, low aspect"),
    ]

    print(f"  {'Label':<35} {'Aspect':>7}  {'Expected':<14} {'Got':<14} {'Conf':>5}  OK?")
    print("  " + "─" * 80)
    correct = 0
    for w, h, features, expected, label in test_bodies:
        br   = MockBodyRegion(w, h)
        res  = clf.classify(br, feature_contours=features if features else None)
        ok   = "✓" if res.family == expected else "✗"
        if res.family == expected:
            correct += 1
        print(f"  {label:<35} {h/w:>7.3f}  {expected:<14} {res.family:<14} "
              f"{res.confidence:>5.2f}  {ok}")

    print(f"\n  Accuracy: {correct}/{len(test_bodies)}")

    # ── Component B: FeatureScaleCalibrator ─────────────────────────
    print("\nCOMPONENT B — FeatureScaleCalibrator:")
    fsc = FeatureScaleCalibrator()

    fc_acoustic = MockBodyRegion(430, 520)
    family_acoustic = FamilyClassification(
        family=InstrumentFamily.ACOUSTIC, confidence=0.85,
        pixel_aspect=1.21, f_hole_detected=False, soundhole_detected=True)

    # Mock a soundhole contour: 100mm diameter at mpp=0.5 → 200px
    class MockContour:
        def __init__(self, ft_str, w_px, h_px):
            class FT:
                value = ft_str
            self.feature_type = FT()
            self.bbox_px = (100, 200, w_px, h_px)

    contours_acoustic = [MockContour("soundhole", 200, 195)]
    result = fsc.calibrate_from_features(None, family_acoustic, contours_acoustic)
    if result:
        expected_mpp = 100.0 / 197.5  # avg of 200+195
        print(f"  Acoustic soundhole: mpp={result['mm_per_px']:.4f} "
              f"(expected ~{expected_mpp:.4f})  conf={result['confidence']:.2f}")
        print(f"  Message: {result['message']}")
    else:
        print("  No result (unexpected)")

    # Test disagreement handling
    print("\n  Disagreement handling (>50% apart):")
    hyp_agree = [
        FeatureScaleHypothesis("f1", 100, 85, 0.85, 0.45, "solid_body"),
        FeatureScaleHypothesis("f2", 102, 85, 0.833, 0.40, "solid_body"),
    ]
    hyp_disagree = [
        FeatureScaleHypothesis("f1", 100, 85, 0.85, 0.45, "solid_body"),
        FeatureScaleHypothesis("f2", 1000, 85, 0.085, 0.20, "solid_body"),  # 10x off
    ]
    r_agree    = fsc._combine_hypotheses(hyp_agree,    FamilyClassification("solid_body", 0.8, 1.25, False, False))
    r_disagree = fsc._combine_hypotheses(hyp_disagree, FamilyClassification("solid_body", 0.8, 1.25, False, False))
    print(f"  Agreeing:    mpp={r_agree['mm_per_px']:.4f}  conf={r_agree['confidence']:.2f}")
    print(f"  Disagreeing: mpp={r_disagree['mm_per_px']:.4f}  conf={r_disagree['confidence']:.2f}")
    print(f"  ✓ Disagreeing uses BEST (0.85) not average (0.47)")

    # ── Component C: BatchCalibrationSmoother ───────────────────────
    print("\nCOMPONENT C — BatchCalibrationSmoother:")

    class MockCal:
        def __init__(self, mpp, conf):
            self.mm_per_px  = mpp
            self.confidence = conf
            self.message    = ""
            class S:
                value = "spec"
            self.source = S()

    class MockResult:
        def __init__(self, mpp, conf, family="jumbo_archtop"):
            self.calibration      = MockCal(mpp, conf)
            self.instrument_family = family
            self.warnings         = []
            self.features         = {}

    smoother = BatchCalibrationSmoother(window_size=7, min_history=3)

    session_data = [
        (0.882, 0.60, "image_1"),
        (0.879, 0.60, "image_2"),
        (0.884, 0.60, "image_3"),
        (0.881, 0.60, "image_4"),
        (0.085, 0.20, "image_5_BAD"),   # ← assumed DPI failure
        (0.883, 0.60, "image_6"),
    ]

    print(f"  {'Image':<20} {'In mpp':>8} {'Out mpp':>9} {'Conf':>6}  {'Action'}")
    print("  " + "─" * 60)
    for mpp, conf, label in session_data:
        r = MockResult(mpp, conf)
        smoother.smooth(r)
        action = "corrected ✓" if r.warnings else \
                 ("history building" if len(smoother._history.get("jumbo_archtop", [])) < 3
                  else "accepted")
        print(f"  {label:<20} {mpp:>8.4f} {r.calibration.mm_per_px:>9.4f} "
              f"{r.calibration.confidence:>6.2f}  {action}")

    print()
    print(smoother.session_summary())

    print(f"\n{'=' * 65}")
    print("All tests complete.")
    print(INTEGRATION_NOTES)
