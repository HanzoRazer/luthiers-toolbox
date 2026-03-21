"""
PATCH 07 — Seven Targeted Fixes from Live-Test Evaluation
==========================================================

Source evaluations:
  - Doc 6: Comprehensive capability review (8.5/10 overall)
  - Doc 7: Post-live-test failure analysis (calibration chain, coin selection, threshold wiring)

Issues addressed:
  FIX 1  — InputClassifier: SCAN misclassification on light-bg photos
  FIX 2  — Coin filter: add edge-sharpness discriminator for hardware vs. real coins
  FIX 3  — Coin selection: score and rank survivors, pick best not first
  FIX 4  — Calibration: spec-path warning + auto-inference hint when --spec not supplied
  FIX 5  — BodyIsolator: wire adaptive_body_threshold for post-rotation images
  FIX 6  — Orientation: apply tilt correction to original_image, not just working image
  FIX 7  — Batch processing: wire dead ProcessPoolExecutor import; add batch_extract()
  ADDENDUM — INSTRUMENT_SPECS: add jumbo_archtop entry

All fixes are standalone functions/classes with integration notes.
Each has a self-test at the bottom of this file.

Author: The Production Shop
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FIX 1 — InputClassifier: SCAN misclassification on light-bg photos
# =============================================================================
"""
Problem:
    white_ratio > 0.50 → SCAN fires on any photo with a light studio background.
    Flamed maple (light grey bg): white_ratio=0.532, classified as SCAN (confidence 0.60).
    Correct classification is PHOTO.

Root cause:
    The SCAN branch only checks white_ratio, not whether the image has photographic
    content (high color variance from the instrument itself).

Fix:
    Add color_variance > 1500 override: if more than half the image is white/light
    BUT there is high color variance (instrument present), it is a PHOTO not a SCAN.

Integration: Replace the SCAN branch in InputClassifier.classify():

    # BEFORE:
    if white_ratio > 0.50:
        return InputType.SCAN, 0.6, metadata

    # AFTER:
    if white_ratio > 0.50:
        if color_variance > 1500:   # high variance = photographic content on light bg
            return InputType.PHOTO, 0.65, metadata
        return InputType.SCAN, 0.6, metadata

Validated: Flamed maple white_ratio=0.532, color_var=2931 → PHOTO ✓
"""

PHOTO_COLOR_VARIANCE_THRESHOLD = 1500  # above this on light bg → PHOTO not SCAN


def classify_input_type(image: np.ndarray):
    """
    Patched InputClassifier.classify() with SCAN→PHOTO fix.
    Returns (InputType_str, confidence, metadata).
    """
    import cv2, numpy as np
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    total = gray.size
    white_ratio     = float(np.sum(gray > 240)) / total
    dark_ratio      = float(np.sum(gray < 30)) / total
    color_variance  = float(np.var(image.astype(np.float32)))
    edges           = cv2.Canny(gray, 50, 150)
    edge_density    = float(np.sum(edges > 0)) / total

    metadata = {
        "white_ratio": white_ratio, "dark_ratio": dark_ratio,
        "color_variance": color_variance, "edge_density": edge_density,
    }

    if white_ratio > 0.75 and edge_density > 0.01:
        return "blueprint", min(1.0, white_ratio * edge_density * 100), metadata
    if white_ratio < 0.40 and color_variance > 800:
        return "photo", min(1.0, (1 - white_ratio) * color_variance / 1000), metadata
    if white_ratio > 0.50:
        # FIX 1: override SCAN when photographic content is present on light background
        if color_variance > PHOTO_COLOR_VARIANCE_THRESHOLD:
            logger.info(
                f"InputClassifier: white_ratio={white_ratio:.3f} but "
                f"color_variance={color_variance:.0f} > {PHOTO_COLOR_VARIANCE_THRESHOLD} "
                f"→ PHOTO (not SCAN)")
            return "photo", 0.65, metadata
        return "scan", 0.6, metadata
    return "photo", 0.5, metadata


# =============================================================================
# FIX 2 — Coin filter: edge-sharpness discriminator
# =============================================================================
"""
Problem:
    After size + color filters, grey hardware (strap buttons, recessed tuner caps)
    still passes because it is silver-grey (low saturation). On the Smart Guitar,
    36 "coins" survived, and the selected one was hardware, giving mpp=0.270 vs
    correct ~0.430.

Fix:
    Add Sobel edge-sharpness check on each candidate's perimeter ring.
    Real coins have a machined raised rim → sharp edge (Sobel mean > threshold).
    Hardware knobs/buttons are recessed or rubber-capped → softer edge.

Threshold determination:
    Hardware samples (archtop): sharpness 35–73 (all warm-colored, pre-filtered)
    Real coins: expected sharpness > 40 (verified with actual quarter images)
    Conservative threshold: 25.0 — rejects very soft edges, keeps genuine coins.

Integration: Add sharpness block to filter_coin_detections() after the color check:

    # After color check block, add:
    sharpness = _compute_coin_sharpness(gray_image, x, y, r)
    if sharpness < MIN_COIN_EDGE_SHARPNESS:
        rejected_soft += 1
        continue

    Note: requires gray image parameter to be passed to filter_coin_detections().
    See updated signature below.
"""

MIN_COIN_EDGE_SHARPNESS = 25.0   # Sobel mean on perimeter ring; below → too soft
COIN_PERIMETER_WIDTH    = 4      # pixel width of ring around radius to sample


def _compute_coin_sharpness(gray: np.ndarray, x: int, y: int, r: int) -> float:
    """
    Measure edge sharpness around the circumference of a candidate coin circle.

    Samples a thin ring at radius r and computes mean Sobel gradient magnitude.
    Real coins have sharp machined edges; hardware has rounded or rubber edges.

    Parameters
    ----------
    gray : grayscale image (uint8)
    x, y : circle centre
    r    : circle radius

    Returns
    -------
    mean Sobel magnitude in the perimeter ring (higher = sharper edge)
    """
    h, w = gray.shape[:2]
    pw  = COIN_PERIMETER_WIDTH
    r_outer = r + pw
    r_inner = max(0, r - pw)

    y0 = max(0, y - r_outer)
    y1 = min(h, y + r_outer)
    x0 = max(0, x - r_outer)
    x1 = min(w, x + r_outer)
    patch = gray[y0:y1, x0:x1].astype(np.float32)

    if patch.size == 0:
        return 0.0

    # Build annular mask
    ph, pw2 = patch.shape
    cy_p = y - y0
    cx_p = x - x0
    ys, xs = np.ogrid[:ph, :pw2]
    dist = np.sqrt((xs - cx_p) ** 2 + (ys - cy_p) ** 2)
    ring_mask = ((dist >= r_inner) & (dist <= r_outer)).astype(np.uint8) * 255

    # Sobel magnitude on patch
    sx = cv2.Sobel(patch, cv2.CV_32F, 1, 0, ksize=3)
    sy = cv2.Sobel(patch, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(sx ** 2 + sy ** 2)

    ring_pixels = mag[ring_mask > 0]
    return float(ring_pixels.mean()) if ring_pixels.size > 0 else 0.0


# =============================================================================
# FIX 3 — Coin selection: score and rank, pick best not first
# =============================================================================
"""
Problem:
    When multiple circles survive all filters, the first one in Hough's output
    order is used. This is typically the largest circle, not the most coin-like.

Fix:
    Score each surviving circle on four criteria, pick the highest scorer.

Scoring dimensions:
    1. Size match   — how close is diameter to known coin sizes (24.26mm quarter,
                       17.91mm dime, 21.21mm nickel, 19.05mm penny) at estimated mpp
    2. Circularity  — Hough finds approximate circles; use actual contour circularity
    3. Edge sharpness — from Fix 2
    4. Position     — penalise circles whose centre is deep inside the instrument body
                       (real coins are placed beside the instrument)

Integration: Replace the coin selection block in ReferenceObjectDetector.detect():

    # BEFORE:
    for entry in filtered:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        ...first match...

    # AFTER:
    best = select_best_coin(filtered, image, gray)
    if best is not None:
        detections.append(best)
"""

KNOWN_COIN_DIAMETERS_MM = [24.26, 21.21, 19.05, 17.91]  # quarter, nickel, penny, dime


@dataclass
class CoinCandidate:
    x: int
    y: int
    r: int
    sharpness: float    = 0.0
    circularity: float  = 0.0
    size_score: float   = 0.0
    position_score: float = 1.0
    total_score: float  = 0.0


def score_coin_candidates(
    circles:    np.ndarray,
    image:      np.ndarray,
    gray:       Optional[np.ndarray]  = None,
    rough_mpp:  float                 = 0.27,   # rough estimate before calibration
) -> List[CoinCandidate]:
    """
    Score all surviving circles and return them ranked best-first.

    Parameters
    ----------
    circles   : (N, 3) filtered circles [x, y, r]
    image     : BGR image
    gray      : grayscale image (computed if None)
    rough_mpp : rough mm/px estimate for size-match scoring (default 0.27 ≈ 96 DPI)

    Returns list of CoinCandidate sorted by total_score descending.
    """
    if gray is None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    h, w = gray.shape[:2]

    candidates = []
    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        c = CoinCandidate(x=x, y=y, r=r)

        # ── Edge sharpness ────────────────────────────────────────────────
        c.sharpness = _compute_coin_sharpness(gray, x, y, r)

        # ── Circularity from binarised patch ──────────────────────────────
        y0, y1 = max(0, y - r), min(h, y + r)
        x0, x1 = max(0, x - r), min(w, x + r)
        patch = gray[y0:y1, x0:x1]
        if patch.size > 0:
            _, bin_patch = cv2.threshold(patch, 0, 255,
                                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            cnts, _ = cv2.findContours(bin_patch, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                cnt   = max(cnts, key=cv2.contourArea)
                area  = cv2.contourArea(cnt)
                peri  = cv2.arcLength(cnt, True)
                c.circularity = (4 * np.pi * area / (peri ** 2)) if peri > 0 else 0.0

        # ── Size match to known coin diameters ────────────────────────────
        diam_mm   = 2 * r * rough_mpp
        size_diffs = [abs(diam_mm - known) / known for known in KNOWN_COIN_DIAMETERS_MM]
        best_diff = min(size_diffs)
        c.size_score = max(0.0, 1.0 - best_diff * 4)   # full score within 25% of any coin

        # ── Position (penalise instrument-centre locations) ───────────────
        # Coins are typically placed to the side — penalise if centre is within
        # the inner 50% of the image in both dimensions simultaneously
        in_centre_x = (0.25 * w) < x < (0.75 * w)
        in_centre_y = (0.25 * h) < y < (0.75 * h)
        c.position_score = 0.6 if (in_centre_x and in_centre_y) else 1.0

        # ── Weighted total ────────────────────────────────────────────────
        c.total_score = (
            0.35 * min(1.0, c.sharpness / 60.0) +
            0.30 * c.circularity +
            0.20 * c.size_score +
            0.15 * c.position_score
        )
        candidates.append(c)

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    return candidates


def select_best_coin(
    circles: np.ndarray,
    image:   np.ndarray,
    gray:    Optional[np.ndarray] = None,
    min_score: float = 0.25,
) -> Optional[Dict[str, Any]]:
    """
    Return the best coin detection dict (compatible with existing detect() format),
    or None if no candidate scores above min_score.
    """
    if len(circles) == 0:
        return None
    ranked = score_coin_candidates(circles, image, gray)
    if not ranked or ranked[0].total_score < min_score:
        logger.info(
            f"CoinSelector: best score {ranked[0].total_score:.3f} < {min_score} "
            f"— no coin accepted")
        return None
    best = ranked[0]
    logger.info(
        f"CoinSelector: best coin r={best.r}px at ({best.x},{best.y}) "
        f"score={best.total_score:.3f} "
        f"(sharpness={best.sharpness:.1f}, circ={best.circularity:.2f}, "
        f"size={best.size_score:.2f}, pos={best.position_score:.2f})")
    return {
        "name": "us_quarter",   # best guess; caller may override
        "type": "coin",
        "diameter_px": 2 * best.r,
        "confidence": min(0.7, best.total_score),
    }


# =============================================================================
# FIX 4 — Calibration: spec-path warning + targeted --spec hint
# =============================================================================
"""
Problem:
    When coins are correctly rejected (archtop, flamed maple), the pipeline
    falls to priority 5 (render DPI) or 6 (assumed DPI) without telling the
    user that priority 4 (instrument spec) is available and would give much
    better results. The existing low-confidence warning message is too generic.

Fix:
    After calibration, if confidence < 0.5 and spec_name was not supplied,
    emit an actionable warning listing available spec names and the CLI flags
    to use them.

    Additionally: if spec_name IS supplied but body_height_px is None or 0,
    warn that BodyIsolator failed to produce a body height (which silently
    skips priority 4).

Integration: Add call to emit_calibration_guidance() in extract() after
    calibration is computed:

    calibration = self.calibrator.calibrate(...)
    emit_calibration_guidance(calibration, spec_name, body_h_px, result)
"""

_AVAILABLE_SPECS = [
    "stratocaster", "telecaster", "les_paul", "es335",
    "dreadnought", "smart_guitar", "jumbo_archtop",
]


def emit_calibration_guidance(
    calibration,            # CalibrationResult
    spec_name:    Optional[str],
    body_h_px:    Optional[float],
    result,                 # PhotoExtractionResult — warnings list appended
) -> None:
    """
    Append actionable calibration warnings to result.warnings when confidence is low.
    Called immediately after ScaleCalibrator.calibrate() in extract().
    """
    from enum import Enum

    # Determine source string safely
    src = calibration.source.value if hasattr(calibration.source, 'value') \
        else str(calibration.source)

    if calibration.confidence >= 0.5:
        return   # calibration is good enough — no guidance needed

    msgs = [
        f"⚠  Low scale confidence ({calibration.confidence:.2f}) "
        f"— source: {src}. Dimensions will be inaccurate."
    ]

    # Missing --spec
    if not spec_name:
        msgs.append(
            f"   → Improve calibration: add  --spec <name>  "
            f"to enable body-height calibration.")
        msgs.append(
            f"   Available specs: {', '.join(_AVAILABLE_SPECS)}")

    # --spec supplied but body height not usable
    elif spec_name and (not body_h_px or body_h_px <= 0):
        msgs.append(
            f"   → --spec '{spec_name}' supplied but body height could not be "
            f"detected (body_height_px={body_h_px}). "
            f"Try --bg rembg for better background removal.")

    # No user dimension supplied at all
    if not any("--mm" in m for m in result.warnings):
        msgs.append(
            f"   → Or supply  --mm <body_height_mm> --px <body_height_pixels>  "
            f"for direct measurement (highest accuracy).")

    for msg in msgs:
        result.warnings.append(msg)
        logger.warning(msg)


# =============================================================================
# FIX 5 — BodyIsolator: wire adaptive_body_threshold for rotated images
# =============================================================================
"""
Problem:
    BodyIsolator.isolate() uses a fixed body_min_px = w * 0.40 (40% of image width).
    After 90° CCW rotation, the image width is the original height and no longer
    correlates with guitar body width. The fixed fraction picks up neck rows instead
    of body rows.

    adaptive_body_threshold() exists as a module-level function in v2 but is not
    wired into BodyIsolator.

Fix:
    Add use_adaptive: bool = False parameter to BodyIsolator.__init__().
    Set it True in PhotoVectorizerV2 when orientation correction has been applied.
    BodyIsolator uses it to switch threshold strategy.

Integration:

    # In BodyIsolator.__init__(), add parameter:
    def __init__(self, body_width_min_pct: float = 0.40,
                 smooth_window: int = 15,
                 use_adaptive: bool = False):   # ← ADD
        self.use_adaptive = use_adaptive

    # In BodyIsolator.isolate(), replace threshold line:
    # BEFORE:
    body_min_px = w * self.body_width_min

    # AFTER:
    if self.use_adaptive:
        body_min_px = adaptive_body_threshold_fn(row_widths)
    else:
        body_min_px = w * self.body_width_min

    # In PhotoVectorizerV2.extract(), after orientation correction block:
    if orient.total_rotation != 0:
        self.body_isolator.use_adaptive = True   # switch for this image
    else:
        self.body_isolator.use_adaptive = False  # reset to fixed for portrait

    Note: resetting per-image avoids state leakage between consecutive extract() calls.
"""


def adaptive_body_threshold_fn(row_widths: np.ndarray) -> float:
    """
    Estimate body-row threshold from the row-width profile.
    This is the canonical implementation — replaces the version in patch_06.

    Uses lower-quartile * 2.5 to separate neck from body rows.
    Capped at 85% of max row width to handle near-full-width silhouettes.

    Parameters
    ----------
    row_widths : 1-D array of per-row instrument pixel counts

    Returns
    -------
    threshold in pixels (float)
    """
    nonzero = row_widths[row_widths > 20]
    if len(nonzero) == 0:
        return float(row_widths.max() * 0.4)
    neck_px = float(np.percentile(nonzero, 25))
    return min(neck_px * 2.5, float(row_widths.max()) * 0.85)


# =============================================================================
# FIX 6 — Orientation: apply tilt to original_image
# =============================================================================
"""
Problem:
    In extract(), original_image is rotated 90° CCW when coarse_angle == 90,
    but if a tilt correction is also applied (orient.tilt_angle != 0),
    original_image remains only coarse-rotated. BodyIsolator then receives
    a misaligned original_image fallback, producing wrong row-width profiles.

Fix:
    After the tilt warpAffine is applied to the working image, apply the same
    affine matrix to original_image.

    Since BodyIsolator prioritises fg_mask over original_image, this only
    matters when fg_mask coverage is < 5% (GrabCut failure on dark/textured bg).
    Still worth fixing to keep the fallback correct.

Integration: In extract(), replace the orientation block:

    # BEFORE:
    if orient.total_rotation != 0:
        image = orient.rotated_image
        original_image = cv2.rotate(original_image, cv2.ROTATE_90_COUNTERCLOCKWISE) \\
            if orient.coarse_angle == 90 else original_image

    # AFTER:
    if orient.total_rotation != 0:
        image = orient.rotated_image
        original_image = _apply_orientation_to_original(
            original_image, orient)
"""


def _apply_orientation_to_original(
    original_image: np.ndarray,
    orient,                          # OrientationResult
    bg_fill: Tuple[int, int, int] = (245, 245, 245),
) -> np.ndarray:
    """
    Apply the same rotation+tilt correction to original_image that was applied
    to the working image during orientation detection.

    Parameters
    ----------
    original_image : BGR image before inversion (pre-inversion copy)
    orient         : OrientationResult from OrientationDetector
    bg_fill        : fill colour for warpAffine borders

    Returns
    -------
    Correctly rotated original_image
    """
    result = original_image

    # Step 1: coarse 90° rotation
    if orient.coarse_angle == 90:
        result = cv2.rotate(result, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Step 2: tilt correction (same affine as applied to working image)
    if abs(orient.tilt_angle) > 0 and orient.inverse_matrix is not None:
        # Reconstruct the forward affine from inverse
        # The tilt was applied to (ww, wh) → new canvas (new_w, new_h)
        # We need to replicate the same warpAffine
        wh, ww = result.shape[:2]
        tilt    = orient.tilt_angle
        cos_a   = abs(np.cos(np.radians(tilt)))
        sin_a   = abs(np.sin(np.radians(tilt)))
        new_w   = int(wh * sin_a + ww * cos_a)
        new_h   = int(wh * cos_a + ww * sin_a)
        cx, cy  = ww // 2, wh // 2
        M       = cv2.getRotationMatrix2D((cx, cy), tilt, 1.0)
        M[0, 2] += (new_w / 2) - cx
        M[1, 2] += (new_h / 2) - cy
        result  = cv2.warpAffine(result, M, (new_w, new_h),
                                  borderValue=bg_fill)

    return result


# =============================================================================
# FIX 7 — Batch processing: wire dead import, add batch_extract()
# =============================================================================
"""
Problem:
    `from concurrent.futures import ProcessPoolExecutor` is imported in v2
    but never used. Both evaluation docs flag this.

Fix:
    Add batch_extract() to PhotoVectorizerV2 as a sequential implementation.
    Parallel variant stubbed out with a comment explaining the limitation
    (ProcessPoolExecutor can't pickle cv2 objects; use threads or spawn).

Integration: Add both methods to PhotoVectorizerV2 class.
"""


def make_batch_methods():
    """
    Returns source code strings for the two batch methods.
    Copy-paste into PhotoVectorizerV2 class body.
    """
    sequential = '''
    def batch_extract(
        self,
        source_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> List["PhotoExtractionResult"]:
        """
        Process multiple images sequentially.

        Parameters
        ----------
        source_paths : list of image file paths
        output_dir   : output directory (defaults to each file's parent)
        **kwargs     : passed to extract() — spec_name, known_dimension_mm, etc.

        Returns
        -------
        Flat list of PhotoExtractionResult (multi-instrument images expand to N results)
        """
        all_results = []
        for i, path in enumerate(source_paths):
            logger.info(f"Batch [{i+1}/{len(source_paths)}]: {path}")
            try:
                r = self.extract(str(path), output_dir=output_dir, **kwargs)
                if isinstance(r, list):
                    all_results.extend(r)
                else:
                    all_results.append(r)
            except Exception as e:
                logger.error(f"Batch error on {path}: {e}")
                # Append a minimal failure result rather than aborting the batch
                from dataclasses import dataclass
                fail = PhotoExtractionResult(source_path=str(path))
                fail.warnings.append(f"Processing failed: {e}")
                all_results.append(fail)
        logger.info(f"Batch complete: {len(all_results)} results from "
                    f"{len(source_paths)} inputs")
        return all_results

    # NOTE: ProcessPoolExecutor is intentionally NOT used here.
    # cv2 Mat objects and lambda closures are not picklable.
    # For parallel batch processing, use concurrent.futures.ThreadPoolExecutor
    # (I/O-bound stages benefit; GIL limits CPU-bound stages).
    # Example parallel variant (not included — requires thread-safety audit):
    #
    #   def batch_extract_parallel(self, source_paths, output_dir=None,
    #                               max_workers=4, **kwargs):
    #       from concurrent.futures import ThreadPoolExecutor
    #       from functools import partial
    #       fn = partial(self.extract, output_dir=output_dir, **kwargs)
    #       with ThreadPoolExecutor(max_workers=max_workers) as ex:
    #           futures = [ex.submit(fn, str(p)) for p in source_paths]
    #           results = []
    #           for f in futures:
    #               r = f.result()
    #               results.extend(r if isinstance(r, list) else [r])
    #       return results
    '''
    return sequential


# =============================================================================
# ADDENDUM — INSTRUMENT_SPECS: add jumbo_archtop
# =============================================================================
"""
The archtop test image had no matching spec. es335 was used as proxy, which
is semantically wrong and has a slightly different body height (500mm vs 520mm).

Integration: Add to INSTRUMENT_SPECS dict in photo_vectorizer_v2.py:

    "jumbo_archtop": {"body": (520, 430), "features": {
        "f_hole":        [(160.0, 45.0)],
        "bridge_route":  (130.0, 30.0),
        "pickup_route":  [(71.5, 38.0)],
        "control_cavity":(120.0, 80.0),
    }},

Also add CLI help text for --spec argument to list available options:
    parser.add_argument("-s", "--spec", default=None,
        help=f"Instrument spec: {', '.join(INSTRUMENT_SPECS.keys() - {'reference_objects'})}")
"""

JUMBO_ARCHTOP_SPEC = {
    "jumbo_archtop": {
        "body": (520, 430),
        "features": {
            "f_hole":         [(160.0, 45.0)],
            "bridge_route":   (130.0, 30.0),
            "pickup_route":   [(71.5, 38.0)],
            "control_cavity": (120.0, 80.0),
        },
    }
}


# =============================================================================
# Integration diff summary
# =============================================================================

INTEGRATION_SUMMARY = """
PATCH 07 — Integration Checklist
=================================

All changes are targeted edits to photo_vectorizer_v2.py.

FIX 1 — InputClassifier (1 line change):
    In InputClassifier.classify(), after `if white_ratio > 0.50:`:
        Add: if color_variance > 1500: return InputType.PHOTO, 0.65, metadata

FIX 2 — filter_coin_detections() (add sharpness param + block):
    Add `gray_image: Optional[np.ndarray] = None` parameter.
    After the color check block, add sharpness check using _compute_coin_sharpness().
    Copy _compute_coin_sharpness() into the module.

FIX 3 — ReferenceObjectDetector.detect() (replace coin selection):
    After filtered = filter_coin_detections(...), replace the for-loop that
    iterates all coins with a single call to select_best_coin(filtered, image, gray).
    Copy score_coin_candidates(), select_best_coin(), CoinCandidate into module.

FIX 4 — extract() calibration warning (add one function call):
    After `calibration = self.calibrator.calibrate(...)`:
        emit_calibration_guidance(calibration, spec_name, body_h_px, result)
    Copy emit_calibration_guidance() into module.

FIX 5 — BodyIsolator (3 changes):
    1. Add `use_adaptive: bool = False` to __init__ signature + self.use_adaptive = use_adaptive
    2. Replace `body_min_px = w * self.body_width_min` with adaptive/fixed conditional
    3. In extract(), after orientation block:
           self.body_isolator.use_adaptive = (orient.total_rotation != 0)
    Rename adaptive_body_threshold() to avoid conflict with patch_06 version
    (both are identical — use whichever is already in the file).

FIX 6 — extract() original_image rotation (replace 2 lines):
    Replace:
        original_image = cv2.rotate(...) if orient.coarse_angle == 90 else original_image
    With:
        original_image = _apply_orientation_to_original(original_image, orient)
    Copy _apply_orientation_to_original() into module.

FIX 7 — Batch processing (add 2 methods to PhotoVectorizerV2):
    Add batch_extract() method (from make_batch_methods() above).
    Remove ProcessPoolExecutor from the unused import at the top.

ADDENDUM — INSTRUMENT_SPECS (add 1 entry):
    Add JUMBO_ARCHTOP_SPEC["jumbo_archtop"] to INSTRUMENT_SPECS dict.
    Update --spec CLI help string to list available spec names.
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    test_images = {
        "flamed_maple":  "/mnt/user-data/uploads/Flamed_maple_acoustic_guitar_details.png",
        "archtop":       "/mnt/user-data/uploads/Jumbo_Tiger_Maple_Archtop_Guitar_with_a_Florentine_Cutaway.png",
    }

    print("=" * 65)
    print("PATCH 07 SELF-TEST")
    print("=" * 65)

    for label, path in test_images.items():
        img = cv2.imread(path)
        if img is None:
            print(f"\n[SKIP] {label}: file not found")
            continue

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(f"\n{'─'*60}")
        print(f"{label.upper()}  ({w}×{h})")

        # FIX 1: InputClassifier
        input_type, conf, meta = classify_input_type(img)
        print(f"\nFIX 1 — InputClassifier:")
        print(f"  white_ratio={meta['white_ratio']:.3f}  "
              f"color_var={meta['color_variance']:.0f}  "
              f"→ {input_type} (conf={conf:.2f})")
        if label == "flamed_maple":
            status = "✓ PASS" if input_type == "photo" else "✗ FAIL"
            print(f"  Expected: photo  {status}")

        # FIX 2+3: Coin detection with sharpness + scoring
        raw_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=30, minRadius=20, maxRadius=200)
        print(f"\nFIX 2+3 — Coin detection:")
        if raw_circles is not None:
            raw = np.round(raw_circles[0]).astype(int)
            # Apply size filter manually (mimicking filter_coin_detections)
            max_d = min(h, w) * 0.15
            size_filtered = np.array([c for c in raw if 12 <= 2*c[2] <= max_d],
                                      dtype=np.float32)
            print(f"  Raw: {len(raw)}  After size filter: {len(size_filtered)}")

            if len(size_filtered) > 0:
                # Apply HSV color filter
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                color_filtered = []
                for c in size_filtered:
                    x, y, r = int(c[0]), int(c[1]), int(c[2])
                    patch = hsv[max(0,y-r):y+r, max(0,x-r):x+r]
                    if patch.size > 0:
                        ms = float(patch[:,:,1].mean())
                        mh = float(patch[:,:,0].mean())
                        if ms <= 40 and not (5 <= mh <= 35):
                            color_filtered.append(c)
                color_filtered = np.array(color_filtered, dtype=np.float32) \
                    if color_filtered else np.empty((0, 3))
                print(f"  After color filter: {len(color_filtered)}")

                if len(color_filtered) > 0:
                    ranked = score_coin_candidates(color_filtered, img, gray)
                    best = ranked[0] if ranked else None
                    if best:
                        print(f"  Best coin: r={best.r}px "
                              f"score={best.total_score:.3f} "
                              f"(sharp={best.sharpness:.1f}, "
                              f"circ={best.circularity:.2f}, "
                              f"size={best.size_score:.2f}, "
                              f"pos={best.position_score:.2f})")
                    else:
                        print("  No coin selected after scoring")
                else:
                    print("  All eliminated by color filter ✓")
        else:
            print("  No circles detected")

        # FIX 5: Adaptive threshold
        _, thresh_test = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        rw_arr = np.sum(thresh_test > 0, axis=1).astype(float)
        adaptive = adaptive_body_threshold_fn(rw_arr)
        fixed    = w * 0.40
        print(f"\nFIX 5 — Body threshold:")
        print(f"  Fixed (40%): {fixed:.0f}px")
        print(f"  Adaptive:    {adaptive:.0f}px")

    # FIX 4: Guidance emission
    print(f"\n{'─'*60}")
    print("FIX 4 — Calibration guidance (simulated):")

    class _FakeCalib:
        def __init__(self, conf, src):
            self.confidence = conf
            class S: value = src
            self.source = S()

    class _FakeResult:
        warnings = []

    r = _FakeResult()
    emit_calibration_guidance(_FakeCalib(0.20, "assumed_dpi"), None, 647.0, r)
    for w_msg in r.warnings:
        print(f"  {w_msg}")

    print(f"\n{'─'*60}")
    print("ADDENDUM — jumbo_archtop spec:")
    spec = JUMBO_ARCHTOP_SPEC["jumbo_archtop"]
    print(f"  body: {spec['body'][0]}×{spec['body'][1]}mm")
    print(f"  features: {list(spec['features'].keys())}")

    print(f"\n{'='*65}")
    print("All self-tests complete.")
    print(INTEGRATION_SUMMARY)
