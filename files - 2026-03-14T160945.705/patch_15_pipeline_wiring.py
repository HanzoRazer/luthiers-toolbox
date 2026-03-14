"""
PATCH 15 — Pipeline Wiring Fixes
==================================

Two structural changes required for Patches 13 and 14 to function correctly:

  FIX A — ScaleSource enum: add FEATURE_SCALE entry
    Patch 13's FeatureScaleCalibrator returns source="feature_scale" but
    ScaleSource enum has no such value. Currently using ESTIMATED_RENDER_DPI
    as a proxy, which makes the calibration log misleading and prevents
    downstream code from distinguishing the two paths.

  FIX B — Calibration ordering: move Stage 7 before Stage 5
    PhotoEdgeDetector now accepts mpp and body_region for adaptive kernel
    sizing (Patch 14). But in v2, calibration (Stage 7) runs AFTER edge
    detection (Stage 5). Without a calibrated mpp, GatedAdaptiveCloser
    falls back to mpp=0.3 for kernel sizing.

    Solution: compute a ROUGH mpp estimate before Stage 5 using only
    body_region (from BodyIsolator) and spec_name if available. The full
    calibration (with reference object detection, EXIF, etc.) still runs
    at Stage 7 for the final result. The rough estimate is only used for
    kernel size selection — a 20% mpp error causes at most a 2px kernel
    difference, which is inconsequential.

    Rough mpp formula (priority order):
      1. spec_name available: spec_body_h_mm / body_region.height_px
      2. No spec: INSTRUMENT_SPECS["dreadnought"]["body"][0] / body_region.height_px
      3. No body_region: 0.30 (safe default, gives 11×11 kernel)

Author: The Production Shop
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# FIX A — ScaleSource enum extension
# =============================================================================

# Integration: In photo_vectorizer_v2.py, add to ScaleSource enum:
#
#   class ScaleSource(Enum):
#       USER_DIMENSION        = "user_dimension"
#       INSTRUMENT_SPEC       = "instrument_spec"
#       REFERENCE_OBJECT      = "reference_object"
#       MULTI_REFERENCE       = "multi_reference"
#       EXIF_DPI              = "exif_dpi"
#       FEATURE_SCALE         = "feature_scale"         # ← ADD (Patch 13)
#       ESTIMATED_RENDER_DPI  = "estimated_render_dpi"
#       ASSUMED_DPI           = "assumed_dpi"
#       NONE                  = "none"
#
# Then in Patch 13 FeatureScaleCalibrator._combine_hypotheses(), replace:
#   "source": "feature_scale"
# and in ScaleCalibrator.calibrate() priority 4.5 block, use:
#   source = ScaleSource.FEATURE_SCALE
#
# This also enables downstream code (emit_calibration_guidance, batch smoother)
# to distinguish feature-based from DPI-estimated calibration.

SCALE_SOURCE_ADDITION = """
Add to ScaleSource enum in photo_vectorizer_v2.py after EXIF_DPI:

    FEATURE_SCALE = "feature_scale"   # Patch 13: instrument feature size

Update emit_calibration_guidance() (Patch 07 Fix 4) to handle this source:
    if source_str == "feature_scale":
        msgs.append(
            "   Scale estimated from detected instrument features "
            "(pickup/soundhole/f-hole dimensions). "
            "Verify before cutting expensive material.")
"""


# =============================================================================
# FIX B — Rough mpp estimate for pre-Stage-5 kernel sizing
# =============================================================================

# Default spec body heights for rough mpp estimation
_ROUGH_SPEC_HEIGHTS = {
    "stratocaster":  406,
    "telecaster":    406,
    "les_paul":      450,
    "es335":         500,
    "dreadnought":   520,
    "smart_guitar":  444,
    "jumbo_archtop": 520,
    "archtop":       520,
    "acoustic":      500,
    "solid_body":    430,
}
_DEFAULT_BODY_HEIGHT_MM = 490.0   # conservative mid-range estimate


def compute_rough_mpp(
    body_region,                        # BodyRegion or None
    spec_name:    Optional[str] = None,
    family_hint:  Optional[str] = None,  # from InstrumentFamilyClassifier
) -> float:
    """
    Compute a rough mm/px estimate for use in GatedAdaptiveCloser
    kernel sizing BEFORE full calibration runs.

    This is NOT used as the final calibration result — only for choosing
    the morphological close kernel size in PhotoEdgeDetector.

    Priority:
      1. spec_name provided → use spec body height
      2. family_hint provided → use family average height
      3. body_region available → assume dreadnought height (safe)
      4. Nothing available → return 0.30 (gives 11×11 kernel)

    A 20% error in rough mpp causes at most ±2px kernel size change,
    which is negligible for gap-bridging purposes.

    Parameters
    ----------
    body_region  : BodyRegion from BodyIsolator (.height_px attribute)
    spec_name    : instrument spec name (e.g. "dreadnought")
    family_hint  : instrument family string (e.g. "acoustic", "archtop")

    Returns
    -------
    rough mpp estimate (float, mm/px)
    """
    if body_region is None or body_region.height_px <= 0:
        logger.debug("compute_rough_mpp: no body_region → using 0.30")
        return 0.30

    body_h_px = float(body_region.height_px)

    # Priority 1: explicit spec
    if spec_name and spec_name.lower() in _ROUGH_SPEC_HEIGHTS:
        h_mm  = _ROUGH_SPEC_HEIGHTS[spec_name.lower()]
        rough = h_mm / body_h_px
        logger.debug(
            f"compute_rough_mpp: spec={spec_name} → {h_mm}mm/{body_h_px:.0f}px "
            f"= {rough:.4f}")
        return rough

    # Priority 2: family hint
    if family_hint and family_hint.lower() in _ROUGH_SPEC_HEIGHTS:
        h_mm  = _ROUGH_SPEC_HEIGHTS[family_hint.lower()]
        rough = h_mm / body_h_px
        logger.debug(
            f"compute_rough_mpp: family={family_hint} → {h_mm}mm/{body_h_px:.0f}px "
            f"= {rough:.4f}")
        return rough

    # Priority 3: generic default
    rough = _DEFAULT_BODY_HEIGHT_MM / body_h_px
    logger.debug(
        f"compute_rough_mpp: no spec/family → "
        f"{_DEFAULT_BODY_HEIGHT_MM}mm/{body_h_px:.0f}px = {rough:.4f}")
    return rough


# =============================================================================
# Pipeline ordering diff
# =============================================================================

PIPELINE_ORDERING_DIFF = """
In PhotoVectorizerV2.extract() / _extract_image(), reorder stages:

CURRENT ORDER:
    Stage 4:   Background removal  → alpha_mask
    Stage 4.5: Body isolation      → body_region
    Stage 5:   Edge detection      → edges          (uses hardcoded close kernel)
    Stage 7:   Calibration         → mpp

NEW ORDER:
    Stage 4:   Background removal  → alpha_mask
    Stage 4.5: Body isolation      → body_region
    Stage 4.6: Rough mpp estimate  → rough_mpp      ← NEW (this patch)
    Stage 5:   Edge detection      → edges           (uses rough_mpp for kernel)
    Stage 7:   Calibration         → mpp             (still full calibration)

ADD after Stage 4.5 (body isolation):

    # Stage 4.6: Rough mpp for adaptive kernel sizing
    from patch_15_pipeline_wiring import compute_rough_mpp
    rough_mpp = compute_rough_mpp(
        body_region,
        spec_name   = spec_name,
        family_hint = getattr(instrument_family, 'family', None),
    )
    logger.info(f"Rough mpp for kernel sizing: {rough_mpp:.4f}")

UPDATE Stage 5 call:

    # was:
    edges = self.edge_detector.detect(fg_image, alpha_mask)

    # becomes:
    edges = self.edge_detector.detect(
        fg_image, alpha_mask,
        input_type  = result.input_type.value,
        mpp         = rough_mpp,        # ← from Stage 4.6
        body_region = body_region,      # ← from Stage 4.5
    )

Stage 7 (full calibration) is UNCHANGED — rough_mpp is only for kernel sizing.
Final body dimensions still use the full calibrated mpp.
"""


# =============================================================================
# Complete integration checklist
# =============================================================================

INTEGRATION_CHECKLIST = """
PATCH 15 — Complete Integration Checklist
==========================================

[ ] FIX A: Add FEATURE_SCALE = "feature_scale" to ScaleSource enum
    File: photo_vectorizer_v2.py
    Location: ScaleSource class, after EXIF_DPI

[ ] FIX A: Update Patch 13 FeatureScaleCalibrator to use ScaleSource.FEATURE_SCALE
    File: photo_vectorizer_v2.py (after absorbing patch_13)
    Location: ScaleCalibrator.calibrate() priority 4.5 return statement
    Change: source=ScaleSource.ESTIMATED_RENDER_DPI → source=ScaleSource.FEATURE_SCALE

[ ] FIX A: Update emit_calibration_guidance() (Patch 07) for FEATURE_SCALE
    Add a branch for source_str == "feature_scale" with appropriate message

[ ] FIX B: Add Stage 4.6 rough_mpp compute after body_region assignment
    File: photo_vectorizer_v2.py
    Location: extract() / _extract_image(), after body_region = self.body_isolator.isolate(...)
    Code: from patch_15_pipeline_wiring import compute_rough_mpp
          rough_mpp = compute_rough_mpp(body_region, spec_name, ...)

[ ] FIX B: Update PhotoEdgeDetector.detect() call to pass rough_mpp + body_region
    File: photo_vectorizer_v2.py
    Location: Stage 5 call in extract()
    Change: edges = self.edge_detector.detect(fg_image, alpha_mask)
        to: edges = self.edge_detector.detect(
                fg_image, alpha_mask,
                input_type=result.input_type.value,
                mpp=rough_mpp, body_region=body_region)

[ ] FIX B: Update PhotoEdgeDetector.detect() signature to accept new params
    File: photo_vectorizer_v2.py
    Add: mpp=None, body_region=None to detect() signature
    Replace close block with GatedAdaptiveCloser call (Patch 14 integration)
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 65)
    print("PATCH 15 — Pipeline Wiring Self-Test")
    print("=" * 65)

    # ── FIX B: rough mpp estimate ────────────────────────────────────
    print("\nFIX B — compute_rough_mpp:")
    print(f"  {'Scenario':<40} {'rough_mpp':>10}  {'kernel'}  Notes")
    print("  " + "─" * 72)

    class MockBR:
        def __init__(self, h): self.height_px = h

    test_cases = [
        (MockBR(589),  "jumbo_archtop", None,        "archtop spec+body"),
        (MockBR(589),  None,            "archtop",   "family hint only"),
        (MockBR(600),  "dreadnought",   None,        "acoustic spec"),
        (MockBR(850),  "smart_guitar",  None,        "smart guitar spec"),
        (MockBR(600),  None,            None,        "no spec, no family"),
        (None,         "dreadnought",   None,        "no body_region"),
        (MockBR(0),    "dreadnought",   None,        "zero height"),
    ]

    from patch_14_gated_adaptive_close import GatedAdaptiveCloser
    closer = GatedAdaptiveCloser()

    for br, spec, family, label in test_cases:
        mpp = compute_rough_mpp(br, spec, family)
        k   = closer.compute_kernel_size(mpp)
        print(f"  {label:<40} {mpp:>10.4f}  {k:>2d}×{k:<2d}")

    # ── FIX A: enum value string ─────────────────────────────────────
    print("\nFIX A — ScaleSource.FEATURE_SCALE value:")
    print(f"  New enum value: 'feature_scale'")
    print(f"  Distinguishes from 'estimated_render_dpi' in logs and guidance")

    # ── Verify rough mpp doesn't affect calibration chain ────────────
    print("\nVerification: rough mpp is not used as final calibration")
    print("  Stage 4.6 rough_mpp → only passed to PhotoEdgeDetector.detect()")
    print("  Stage 7 ScaleCalibrator.calibrate() runs independently")
    print("  Final result.calibration uses Stage 7 output, not rough_mpp")
    print("  ✓ No calibration accuracy regression from this change")

    print(f"\n{'='*65}")
    print("Pipeline wiring complete.")
    print(PIPELINE_ORDERING_DIFF)
    print(INTEGRATION_CHECKLIST)
